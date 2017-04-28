# coding: utf-8
# 独立执行的django脚本, 需要添加这六行
import sys
import os
import django

sys.path.append((sys.path[0] + '/')[:sys.path[0].find('work')])
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from utils import manage_script
from django.db.models import Sum
from lib.utils import get_now
from order_action import create_package
from package_action import lock_packageitem, mapping_item_wanted, charge_package_can_pick
from order.models import Order, OrderItem
from shipping.models import Package, PackageItem


# todo 写到order的models.py中
def order_delivery_complete(order):
    status = False
    # 判断订单中产品的数量, 和package中已发货的产品数量是否一致
    order_item_qtys = OrderItem.objects.filter(order_id=order.id)\
                                       .filter(deleted=False)\
                                       .filter(order__status=4)\
                                       .aggregate(Sum('qty'))['qty__sum'] or 0

    delivered_qtys = PackageItem.objects.filter(package__order_id=order.id)\
                                        .filter(package__status=5)\
                                        .filter(deleted=False)\
                                        .aggregate(Sum('qty'))['qty__sum'] or 0

    if order_item_qtys == delivered_qtys:
        status = True
    return status


def orders_delivery():
    # 校验所有开始发货的订单
    orders = Order.objects.filter(status=4)
    for order in orders:
        res = order_delivery_complete(order)
        if res:
            order.status = 5  # 开始发货 => 发货完成
            order.save()
            print order.id, 'delivery'


def update_package_status_to1():
    # 将未处理的package状态改为开始处理
    packages = Package.objects.filter(status=0)
    for package in packages:
        package.status = 1
        package.save()
    print len(packages), 'to 1'


def do_package():
    # 创建package
    print 'START create package', get_now()
    create_package()
    print 'END create package', get_now()

    # 更新package的状态
    print 'START update_package_status_to1', get_now()
    update_package_status_to1()
    print 'END update_package_status_to1', get_now()

    # 创建itemlocked & itemwanted
    print 'START itemlocked', get_now()
    lock_packageitem()
    print 'END itemlocked', get_now()

    # 链接itemwanted & itemlocked
    print 'START mapping_item_wanted', get_now()
    mapping_item_wanted()
    print 'END mapping_item_wanted', get_now()

    # charge_package_can_pick
    print 'START charge_package_can_pick', get_now()
    charge_package_can_pick()
    print 'END charge_package_can_pick', get_now()

    # 更新order为发货完成
    print 'START orders_delivery', get_now()
    orders_delivery()
    print 'END orders_delivery', get_now()

manage_script(do_package)
