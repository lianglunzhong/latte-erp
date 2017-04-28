# -*- coding: utf-8 -*-
import time

from lib.utils import get_now, pp, ee, eparse
from order.models import Order, OrderItem, Channel, Alias
from shipping.models import Package
from zhuadan.shopify.shopify import Shopify
from zhuadan.utils import get_accounts


def get_tracking_company(shipping_label):
    shippings = {
        'GUB': 'USPS',
        'CUB': 'USPS',
        'SUB': 'USPS',
        'EUB': 'USPS',
        'DHL': 'DHL',
        'SDHL': 'DHL',
        'MDHL': 'DHL',
        'UPS': 'UPS',
        'FEDEX': 'FEDEX',
    }
    return shippings.get(shipping_label, 'Other')

def get_package_data(package):
    data = {}
    data['order_id'] = package.order.channel_ordernum
    data['tracking_number'] = package.tracking_no
    data['tracking_url'] = package.shipping.link
    data['tracking_company'] = get_tracking_company(package.shipping.label)
    item_ids = list(PackageItem.objects.filter(package_id=package.id).values_list('item_id', flat=True))
    data['line_items_ids'] = OrderItem.objects.filter(id=package.order_id)\
                                              .filter(item_id__in=item_ids)\
                                              .values('channel_oi_id', flat=True)
    return data                                        

def post_shopify_no():
    print "**START**", get_now()

    channel_accounts = get_accounts('shopify')
    for account in channel_accounts:
        print "\n *Account: %s Start" % account.name
        # 选出合适的package
        packages = Package.objects.filter(order__channel_id=account.id)\
                                  .filter(shipping_id__isnull=False)\
                                  .filter(possback_status=0)\
                                  .exclude(status__in=[0, 4])\
                                  .exclude(tracking_no='')
        for package in packages:                                  
            data = get_package_data(package)
            shopify = Shopify(account.name, account.api_key, account.password)
            try:
                r = shopify.upload_tracking(**data).json()
            except Exception, e:
                print 'Failure', package.order.ordernum, get_now(), account.name, e

            error_info = r.get('errors', {}).get('order', '')
            if r.get('fulfillment', {}).get('status', '') == 'success':
                print 'Success', package.order.ordernum, get_now(), account.name
            elif 'is already fulfilled' in error_info:
                print 'Already', package.order.ordernum, get_now(), account.name
            elif error_info:
                print 'Failure', package.order.ordernum, get_now(), account.name, error_info
            else:
                print 'Failure', package.order.ordernum, get_now(), account.name, 'need IT'

        time.sleep(5)
    print "**END**", get_now()








              

