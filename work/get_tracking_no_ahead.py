# coding: utf-8
# 独立执行的django脚本, 需要添加这六行
import sys
import os
import django

sys.path.append((sys.path[0] + '/')[:sys.path[0].find('work')])
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from utils import manage_script
from lib.utils import get_now
from lib.models import Shipping
from order_action import create_package
from shipping.models import Package

from logistics.logistics import verify_can_shipping, logistics_tracking_no, ShippingList


# 提前分配物流方式
def ahead_assign_shipping():
    # 给速卖通的package提前跑运单号
    packages = Package.objects.filter(shipping__isnull=True)\
                              .filter(order__channel__type=2)\
                              .exclude(status=4)
    print packages
    for package in packages:
        carrier = package.get_carrier()
        if carrier:
            shipping = Shipping.objects.filter(label=carrier).first()
            if not shipping:
                print "Failure", package.id, get_now(), carrier, "not exist"
                continue
            package.shipping = shipping
            package.option_log += u'\n IT 在%s 通过 提前跑运单号 分配了物流方式%s' % (get_now(), shipping.label)
            package.save()
            print "Success", package.id, get_now(), shipping
        else:
            print "Failure", package.id, get_now(), "not assign carrier"


def ahead_shipping_order():
    # 给速卖通的package提前获取运单号
    packages = Package.objects.filter(shipping__isnull=False)\
                              .filter(order__channel__type=2)\
                              .filter(tracking_no='')\
                              .exclude(status=4)\
                              .filter(shipping__label__in=ShippingList.have_api_shipping)
    for package in packages:
        # todo 测试的时候不走sfru
        # if package.shipping.label == 'SFRU':
        #     print 'SFRU continue'
        #     continue
        result = logistics_tracking_no(package)
        if result['success']:
            # todo 记录谁在什么时候分配的运单号
            package.tracking_no = result['tracking_no']
            package.option_log += u'\n IT 在%s 通过 提前跑运单号 获取了运单号%s' % (get_now(), result['tracking_no'])
            package.save()
            print "Success", package.id, package.shipping.label, get_now(), package.tracking_no
        else:
            print "Failure", package.id, package.shipping.label, get_now(), result['msg']


def get_tracking_no_ahead():
    """真正执行的脚本"""
    print "***START assign shipping***", get_now()
    ahead_assign_shipping()
    print "***END assign shipping***", get_now()

    print "***START shipping order***", get_now()
    ahead_shipping_order()
    print "***END shipping order***", get_now()

if __name__ == '__main__':
    get_tracking_no_ahead()
