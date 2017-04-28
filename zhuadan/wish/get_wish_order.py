# coding: utf-8
import time, datetime

from django.db import connection

from lib.utils import get_now, pp, ee, eparse
from lib.iorder import import_order
from order.models import Order
from zhuadan.wish.wish import Wish
from zhuadan.utils import get_accounts

# todo
# 和ws的旧数据会发生重复抓单 wish还要单独做, 其他的可以坐在import_order方法中

# 将api获取的订单数据, 进行合单并整理数据格式
def data_to_order_dicts(order_list, account):
    order_dicts = {}

    for order_info in order_list:
        order = order_info['Order']
        ordernum = order['transaction_id']
        import_note = ''

        try:
            sku = order['sku']
            qty = int(order['quantity'])
            price = float(order['price'])
            order_item = {
                'sku': sku,
                'qty': qty,
                'price': price,
                'channel_oi_id': order['order_id'],
            }
        except Exception, e:
            import_note += u'| orderitem 有误 %s \n' % ee(e)

        if ordernum not in order_dicts:
            order_dict = {}
            order_dict['ordernum'] = ordernum
            order_dict['channel'] = account

            order_dict['order_items'] = [order_item]


            # 金额的计算, 使用扣除平台费之前的金额
            try:
                order_dict['currency'] = "USD"
                order_dict['rate'] = 1.0
                order_dict['amount_shipping'] = float(order['shipping']) * qty
                order_dict['amount'] = qty * price + order_dict['amount_shipping']
            except Exception, e:
                import_note += u'| 订单金额有误 %s \n' % ee(e)

            order_dict['shipping_type'] = 0
            order_dict['create_time'] = eparse(order['order_time'] + '+00:00')
            order_dict['latest_ship_date'] = get_now() + datetime.timedelta(hours=int(order['hours_to_fulfill']))

            # 地址信息
            try:
                address_info = order['ShippingDetail']

                order_dict['shipping_firstname'] = address_info['name']
                order_dict['shipping_address'] = address_info.get('street_address1', '') + u" " + \
                                                 address_info.get('street_address2', '')
                order_dict['shipping_city'] = address_info['city']
                order_dict['shipping_state'] = address_info.get('state', '')
                order_dict['shipping_country_code'] = address_info['country']
                order_dict['shipping_zipcode'] = address_info.get('zipcode', '')
                order_dict['shipping_phone'] = address_info['phone_number']
            except Exception, e:
                import_note += u'| 订单地址信息有误 %s \n' % ee(e)

            order_dict['import_note'] = import_note

            # 建立order_dicts的大字典
            order_dicts[ordernum] = order_dict
        else:
            # 如果这个订单已经存在, 那么取出这个订单, 编辑orderitem及金额信息
            order_dict = order_dicts[ordernum]

            import_note += u'wish的合并订单'

            order_dict['order_items'].append(order_item)
            order_dict['amount_shipping'] += float(order['shipping']) * qty
            order_dict['amount'] += qty * price + order_dict['amount_shipping']
            order_dict['import_note'] += import_note

    return order_dicts


#获取wish order
def get_wish_order():
    print "**START**", get_now()

    channel_accounts = get_accounts('wish')
    for account in channel_accounts:
        print "\n *Account: %s Start" % account.name

        try:
            wish = Wish(client_id=account.client_id,
                        client_secret=account.client_secret,
                        refresh_token=account.refresh_token
                        )
        except Exception, e:
            print "Failure, account: ", account.name, get_now(), e
            continue
        
        #取最近2天
        next_page = "First"
        since = (get_now() - datetime.timedelta(days=2)).isoformat()[:-6]

        while next_page:
            try:
                if next_page == "First":
                    datas = wish.list_order(since, limit=5)
                else:
                    datas = wish.list_order_by_next_page(next_page)

                next_page = datas.get('paging', {}).get('next', '')
            except Exception, e:
                print ee(e), get_now()
                break

            order_list = datas.get('data', [])
            #如果最后一页只有一个订单,数据类型会变成字典,需转换成列表
            if type(order_list) == dict:
                order_list = [order_list]

            # pp(order_list)
            order_dicts = data_to_order_dicts(order_list, account)

            for ordernum, order_dict in order_dicts.iteritems():
                r = import_order(order_dict)

                #每导入一个订单, 打印出订单信息
                print "Success" if r['success'] else 'Failure',\
                      ordernum, get_now(), account.name, r['msg'].strip()

        connection.close()
        time.sleep(2)
    print "**END**", get_now()
 