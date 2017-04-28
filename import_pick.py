# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os
from django.db.models import Sum

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.contrib.auth.models import User
import depot as _depot
import shipping as _shipping

# 单单1，单多2，多多3
# package status 未处理0（有暂用库存有采购单），开始处理1（全部暂用库存），配货中2（生成pick），打包中3（生成出库记录，打印面单），已发货4（），妥投（从物流查询网站可以查到跟踪信息的时间）

packege_lists = _shipping.models.Package.objects.filter(status=0).order_by('-created')[:10]
for list in packege_lists:
    package_items = _shipping.models.PackageItem.objects.filter(package=list.id, deleted=False)
    # print package_items
    # package_items_count = package_items.count()
    package_items_sum = package_items.aggregate(Sum('qty'))
    itemlocaked_sum = 0
    for item in package_items:
        item_qty = _shipping.models.ItemLocked.objects.filter(package_item=item.id, deleted=False).aggregate(Sum('qty'))#一个packageitem可能占用不同仓库的库存
        itemlocaked_sum = itemlocaked_sum + item_qty['qty__sum']

    print(package_items_sum['qty__sum'], itemlocaked_sum)
    if(package_items_sum['qty__sum'] == itemlocaked_sum):
        list.status = 1
        list.pick_type = list.get_pick_type()
        list.code = 1
        list.save()


# 配货中2（生成pick）
# print _depot.models.Pick.PICK_TYPES
import json
for pick_type in _depot.models.Pick.PICK_TYPES:
    print pick_type[0]
    packages = _shipping.models.Package.objects.filter(status=1, code=1, pick_type=pick_type[0]).values_list('id', flat=True)#order_by('id').values_list('id', flat=True)
    if packages:
        print packages
        packages_str = ','.join( [str(x) for x in packages])
        print packages_str
        depot_item_sql = "SELECT itemlocaked.id,itemlocaked.`depot_item_id` , SUM( itemlocaked.qty ) as sum_qty " \
                        " FROM  `shipping_itemlocked` AS itemlocaked " \
                        " LEFT JOIN shipping_packageitem AS packageitem ON itemlocaked.`package_item_id` = packageitem.id" \
                        " WHERE itemlocaked.deleted =0" \
                        " AND packageitem.deleted =0" \
                        " AND packageitem.package_id" \
                        " IN ( %s )" \
                        " GROUP BY itemlocaked.`depot_item_id`" % ( packages_str )

        depot_items = _shipping.models.ItemLocked.objects.raw(depot_item_sql)
        depot_pick = _depot.models.Pick.objects.create(pick_type=pick_type[0])
        print depot_pick.id
        for item in depot_items:
            print item.depot_item_id,item.sum_qty
            pick_item = _depot.models.PickItem.objects.create(pick_id=depot_pick.id, qty=item.sum_qty, depot_item_id=item.depot_item_id)

        packages.update(pick_id=depot_pick.id, status=2)












