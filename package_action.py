# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.db import models
from mptt.models import MPTTModel
import datetime
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings

from django.db.models import Avg, Sum

import product as _product
import depot as _depot
import order as _order
import shipping as _shipping
import lib as _lib
from shipping.models import Package

def package_get_items(package):
    depots = package.order.channel.depots.order_by('channeldepot__order').all()

    default_depot = package.order.channel.default_depot

    for packageitem in _shipping.models.PackageItem.objects.filter(package=package).filter(deleted=False):

        qty_locked = _shipping.models.ItemLocked.objects.filter(package_item=packageitem, deleted=False).aggregate(Sum('qty'))['qty__sum']
        if not qty_locked:
            qty_locked = 0

        qty_wanted = _shipping.models.ItemWanted.objects.filter(package_item=packageitem, deleted=False).aggregate(Sum('qty'))['qty__sum']

        if not qty_wanted:
            qty_wanted = 0

        #当前订单物品需要的库存量
        qty_target = packageitem.qty - qty_locked - qty_wanted 

        if qty_target < 0:
            for qty_locked in _shipping.models.ItemLocked.objects.filter(package_item=packageitem, deleted=False):
                qty_locked.deleted = True
                qty_locked.save()
            for qty_wanted in _shipping.models.ItemWanted.objects.filter(package_item=packageitem, deleted=False):
                qty_wanted.deleted = True
                qty_wanted.save()

            qty_target = packageitem.qty

        # 到各个仓库按照仓库顺序锁定库存
        if qty_target > 0:
            for depot in depots:
                try:
                    depot_item = _depot.models.DepotItem.objects.get(item=packageitem.item, depot=depot)
                except _depot.models.DepotItem.DoesNotExist:
                    depot_item = _depot.models.DepotItem()
                    depot_item.item = packageitem.item
                    depot_item.depot = depot
                    depot_item.qty = 0
                    depot_item.qty_locked = 0
                    depot_item.save()

                #有无可用库存
                _qty = depot_item.qty_unlocked - qty_target

                if _qty >= 0 :
                    _shipping.models.ItemLocked.objects.create(package_item=packageitem, depot_item=depot_item, qty=qty_target)
                    qty_target = 0

                elif _qty < 0:
                    if depot_item.qty_unlocked > 0:
                        _shipping.models.ItemLocked.objects.create(package_item=packageitem, depot_item=depot_item, qty=depot_item.qty_unlocked)
                        qty_target = 0 - _qty

        # 锁定库存后，还不满足，生成itemwanted. 到 渠道的 默认仓库 
        if qty_target > 0:
            _shipping.models.ItemWanted.objects.create(package_item=packageitem, depot=default_depot, item=packageitem.item, create_time=package.order.create_time, qty=qty_target)

def mapping_item_wanted():
    itemwanteds = _shipping.models.ItemWanted.objects.filter(deleted=False).order_by('create_time')

    for itemwanted in itemwanteds:
        # check inventory 
        qty_unlocked = 0
        try:
            depot_item = _depot.models.DepotItem.objects.get(item=itemwanted.item, depot=itemwanted.depot)
            qty_unlocked = depot_item.qty_unlocked
        except _depot.models.DepotItem.DoesNotExist:
            pass

        if qty_unlocked > 0:
            _qty = itemwanted.qty - qty_unlocked

            if _qty > 0:
                _shipping.models.ItemLocked.objects.create(package_item=itemwanted.package_item, depot_item=depot_item, qty=qty_unlocked)
                itemwanted.qty = _qty
                itemwanted.save()

            elif _qty <= 0:
                _shipping.models.ItemLocked.objects.create(package_item=itemwanted.package_item, depot_item=depot_item, qty=itemwanted.qty)
                itemwanted.deleted = True
                itemwanted.save()
                continue


def lock_packageitem():
    packages = Package.objects.filter(status=1)
    for package in packages:
        package_get_items(package)

# package status 1, check all item locked 
# change package status :2
def charge_package_can_pick():
    for package in Package.objects.filter(status=1):
        if package.can_pick():
            package.status = 2
            package.pick_type = package.get_pick_type()
            package.position_score = package.get_position_score()
            package.save()

