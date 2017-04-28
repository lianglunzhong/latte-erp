# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.contrib.auth.models import User
from order.models import Order
from shipping.models import Package

from lib.action import *

def order():
    # 验证订单数据
    orders = Order.objects.filter(deleted=False).filter(status__in=[0,2]).filter(is_fba=False)
    for order in orders:
        order_verify(order)

    # 订单打包
    orders = Order.objects.filter(deleted=False).filter(status=3).filter(is_fba=False)
    for order in orders:
        order_do_package(order)
        order.status = 4
        order.save()

    # 验证订单发货完成
    orders = Order.objects.filter(deleted=False).filter(status=4).filter(is_fba=False)
    for order in orders:
        # 所有包裹发货完成
        package_count = Package.objects.filter(deleted=False).filter(status__in=[0,1,2,3]).count()
        if not package_count:
            order.status = 5
            order.save()

# 解决import该文件时，方法被执行
if __name__=='__main__':
    import time
    t1 = time.time()
    order()
    print time.time()-t1
