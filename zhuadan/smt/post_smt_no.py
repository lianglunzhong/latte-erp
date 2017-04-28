# -*- coding: utf-8 -*-
import time

from lib.utils import *
from order.models import Order, OrderItem, Channel, Alias
from zhuadan.smt.aliexpress import Aliexpress
from zhuadan.utils import get_accounts

def get_sendType(package):
    # 判断是否全部发货: 已经回传的, 加上当前包裹回传的数量, 是否小于orderitem总和
    sendType = 'all'
    # 总共需要回传的数量
    all_num = OrderItem.objects.filter(order_id=package.order_id).filter(deleted=False).aggregate(Sum('qty')).get("qty__sum") or 0
    # todo 需要确认package的回传状态字段放在哪里 
    # 订单中已经回传的包裹产品总数
    already_send_num = PackageItem.objects.filter(package__order_id=package.order_id)\
                                          .filter(package__possback_status=1)\
                                          .aggregate(Sum('qty'))\
                                          .get("qty__sum") or 0
    # 这次回传的产品总数
    this_send_num = PackageItem.objects.filter(package_id=package.id).aggregate(Sum('qty')).get("qty__sum") or 0

    if all_num > (already_send_num + this_send_num):
        sendType = 'part'
    return sendType

def get_service_name(label):
    service_name_dict = {
        "SF"        :   "SF",
        "SFRU"      :   "SF",
        "DHL"       :   "EMS_SH_ZX_US",
        "EMS"       :   "EMS",
        "EUB"       :   "EMS_ZX_ZX_US",
        "FedEx"     :   "FEDEX",
        "ARAMEX"    :   "ARAMEX",
        "NXB"       :   "CPAM",
        "FEDEXIE"   :   "FEDEX_IE",
        "DNXB"      :   "CPAM",
    }
    return service_name_dict[label]

def post_smt_no():
    print "*****Aliexpress START*****"
    channel_accounts = get_accounts('Smt')

    # todo 
    return 'Test Ending'
    failure_ordernum = []
    for account in channel_accounts:
        print "Account: %s Start" % account.name, get_now()
        #实例化, 因为部分帐号不一定能一次实例化成功
        for i in range(15):
            try:
                aliexpress = Aliexpress(
                                app_key=account.access_key, 
                                app_pwd=account.secret_key, 
                                refresh_token=account.auth_token,
                             )
                break
            except Exception, e:
                print ee(e)
                print "Failure %s , try numbers: %s" % (account.name, i+1)
        else:
            print "**Failure %s" % account.name
            continue

        # 选择合适的package回传
        # 当前channel, 有shipping, 回传状态为0, 有运单号, 不是取消和未处理
        packages = Package.objects.filter(order__channel_id=account.id)\
                                  .filter(shipping_id__isnull=False)\
                                  .filter(possback_status=0)\
                                  .filter(order__order_from=account.name)\
                                  .exclude(status__in=[0, 4])\
                                  .exclude(tracking_no='')

        for package in packages:
            ordernum = package.order.ordernum
            service_name = get_service_name(package.shipping.label)
            no = package.tracking_no
            # 如果是顺丰俄罗斯, 那么需要回传sf_numbers
            if package.shipping.label == 'SFRU':
                no = package.sf_numbers
            send_type = get_sendType(package)
            for i in range(5):
                try:
                    result = aliexpress.shipment(ordernum, service_name=service_name, no=no, send_type=send_type)
                    break
                except:
                    print 'Possback numbers:%s ordernum:%s' % (i, ordernum)
            else:
                print 'Possback failure. ordernum: %s' % ordernum
                failure_ordernum.append(ordernum)
                continue
            #更新成功
            if 'success' in result:
                if send_type == 'all':
                    #如果回传的状态是all, 那么就将这个order下的所有package的状态全部更新成回传完成
                    #因为之前发的包裹是待更新, 这次完成后, 之前的也全部完成
                    Package.objects.filter(order_id=package.order_id).update(possback_status=2)
                else:
                    Package.objects.filter(id=package.id).update(possback_status=1)

                print 'Success', package.id, send_type, get_now(), package.tracking_no
            #对于已经上传的数据进行更新, 运单号校验失败, 因为运单号已经被手工回传过了
            elif result.get('error_code', '') == '15-2001':
                Package.objects.filter(id=package.id).update(possback_status=2)                
                print 'Update', package.id, send_type, get_now(), package.tracking_no
            #更新失败
            else:
                print 'Failure', package.id, send_type, get_now(), package.tracking_no, result.get('error_code', 'Need Check')
    print "*****Aliexpress END*****"
    time.sleep(10)
