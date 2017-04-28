# -*- coding: utf-8 -*-
from __future__ import unicode_literals

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

def order_verify(order):
    # default 0
    order.status = 1
    # verify order country
    if not order.shipping_country:
        try:
            country = _lib.models.Country.objects.get(code=order.shipping_country_code)
            order.shipping_country = country
        except _lib.models.Country.DoesNotExist:
            # order 数据出错
            order.status = 7 
    else:
        pass

    # verify order items 
    for orderitem in order.orderitem_set.filter(deleted=False):
        if not orderitem.item:
            try:
                alias = _order.models.Alias.objects.get(sku=orderitem.sku)
                orderitem.item = alias.item 
                orderitem.save()
            except _order.models.Alias.DoesNotExist:
                alias = None
            
            if not alias:
                try:
                    item = _product.models.Item.objects.get(sku=orderitem.sku)
                    orderitem.item = item
                    orderitem.save()
                except _product.models.Item.DoesNotExist:
                    order.status = 7 
                    continue
    order.save()

def order_do_package(order):

   ## get order items
   #order_items = _order.models.OrderItem.objects.filter(order=order,deleted=False).values_list('item_id','qty')

   ## get package items
   #packageitems = _shipping.models.PackageItem.objects.get(package__order=order, deleted=False).values_list('item_id','qty')
   #
   #_update_items = {}

   #_delete_items = packageitems

   #for key in order_items.keys():
   #    _update_items[key] = order_items[key] - packageitems.get(key, 0)
   #    try:
   #        _delete_items.pop(key)
   #    except KeyError:
   #        pass


   #for item_id, qty in order_items:
   #    print item_id
   #    try:
   #        packageitem = _shipping.models.PackageItem.objects.get(item_id=item_id, package=package, deleted=False)
   #    except _shipping.models.PackageItem.DoesNotExist:
   #        packageitem = _shipping.models.PackageItem()
   #        packageitem.item_id = item_id
   #        packageitem.package = package

   #    packageitem.qty = qty
   #    packageitem.save()

    # get package 获得或者创建package头
    package, is_created = _shipping.models.Package.objects.get_or_create(order=order, deleted=False, status=0)
    
    if is_created:
        package.email = order.email
        package.shipping_firstname = order.shipping_firstname
        package.shipping_lastname = order.shipping_lastname
        package.shipping_address = order.shipping_address
        package.shipping_address1 = order.shipping_address1
        package.shipping_city = order.shipping_city
        package.shipping_state = order.shipping_state
        package.shipping_country = order.shipping_country
        package.shipping_zipcode = order.shipping_zipcode
        package.shipping_phone =  order.shipping_phone
        package.save()

    # get order items
    order_items = _order.models.OrderItem.objects.filter(order=order,deleted=False).values_list('item_id','qty')

    for item_id, qty in order_items:
        print item_id
        try:
            packageitem = _shipping.models.PackageItem.objects.get(item_id=item_id, package=package, deleted=False)
        except _shipping.models.PackageItem.DoesNotExist:
            packageitem = _shipping.models.PackageItem()
            packageitem.item_id = item_id
            packageitem.package = package

        packageitem.qty = qty
        packageitem.save()

def package_get_items(package):
    depots = package.order.channel.depots.order_by('channeldepot__order').all()

    default_depot = package.order.channel.default_depot

    for packageitem in _shipping.models.PackageItem.objects.filter(package=package).filter(deleted=False):

        print 'item start*******************'
        print packageitem.item.sku
        print packageitem.qty

        qty_locked = _shipping.models.ItemLocked.objects.filter(package_item=packageitem, deleted=False).aggregate(Sum('qty'))['qty__sum']
        if not qty_locked:
            qty_locked = 0
        print 'qty_locked %s' % qty_locked

        qty_wanted = _shipping.models.ItemWanted.objects.filter(package_item=packageitem, deleted=False).aggregate(Sum('qty'))['qty__sum']
        if not qty_wanted:
            qty_wanted = 0
        print 'qty_wanted %s' % qty_wanted

        #当前订单物品需要的库存量
        qty_target = packageitem.qty - qty_locked - qty_wanted 
        print 'qty_target %s' % qty_target

        if qty_target < 0:

            print 'qty clean!!!!!!!!'

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

def mapping_item_wanted(package):
    itemwanteds = _shipping.models.ItemWanted.objects.filter(deleted=False).ordery_by('created_time')
    for itemwanted in itemwanteds:
        # check inventory 
        qty_unlocked = 0
        try:
            depot_item = _depot.models.DepotItem.objects.get(item=itemwanted.item, depot=_shipping.models.ItemWanted.depot)
            qty_unlocked = depot_item.qty_unlocked
        except _depot.models.DepotItem.DoesNotExist:
            pass

        if qty_unlocked > 0:
            _qty = itemwanted.qty - qty_unlocked

            if _qty > 0:
                _shipping.models.ItemLocked.objects.create(packageitem=itemwanted.packageitem, depot_item=depot_item, qty=qty_unlocked)
                itemwanted.qty = _qty
                itemwanted.save()

            elif _qty <= 0:
                _shipping.models.ItemLocked.objects.create(packageitem=itemwanted.packageitem, depot_item=depot_item, qty=itemwanted.qty)
                itemwanted.deleted = True
                itemwanted.save()
                continue




