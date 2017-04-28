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
from order.models import Order,OrderItem
from shipping.models import Package

def order_verify(order):
    # default 0
    order.status = 3
    # verify order country
    if not order.shipping_country:
        try:
            country = _lib.models.Country.objects.get(code=order.shipping_country_code)
            order.shipping_country = country
        except _lib.models.Country.DoesNotExist:
            # order 数据出错
            order.status = 2 
    else:
        pass
    # verify order items 
    for orderitem in order.items.filter(deleted=False):
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
                    order.status = 2 
                    continue
    order.save()
    return order.status

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
    package, is_created = _shipping.models.Package.objects.get_or_create(order=order, status=0)
    # 设置package的物理仓库
    code = order.channel.depots.first().code
    if is_created:
        package.code = code
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


def create_package():
    # 验证订单 : 开始处理1，数据错误2
    for order in Order.objects.filter(status__in = [1,2]):        
        order_verify(order)

    # 验证是否是报缺，或者已经停止销售
    # 订单状态是:3 准备发货/验证通过
    # 4 开始发货 ／ 8 报缺，客服介入
    for order in Order.objects.filter(status = 3):
        order.status = 4
        for orderitem in order.items.filter(deleted=False):
          if orderitem.item.status in [0, 2]:
              order.status = 8
              break

        if order.status == 4:
          order_do_package(order)

        order.save()

def finish_order():
    #订单状态开始发货:4
    #确认订单是否 发货完毕,一天一次比较好
    for order in Order.objects.filter(status = 4):
        # 除了4 删除的包裹
        all_count = Package.objects.exclude(status = 4).filter(order=order).count()
        # 所有发货完成的包裹
        finish_count = Package.objects.filter(status__in = [5,6,7]).filter(order=order).count()

        # 有包裹，并且包裹总数和已经发货的数据一样
        if all_count and all_count == finish_count:
          order.status = 5
          order.save()






