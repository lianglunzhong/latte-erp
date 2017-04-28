# coding: utf-8
import time, datetime

from django.db import connection

from lib.utils import get_now, pp, ee, eparse
from lib.iorder import import_order
from order.models import Order
from zhuadan.shopify.shopify import Shopify
from zhuadan.utils import get_accounts

def get_shopify_order_dict(order_data, account):
    order_dict = {}

    # 必填信息
    order_dict['channel'] = account
    order_dict['ordernum'] = order_data['name']

    #出错的订单, 在import_note中注明原因
    import_note = ''

    # order_items: sku, qty, price, note, deleted
    order_items = []
    try:
        for item_data in order_data['line_items']:
            order_item = {}
            order_item['sku'] = str(item_data['sku'])
            order_item['qty'] = item_data['quantity']
            order_item['price'] = item_data['price']

            order_item['is_gift'] = item_data['gift_card']
            order_item['channel_oi_id'] = item_data['id']

            order_items.append(order_item)
    except Exception, e:
        import_note += u'| 订单产品信息出错, 请联系IT, %s \n' % ee(e)
    
    order_dict['order_items'] = order_items

    # 单身信息
    order_dict['channel_ordernum'] = order_data['id']
    order_dict['email'] = order_data['email']

    # 订单信息
    try:
        order_dict['currency'] = order_data['currency']
        order_dict['rate'] = float(order_data['total_price']) / float(order_data['total_price_usd'])
        order_dict['amount'] = float(order_data['total_price'])
        order_dict['amount_shipping'] = sum([float(i['price']) for i in order_data.get('shipping_lines', {})])
        order_dict['shipping_type'] = 0 # 默认小包
        order_dict['payment'] = order_data['gateway']
    except Exception, e:
        import_note += u'| 订单金额信息出错, 请联系IT, %s \n' % ee(e)

    order_dict['create_time'] = eparse(order_data['created_at'])

    # 地址信息
    try:
        address_info = order_data['shipping_address']

        order_dict['shipping_firstname'] = address_info['first_name']
        order_dict['shipping_lastname'] = address_info['last_name']
        order_dict['shipping_address'] = address_info['address1'] + ' ' + (address_info['address2'] or '')
        order_dict['shipping_city'] = address_info['city']
        order_dict['shipping_state'] = address_info['province_code']
        order_dict['shipping_country_code'] = address_info.get('country_code') or 'XX'
        order_dict['shipping_zipcode'] = address_info['zip']
        order_dict['shipping_phone'] = address_info['phone']
    except Exception, e:
        import_note += u'| 订单地址信息出错, 请联系IT, %s \n' % ee(e)

    order_dict['import_note'] = import_note
    return order_dict
    

def get_shopify_order():
    channel_accounts = get_accounts('shopify')

    print "**START**", get_now()

    for account in channel_accounts:
        print "\n *Account: %s Start" % account.name

        page = 1
        from_time = str(get_now().date() - datetime.timedelta(days=1))
        order_datas = 'First'
        shop = Shopify(account.name, account.api_key, account.password)

        while order_datas:
            order_datas = shop.get_order_list(page=page, from_time=from_time).get('orders', {})

            for data in order_datas:
                ordernum = data['name'] # ordernum保存name, channel_ordernum保存order的id
                try:
                    order = Order.objects.get(ordernum=ordernum)
                    continue
                except Exception, e:
                    pass

                order_dict = get_shopify_order_dict(data, account)
                r = import_order(order_dict)

                #每导入一个订单, 打印出订单信息
                print "Success" if r['success'] else 'Failure',\
                      ordernum, get_now(), account.name, r['msg'].strip()
            page += 1

        connection.close()
        time.sleep(5) # 账号间间隔5秒
        print "\n *Account: %s End" % account.name

    print "**END**", get_now()

get_shopify_order()