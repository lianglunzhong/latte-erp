# coding: utf-8
import time, datetime, gc

from django.db import connection

from lib.models import Country
from lib.utils import get_now, pp, ee, eparse
from lib.iorder import import_order
from order.models import Order, OrderItem, Channel

from zhuadan.amazon.amazon import Orders
from zhuadan.amazon.accounts import Accounts
from zhuadan.utils import get_accounts

def get_amazon_order_dict(order_info, account, amazon):
    ordernum = order_info.get('AmazonOrderId', '')
    order_dict = {}
    order_item_list = []
    import_note = ''

    order_dict['ordernum'] = ordernum
    order_dict['channel'] = account
    order_dict['email'] = order_info.get('BuyerEmail', '')
    
    # Order金额
    try:
        order_dict['currency'] = order_info['OrderTotal']['CurrencyCode']
        order_dict['amount'] = order_info['OrderTotal']['Amount']
    except:
        order_dict['currency'] = 'USD'
        order_dict['amount'] = 0
        import_note += u'| 订单没有金额或汇率有问题\n'

    #order_item
    order_items = []
    item_list = amazon.list_order_items(amazon_order_id=ordernum).parsed['OrderItems']['OrderItem']
    amount_product = 0
    amount_coupon = 0
    amount_shipping = 0
    if type(item_list) == dict:
        item_list = [item_list]

    #如果订单产品超过10件, 请手动检验数据完整性
    if len(item_list) > 10:
        import_note += u'| 订单产品超过10件, 请手动检验数据完整性\n'

    #amount = amount_product + amount_shipping - amount_coupon 
    for item_info in item_list:
        # 如果item_info的数量为0, 说明这个orderItem被取消了
        if not int(item_info['QuantityOrdered']):
            continue
        amount_product += float(item_info['ItemPrice']['Amount'])
        amount_coupon += (float(item_info['PromotionDiscount']['Amount']) + float(item_info['ShippingDiscount']['Amount'])) 
        amount_shipping += float(item_info['ShippingPrice']['Amount'])

        try:
            # sku的验证使用alias进行验证, 这里只保存即可
            sku = item_info['SellerSKU']
            qty = int(item_info['QuantityOrdered'])
            try:
                price = float(item_info['ItemPrice']['Amount']) / qty
            except Exception, e:
                import_note += u'|qty error:%s数量为0, %s\n' % (sku, e)
                continue

            order_item = {
                'sku': sku,
                'qty': qty,
                'price': price,
                'channel_oi_id': item_info['OrderItemId'],
            }
            order_items.append(order_item)
        except Exception, e:
            import_note += u'orderitem:%s数据不全,%s |' % (sku, e)
    order_dict['order_items'] = order_items

    # amount
    order_dict['amount_product'] = amount_product
    order_dict['amount_coupon'] = amount_coupon
    order_dict['amount_shipping']   = amount_shipping
    order_dict['payment'] = order_info.get('PaymentMethod', 'other')
    order_dict['payment_date'] = eparse(order_info.get('PurchaseDate', ''))
    order_dict['create_time'] = order_dict['payment_date']
    order_dict['latest_ship_date'] = eparse(order_info.get('LatestShipDate', ''))

    #shipping
    shipping_info = order_info['ShippingAddress']
    order_dict['shipping_firstname'] = shipping_info['Name']
    order_dict['shipping_address'] = shipping_info.get('AddressLine1','') + \
                                     shipping_info.get('AddressLine2','') + \
                                     shipping_info.get('AddressLine3','')
    order_dict['shipping_city'] = shipping_info.get('City', '')
    order_dict['shipping_state'] = shipping_info.get('StateOrRegion', '')
    order_dict['shipping_country_code'] = shipping_info.get('CountryCode', 'XX')
    order_dict['shipping_zipcode'] = shipping_info.get('PostalCode', '')
    order_dict['shipping_phone'] = shipping_info.get('Phone', '')

    return order_dict

