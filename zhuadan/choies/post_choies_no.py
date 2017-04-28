# -*- coding: utf-8 -*-
import time

from lib.utils import *
from order.models import Order, OrderItem, Channel
from shipping.models import Package

def post_choies_no():
    print "***********START*********** %s" % get_now()
    # todo choies, 是否还有其他, 比如wholesale, persunmall
    shop_ids = (1, )
    # todo  条件的筛选
    packages = Package.objects.filter(possback_status__in=(0, 1))\
                              .exclude(status=4)\
                              .filter(order__shop_id__in=shop_ids)\
                              .exclude(shipping_id__isnull=True)\
                              .exclude(tracking_no='')\
                              .exclude(ship_time__isnull=True)
    #回传物流发货信息到对应网站
    posturls = {
        "choies"     : "http://www.choies.com/api/from_ws_update_shipment",
        "persunmall" : "http://www.persunmall.com/api/from_ws_update_shipment",
        "iwantwig"   : "http://www.iwantwig.com/api/from_ws_update_shipment",
        "wholesale"  : "http://www.choieswholesale.com/api/from_ws_update_shipment",
    }
    for package in packages:
        #wholesale只回传运单号以WH开头的订单
        if package.order.channel.name.lower() == 'wholesale' and not package['order__ordernum'].startswith('WH'): 
            continue

        tracking_no = package['tracking_no']
        shipping_method = package['shipping__label']
        cost = package['cost'] + package['cost1']
        tracking_link = ''

        if shipping_method:
            tracking_link = package['shipping__link']
        else:
            print u"Package ID:%s has no shipping:%s ;" % (package_id,shipping_method)
            continue

        #回传物流发货信息到对应网站
        shop = package['order__shop__name'].lower()
        if package['possback_status'] == 0:
            try:
                posturl = posturls[shop]
                shipment_status = 'shipped'
                order_id = package['order_id']
                
                #如果订单的产品总数量比这个package的发货数量和这个订单已经发货的产品数量还多, 那么就是部分发货
                all_num = OrderItem.objects.filter(order_id=order_id).filter(status=1).aggregate(Sum('qty')).get("qty__sum")
                already_send_num = PackageItem.objects.filter(package__order_id=order_id).filter(package__possback_status=2).aggregate(Sum('qty')).get("qty__sum")
                this_send_num = PackageItem.objects.filter(package_id=package_id).aggregate(Sum('qty')).get("qty__sum")
                if not all_num:
                    print 'Order:%s has no item.' % order_id
                    continue
                if not already_send_num : already_send_num = 0
                if not this_send_num    : this_send_num = 0
                if all_num > already_send_num + this_send_num:
                    shipment_status = 'partial_shipped'

                skus = ''
                qtys = ''
                packageitems = PackageItem.objects.filter(package_id=package_id).values("item__sku", "qty")
                for pitem in packageitems:
                    skus += pitem['item__sku'] + ','
                    qtys += str(pitem['qty']) + ','

                postdata = {
                    'updated': 1,
                    'ordernum': package['order__ordernum'],
                    'status': shipment_status,
                    'skus': skus,
                    'qtys': qtys,
                    'totals': cost,
                    'tracking_no': tracking_no,
                    'shipping_method': shipping_method,
                    'tracking_link': tracking_link,
                    'package_id': package_id,
                    'shipping_time': package['ship_time'],
                }

                try:
                    r = requests.post(posturl, data=postdata)
                    if r.status_code == 200:
                        if r.json() == 0:
                            print u"Package: %s  %s  %s, Failure-1-data_error" % (shop, package_id, get_now())
                            continue
                        Package.objects.filter(pk=package_id).update(possback_status=2)
                        if shipment_status == 'shipped':
                            print u"Package: %s  %s  %s, Success-1" % (shop, package_id, get_now())
                        else:
                            print u"Package: %s  %s  %s, Success-1 partial_shipped" % (shop, package_id, get_now())
                    else:
                        print u"Package: %s  %s  %s, Failure-1-connect" % (shop, package_id, get_now())
                except Exception, e:
                    print u"Package: %s  %s %s, Failure-1-to_test, %s" % (shop, package_id, get_now(), str(e))

            except Exception, e:
                print u"Package: %s  %s  %s, Failure-1-to_solve, %s" % (shop, package_id, get_now(), str(e))
        elif package['possback_status'] == 1:
            try:
                posturl = posturls[shop]
                postdata = {
                    'updated': 2,
                    'ordernum': package['order__ordernum'],
                    'tracking_no': tracking_no,
                    'shipping_method': shipping_method,
                    'tracking_link': tracking_link,
                    'package_id': package_id,
                    'shipping_time': package['ship_time'],
                }
                try:
                    r = requests.post(posturl, data=postdata)
                    if r.status_code == 200:
                        if r.json() == 0:
                            print u"Package: %s  %s  %s, Failure-2-data_error" % (shop, package_id, get_now())
                            continue
                        print u"package: %s  %s  %s, success-2" % (shop, package_id, get_now())
                        Package.objects.filter(pk=package_id).update(possback_status=2)
                    else:
                        print u"Package: %s  %s  %s, Failure-2-connect" % (shop, package_id, get_now())
                except Exception, e:
                    print u"Package: %s  %s  %s, Failure-2-to_test, %s" % (shop, package_id, get_now(), str(e))
            except Exception, e:
                print u"Package: %s  %s  %s, Failure-2-to_solve, %s" % (shop, package_id, get_now(), str(e))

    print "***********END*********** %s" % get_now()

