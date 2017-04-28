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
from django.db.models import Sum

from shipping.models import *

from lib.action import *

def package():
    # package 比对库存，产生需求
    # package 验证是否可以pick，状态是2的意思是包裹全部暂用库存，已确定pick类型；否则状态一直是1-开始处理
    # packages = Package.objects.filter(deleted=False).filter(status__in=[1,2])
    packages = Package.objects.filter(deleted=False).filter(status=1)
    for package in packages:
        #包裹物品生成库存占用或采购需求单
        package_get_items(package)
        packageitems = PackageItem.objects.filter(deleted=False).filter(package=package)
        i=0
        j=0
        for packageitem in packageitems:
            j += 1
            locked_qty = ItemLocked.objects.filter(deleted=False).filter(package_item=packageitem).annotate(Sum('qty'))
            print locked_qty.values()
            # print 'locked_qty.qty,packageitem.qty',locked_qty[0].qty,packageitem.qty
            if locked_qty and packageitem.qty == locked_qty[0].qty:
                i += 1
        if i>0 and i==j:
            package.status = 2#包裹全部占用库存的状态
            package.pick_type = package.get_pick_type()#获取包裹分拣类型
            package.save()
        #
        # package.status = 2
        # package.save()

    # package 验证是否可以pick，状态是2的意思是包裹全部暂用库存，已确定pick类型；否则状态一直是1-开始处理
    # packages = Package.objects.filter(deleted=False).filter(status=2)
    #
    # for package in packages:
    #     package.status = 3
    #
    #     packageitems = PackageItem.objects.filter(deleted=False).filter(package=package)
    #     for packageitem in packageitems:
    #         locked_qty = ItemLocked.objects.filter(deleted=False).filter(package_item=packageitem).annotate(Sum('qty'))
    #         if packageitem.qty != locked_qty:
    #             package.status = 2
    #             continue
    #     package.save()

# 解决import该文件时，方法被执行
if __name__ == '__main__':
    import time
    t1 = time.time()
    package()
    print time.time()-t1