def get_amazon_order():
    print '***START work get amazon order %s ***' % get_now()

    channel_accounts = get_accounts('amazon')

    for account in channel_accounts:
        print "\n *Account: %s Start %s" % (account.name, get_now())
        #去除这个用户所在大洲的开发人员账号信息
        developer = Accounts.developers[account.continent.title()]
        amazon = Orders(access_key=developer['access_key'], 
                        secret_key=developer['secret_key'], 
                        account_id=account.account_id,
                        auth_token=account.auth_token,
                        )
        #尝试, 当无法获取的时候, 进行
        for i in range(10):
            if amazon.get_service_status().parsed.get('Status') == 'GREEN':
                print "GREEN"
                break
            else:
                print "Failure number: %s" % i+1
                time.sleep(60)
        else:
            time.sleep(1)
            print "Account:%s Failure" % account.name
            continue

        # # test start
        # #商品数量为0, 两件产品, 单件有运费,对多件有优惠
        # ordernums = ['113-6935756-6939409','115-5224300-1466659', '107-8893319-1637852', '111-5685070-5646636']
        # order_info = amazon.get_order(ordernums).parsed
        # next_token = order_info.get('NextToken', '')
        # order_list = order_info.get('Orders').get('Order')
        # print 33333
        # break
        # # test end

        # 给next_token赋初值
        next_token = 'First'
        now_days = (datetime.datetime.now()- datetime.timedelta(days=1)).strftime('%Y-%m-%d') 
        while next_token:
            #每个帐号第一次获取order, 后面使用next_token进行订单信息的获取
            if next_token == 'First':
                order_info = amazon.list_orders(marketplaceids=account.marketplaceids.split('#'),
                                                lastupdatedafter=now_days, 
                                                max_results="50", 
                                                orderstatus=('Unshipped','PartiallyShipped'),
                                                fulfillment_channels=('MFN',)
                                                ).parsed
            else:
                order_info = amazon.list_orders_by_next_token(token=next_token).parsed            
            next_token = order_info.get('NextToken', '')

            try:
                order_list = order_info.get('Orders').get('Order')
            except Exception, e:
                print e
                break
            #获取订单的时候, 如果最后一页只剩下一个订单, 那么那个订单的数据结构会是dict而不是list, 转化一下
            if type(order_list) == dict:
                order_list = [order_list]

            for order_info in order_list:
                ordernum = order_info.get('AmazonOrderId', '')
                try:
                    order = Order.objects.get(ordernum=ordernum)
                    continue
                except Exception, e:
                    pass

                order_dict = get_amazon_order_dict(order_info, account, amazon)
                r = import_order(order_dict)

                #每导入一个订单, 打印出订单信息
                print "Success" if r['success'] else 'Failure',\
                      ordernum, get_now(), account.name, r['msg'].strip()

            connection.close()
            time.sleep(60)
        print "\n *Account: %s End %s" % (account.name, get_now())
        #一个帐号结束
        time.sleep(2)

    print '***END work get order %s' % get_now()

def get_amazon_fba_order():
    print '***START work get amazon fba order %s ***' % get_now()

    channel_accounts = get_accounts('amazon')

    for account in channel_accounts:
        print "\n *Account: %s Start %s" % (account.name, get_now())
        #去除这个用户所在大洲的开发人员账号信息
        developer = Accounts.developers[account.continent.title()]
        amazon = Orders(access_key=developer['access_key'], 
                        secret_key=developer['secret_key'], 
                        account_id=account.account_id,
                        auth_token=account.auth_token,
                        )
        #尝试, 当无法获取的时候, 进行
        for i in range(10):
            if amazon.get_service_status().parsed.get('Status') == 'GREEN':
                print "GREEN"
                break
            else:
                print "Failure number: %s" % i+1
                time.sleep(60)
        else:
            time.sleep(1)
            print "Account:%s Failure" % account.name
            continue

        # # test start
        # #商品数量为0, 两件产品, 单件有运费,对多件有优惠
        # ordernums = ['113-6935756-6939409','115-5224300-1466659', '107-8893319-1637852', '111-5685070-5646636']
        # order_info = amazon.get_order(ordernums).parsed
        # next_token = order_info.get('NextToken', '')
        # order_list = order_info.get('Orders').get('Order')
        # print 33333
        # break
        # # test end

        # 给next_token赋初值
        next_token = 'First'
        now_days = (datetime.datetime.now()- datetime.timedelta(days=2)).strftime('%Y-%m-%d') 
        while next_token:
            #每个帐号第一次获取order, 后面使用next_token进行订单信息的获取
            if next_token == 'First':
                order_info = amazon.list_orders(marketplaceids=account.marketplaceids.split('#'),
                                                lastupdatedafter=now_days, 
                                                max_results="50", 
                                                orderstatus=('Shipped'),
                                                fulfillment_channels=('AFN',)
                                                ).parsed
            else:
                order_info = amazon.list_orders_by_next_token(token=next_token).parsed            
            next_token = order_info.get('NextToken', '')

            try:
                order_list = order_info.get('Orders').get('Order')
            except Exception, e:
                print e
                break
            #获取订单的时候, 如果最后一页只剩下一个订单, 那么那个订单的数据结构会是dict而不是list, 转化一下
            if type(order_list) == dict:
                order_list = [order_list]

            for order_info in order_list:
                ordernum = order_info.get('AmazonOrderId', '')
                try:
                    order = Order.objects.get(ordernum=ordernum)
                    continue
                except Exception, e:
                    pass

                order_dict = get_amazon_order_dict(order_info, account, amazon)
                # is_fba 在这里进行标识
                order_dict['is_fba'] = True
                r = import_order(order_dict)

                #每导入一个订单, 打印出订单信息
                print "Success" if r['success'] else 'Failure',\
                      ordernum, get_now(), account.name, r['msg'].strip()

            connection.close()
            time.sleep(60)
        print "\n *Account: %s End %s" % (account.name, get_now())
        #一个帐号结束
        time.sleep(2)

    print '***END work get order %s' % get_now()

if __name__ == "__main__":
    get_amazon_order()