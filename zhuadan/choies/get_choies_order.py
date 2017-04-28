# coding: utf-8
import requests
import datetime, time
from django.utils import timezone

from order.models import Order, OrderItem, Channel
from lib.utils import pp, eparse,  get_now
from lib.iorder import import_order

def get_choies_order():
    print '*START work get order %s' % get_now()
    sys.stdout.flush()

    #从choies或者wholssale导入的订单, 有5小时的时差
    add_5hour = datetime.timedelta(hours=5)

    shops = ['choies.com', ]

    urls = {
        'choies.com': 'http://www.choies.com/api/order_date_list',
        # 'wholesale': 'http://www.choieswholesale.com/api/order_date_list',
        # 'persunmall': 'http://www.persunmall.com/api/order_date_list',
        # 'choies': 'http://local.clothes.com/api/order_date_list',
    }

    posturls = {
        'choies.com': 'http://www.choies.com/api/from_ws_update_order_erp',
        # 'wholesale': 'http://www.choieswholesale.com/api/from_ws_update_order_erp',
        # 'persunmall': 'http://www.persunmall.com/api/from_ws_update_order_erp',
        # 'choies': 'http://local.clothes.com/api/from_ws_update_order_erp',
    }
    
    for shop_name in shops:
                
        today = datetime.date.today()
        start_date = today - datetime.timedelta(days=30)
        start_date = today - datetime.timedelta(days=3) # 测试用
        while today >= start_date:
            # 根据日期获取订单信息
            start_date=start_date + datetime.timedelta(days=1)
            url = urls[shop_name] + "?date=%s" % start_date.isoformat()
            print url, shop_name
            shop = Channel.objects.get(name=shop_name)
            r = requests.get(url)
            if r.status_code == 200:
                pass
            else:
                print 'Url return %s' % str(r.status_code)
                continue

            try:
                orders_data = r.json()
            except Exception, e:
                print str(e)
                continue

            # 处理订单
            for order_data in orders_data:
                if order_data['payment_status'] != 'verify_pass':
                    continue
                
                order_dict = {}
                #print order_data
                try:
                    order = Order.objects.get(ordernum=order_data['ordernum'])
                except:
                    # 必填字段
                    order_dict['ordernum'] = order_data['ordernum']
                    order_dict['channel'] = shop

                    order_items = []
                    for item_data in order_data['orderitems']:
                        model = item_data['sku']
                        sku_items = [] 
                        size = ''
                        color = ''
        
                        for attribute in item_data['attributes'].strip().split(';'):
                            if not attribute:
                                continue
        
                            key = attribute.split(':')[0]
                            try:
                                value = attribute.split(':')[1]
                            except:
                                break
        
                            if key == 'Size':
                                size = value.replace(' ', "")
                                if size.startswith('EUR'):
                                    size = size.split('/')[1]
                            elif key == 'Color':
                                color = value.replace(' ', "")
                                try:
                                    other = attribute.split(':')[2]
                                    color = ""
                                except:
                                    pass
        
                            size = size.split('(')[0]
        
                            try:
                                color_other = color.split('[-]')[1]
                                color = ""
                            except:
                                pass
        
                        sku_items.append(model)
                        sku_items.append(size)
                        sku_items.append(color)
                        sku = '-'.join([i for i in sku_items if i])
                        sku = sku.upper()
                        if 'is_gift' in item_data and int(item_data['is_gift']) == 0:
                            is_gift = False
                        else:
                            is_gift = True

                        order_item = {
                            'sku': sku,
                            'qty': item_data['quantity'],
                            'note': item_data['attributes'],
                            'price': item_data['price'],
                            # 如果是礼品, 当成正常的商品用, 只是price为0
                        }

                        order_items.append(order_item)
                    order_dict['order_items'] = order_items

                    # 订单信息
                    order_dict['email'] = order_data['email']
                    order_dict['note'] = order_data['remark']
                    order_dict['currency'] = order_data['currency']
                    order_dict['amount'] = float(order_data['amount'] or 0)
                    order_dict['amount_shipping'] = float(order_data['amount_shipping']) # to add 运费
                    if 'order_insurance' in order_data and order_data['order_insurance']:
                        order_dict['amount_shipping'] += float(order_data['order_insurance'])

                    if order_data['rate'] == 0:
                        rate = 1
                    else:
                        rate = order_data['rate']
                    order_dict['rate'] = rate    # to delete order是否需要rate
                    if float(order_data['amount_shipping']) / rate < 10:
                        order_dict['shipping_type'] = 0
                    else:
                        order_dict['shipping_type'] = 1
                    if shop_name == "wholesale":
                        if 0 <= float(order_data['amount_shipping']) / rate < 1:
                            order_dict['shipping_type'] = 0
                        else:
                            order_dict['shipping_type'] = 1
                    order_dict['create_time'] = eparse(order_data['date_purchased'], offset="+00:00") + add_5hour
                    # naive = parse_datetime(order_data['date_purchased']) + add_14hour
                    # order_dict['create_time'] = pytz.timezone("Asia/Shanghai").localize(naive, is_dst=None)
                    
                    # 地址信息
                    order_dict['shipping_firstname'] = order_data['shipping_firstname']
                    order_dict['shipping_lastname'] = order_data['shipping_lastname']
                    order_dict['shipping_address'] = order_data['shipping_address']
                    order_dict['shipping_city'] = order_data['shipping_city']
                    order_dict['shipping_state'] = order_data['shipping_state']
                    order_dict['shipping_country_code'] = order_data['shipping_country']
                    order_dict['shipping_zipcode'] = order_data['shipping_zip']
                    order_dict['shipping_phone'] = order_data.get('shipping_phone', '')


                    # START 下面都是待定 是否需要一个other_msg的字段专门用来保存这些不是很重要且无规律, 但是可能需要看的信息

                    order_dict['comment1'] = order_data['cele_admin'] # to delete 红人单
                    if order_data['ip_address'] == '0.0.0.0':
                        order_dict['is_hand'] = True
                    else:
                        order_dict['is_hand'] = False

                    # todo payment_date是否需要, 和create是否二选一, 
                    # 可以使用导单备注进行保存需要保存的信息
                    order_dict['payment_date'] = eparse(order_data['payment_date'], offset="+00:00") + add_5hour
                    
                    order_dict['order_from'] = order_data['order_from'] # to delete 只有choies用, 记录after_sale和celebrate的
                    order_dict['payment'] = order_data['payment'] # to delete 付款方式, 不确定是否要保留
                    order_dict['amount_product'] = order_data['amount_products'] # to add 商品价格
                    order_dict['amount_coupon'] = order_data['amount_coupon'] # to add 优惠金额
                    order_dict['address_confirm'] = 1 # to delete 地址是否验证
                    # END 上面都是待定
                    
                    print order_dict['ordernum'], order_dict['shipping_country_code'], order_dict['amount'], [i['sku'] for i in order_dict['order_items']]

                    # todo 
                    # order_dict['add_user'] = User.objects.get(username='lidongchao')
                    # order_dict['order_manager'] = User.objects.get(username='lidongchao')
                    r = import_order(order_dict)
                    print r['msg']

                #update choies order erp_header_id = 2
                # posturl = posturls[shop_name]
                # postdata = {
                #     'order_id': order_data['id'],
                # }
                # try:
                #     pass  # 测试的时候不能回传
                #     # r = requests.post(posturl, data=postdata)
                # except Exception, e:
                #     print str(order_data['ordernum']) + ' update ' + str(shop_name) + ' order erp_header_id Failed!'
    
    print '*END work get order %s' % get_now()

get_choies_order()