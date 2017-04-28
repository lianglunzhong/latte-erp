# -*- coding: utf-8 -*-
import time

from lib.utils import *
from order.models import Order, OrderItem, Channel
from zhuadan.smt.aliexpress import Aliexpress
from zhuadan.utils import get_accounts

account_list = AmazonAccounts.account_list

def get_feed_xml(packages, account):
    # 一个包裹中每条信息有自己的MessageID, 从0自增
    i = 1
    # 初始化保存包裹信息的xml字符串
    message_xml = ''

    for package in packages:
        # 先拼出产品的xml
        item_xml = ''
        package_items = dict(PackageItem.objects.filter(package_id=package['id']).values_list('item__sku', 'qty'))
        order_items = dict(OrderItem.objects.filter(order_id=package['order_id']).values_list('sku', 'channel_oi_id'))
        for sku, qty in package_items.iteritems():
            channel_oi_id = order_items.get(sku)
            item_xml += '''<Item>
        <AmazonOrderItemCode>{}</AmazonOrderItemCode>
        <Quantity>{}</Quantity>
    </Item>'''.format(channel_oi_id, qty)

        # 发货时间需要比最迟发货时间早1天
        try:
            send_time = package['order__latest_ship_date'] - datetime.timedelta(days=1)
        except Exception, e:
            print package['id'], str(e)
            continue
        if timezone.now() < send_time:
            send_time = timezone.now()

        # 拼写出物流信息的主体
        main_xml = '''<Message>
        <MessageID>{}</MessageID>
        <OrderFulfillment>
            <AmazonOrderID>{}</AmazonOrderID>
            <FulfillmentDate>{}</FulfillmentDate>
            <FulfillmentData>
                <CarrierName>China Post</CarrierName>
                <ShippingMethod>e-packet</ShippingMethod>
                <ShipperTrackingNumber>{}</ShipperTrackingNumber>
            </FulfillmentData>
            {}
        </OrderFulfillment>
    </Message>
    '''.format(i, package['order__ordernum'], send_time.replace(microsecond=0).isoformat(), package['tracking_no'], item_xml)
        message_xml += main_xml
        i += 1
        
    # 构建完整的xml信息
    all_package_xml = '''<?xml version="1.0" encoding="UTF-8"?>
    <AmazonEnvelope xsi:noNamespaceSchemaLocation="amzn-envelope.xsd" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
        <Header>
            <DocumentVersion>1.01</DocumentVersion>
            <MerchantIdentifier>{}</MerchantIdentifier>
        </Header>
        <MessageType>OrderFulfillment</MessageType>
        {}
    </AmazonEnvelope>
    '''.format(account['account_id'], message_xml)
    return all_package_xml

def post_amazon_no():
    print '###Start Possback', timezone.now()
    for account in account_list:
        print "#Start", account['account'], timezone.now()

        developer = AmazonAccounts.developers[account['continent']]
        amazon = Feeds(
                    access_key=developer['access_key'], 
                    secret_key=developer['secret_key'], 
                    account_id=account['account_id'], 
                    auth_token=account['auth_token']
                 )

        # 根据账号, 选择1.)这个账号抓的单, 2.)这个shop, 3.)未回传的包裹, 4.)有运单号, 5.)包裹未取消, 6.)订单未暂停
        packages = Package.objects.filter(order__order_from=account['account']).filter(order__shop_id=account['shop_id'])\
                                  .filter(possback_status__in=[0, 1]).exclude(tracking_no='')\
                                  .exclude(status=4).exclude(order__active=6).filter(created__gte='2016-01-01')\
                                  .values('id', 'order_id', 'order__ordernum', 'tracking_no', 'order__latest_ship_date')

        # # test
        # packages = Package.objects.filter(id__in=[255732, 256123, 256177, 256266, 257178, 257655, 257913, 262613, 262762, 264804])\
        #                           .values('id', 'order_id', 'order__ordernum', 'tracking_no')

        # 使用分页, 每次回传最多1000个 ---- 以后包裹多了, 会进行分页, 这里设计好结构
        objs = Paginator(packages, 1000)

        for i in objs.page_range:
            this_page = objs.page(i)
            if not this_page:
                break

            feed_xml = get_feed_xml(this_page, account)
            res = amazon.submit_feed(feed=feed_xml,
                                     feed_type='_POST_ORDER_FULFILLMENT_DATA_',
                                     marketplaceids=account['marketplaceids']).parsed
            #更新package的回传状态为已回传
            package_ids = [j['id'] for j in this_page]
            Package.objects.filter(id__in=package_ids).update(possback_status=2)

            close_connection()
            print package_ids
            time.sleep(60 * 2)

        print "#End", account['account'], timezone.now()
        time.sleep(10)

    print '###End Possback', timezone.now()
            