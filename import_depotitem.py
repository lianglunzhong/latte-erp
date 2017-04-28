# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
import csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()


from product.models import *
from order.models import *
from depot.models import *
from django.contrib.auth.models import User

path = os.getcwd()
file2 = 'NJ-qty-2016-6-13-17-13.csv'

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)

index = True
i = 0
for row in reader:

    i = i+1
    if index:
        index = False
        continue

    for j in range(0,3):
        row[j] = row[j].decode('gbk').encode('utf-8')#不要相信业务提供的表格
        row[j] = row[j].strip()
        if j == 1:
            try:
               row[j]=int(row[j])
            except Exception,e:
                row[j] = 0

    try:
        alias = Alias.objects.get(sku=row[0])
        note = '从ky里的移库库存做期初账套'
        obj=None
        type=4
        user = User.objects.get(id=1)
        # item_in(self, qty, cost, note="", obj=None, type=0, operator=None):
        depotitem,flag = DepotItem.objects.get_or_create(depot_id=2,item=alias.item)
        try:
            depotitem.item_in(row[1],0,note,obj,type,user)
        except Exception,e:
            print row[0],u'入库失败',e

    except Alias.DoesNotExist:
        print u'无法匹配的产品：%s'% row[0]
        # depotInLog = DepotInLog()
        # depotInLog.depot_id = 1
        # depotInLog.qty = int(row[1])
        # depotInLog.type = 4
        # depotInLog.item_id = alias.item_id
        # depotInLog.operator_id = 1
        # depotInLog.save()
        # # print depotInLog.id
        # depotItem = DepotItem.objects.get(item_id=alias.item_id,depot_id=1)
        # depotItem.position = str(row[2])
        # depotItem.save()

        # try:
        #     depotItem = DepotItem.objects.get(item_id=alias.item_id,depot_id=1)
        # except DepotItem.DoesNotExist:
        #     DepotItem.objects.get_or_create(item_id=alias.item_id,depot_id=1,position=row[2],qty=0)

handle.close()