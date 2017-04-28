# coding: utf-8
import sys
import time
import datetime

from django.db import connection

from lib.utils import get_now, pp, ee, eparse
from lib.iorder import import_order
from order.models import Order, Alias
from zhuadan.smt.aliexpress import Aliexpress
from zhuadan.utils import get_accounts
from zhuadan.smt.black_ordernum_list import black_ordernums


def get_smt_order_dict(order_data, account, order_info_dict):
    # 速卖通sku的映射多个账号共享一套规则, 这里设置在zhujoe账号下
    sku_transform = dict(Alias.objects.filter(channel__name='NAE01').values_list('sku', 'item__sku'))

    order_dict = {}
    # 必填信息
    order_dict['channel'] = account
    order_dict['ordernum'] = str(order_data['id'])

    # 出错的订单, 在import_note中注明原因
    import_note = ''

    # order_items: sku, qty, price, note, deleted
    order_items = []
    try:
        for child_order in order_data['childOrderList']:
            sku_code = child_order['skuCode']
            sku_info_dict = {}
            try:
                sku_info = eval(child_order['productAttributes'])['sku']
                for info in sku_info:
                    sku_info_dict[info['pName']] = info['pValue']
                # print sku_info_dict
                size = sku_info_dict.get('Size', 'ONESIZE')
                if size.upper() == "ONE SIZE" or size.upper() == "FREE":
                    size = "ONESIZE"
            except Exception, e:
                size = "ONESIZE"

            sku = '-'.join([sku_code, size]).upper()

            # sku转化, 根据转化字典, 将sku进行转化
            sku = sku_transform.get(sku, '') or sku

            qty = int(child_order.get('productCount', 1))
            total_price = float(child_order['productPrice']['amount'])

            # 判断产品的类别是a lot的话, 数量改为5件
            try:
                product_unit = child_order['productUnit']
                if product_unit == 'Lot':
                    qty = qty * 5
            except Exception, e:
                pass
            price = round(total_price / qty, 2)

            order_item = {
                'sku': sku,
                'qty': qty,
                'price': price,
            }

            # 发往美国的产品, 订单状态改为未处理, 增加说明, 订单产品的状态改为删除, 一个订单可能多个产品从美国发货
            ships_from = sku_info_dict.get("Ships From", "China")
            if ships_from != "China":
                order_item['deleted'] = True
                order_item['note'] = u'从美国发货'
                import_note += u'|%s 从美国发货\n' % str(sku)

            order_items.append(order_item)
    except Exception, e:
        # 如果订单产品信息有异常, 则将订单的状态改为未处理
        import_note += u'| 订单产品信息出错, 请联系IT, %s \n' % ee(e)
        print '订单产品信息出错, 请联系IT, %s |' % ee(e)

    order_dict['order_items'] = order_items

    # 单身信息
    try:
        # todo 对象字段
        # order_dict['add_user'] = User.objects.get(username='lidongchao')
        # order_dict['order_manager'] = User.objects.get(username='lidongchao')

        # 2016-03-01 速卖通api不再提供卖家邮箱, 邮箱使用陈菲的邮箱
        order_dict['email'] = 'chen.fei@wxzeshang.com'  # order_data['buyerInfo']['email'].strip()
        order_dict['comment'] = order_info_dict.get(order_dict['ordernum'], '')  # 卖家留言
        if order_dict['comment']:
            import_note += u'| 卖家留言: %s \n' % order_dict['comment']

        order_dict['currency'] = order_data['orderAmount']['currencyCode']
        # order_dict['payment'] = "Credit Card" # to delete 不保存这个字段了
        order_dict['amount'] = order_data['orderAmount']['amount']
        order_dict['amount_shipping'] = order_data['logisticsAmount']['amount']

        # 如果shipping<10美金, 则使用小包(0)
        order_dict['shipping_type'] = 0 if order_dict['amount_shipping'] < 10 else 0

        # 地址信息
        address_info = order_data.get('receiptAddress', {})
        order_dict['shipping_firstname'] = address_info.get('contactPerson', "")
        # 没有lastname
        order_dict['shipping_address'] = address_info.get('detailAddress', "")
        order_dict['shipping_address1'] = address_info.get('address2', "")
        order_dict['shipping_city'] = address_info.get('city', "")
        order_dict['shipping_state'] = address_info.get('province', "")
        # shipping_country 比较特殊, smt使用的不是标准二字码, 有几个需要转换
        # UK=>GB, SRB=>RS
        country_code = address_info.get('country', "XX")
        if country_code == "UK":
            country_code = "GB"
        elif country_code == "SRB":
            country_code = "RS"
        order_dict['shipping_country_code'] = country_code

        order_dict['shipping_zipcode'] = address_info.get('zip', "")
        # 处理订单的电话, 电话|手机, 电话是phoneCountry-phoneArea-phoneNumber
        try:
            phone_list = []
            if address_info.get('phoneNumber', ''):
                phone_list.append(address_info.get('phoneCountry', ''))
                phone_list.append(address_info.get('phoneArea', ''))
                phone_list.append(address_info.get('phoneNumber', ''))
                phone_number = '-'.join([i for i in phone_list if i])
            else:
                phone_number = ''
            mobile_no = address_info.get('mobileNo', '')
            order_dict['shipping_phone'] = phone_number + "|" + mobile_no
        except Exception, e:
            order_dict['shipping_phone'] = '|'
            pass
        # 没有电话信息
        if order_dict['shipping_phone'] == '|':
            import_note += u'| 该订单没有电话信息 \n'

        # 订单的创建时间, 取付款成功时间
        # 原格式是gmtCreate: 20160512102509000-0700, 需要去除时区前的三个0, 否则无法解析
        try:
            gmtPaySuccess = order_data.get('gmtPaySuccess')
            useful = gmtPaySuccess[:14] + gmtPaySuccess[17:]
            create_time = eparse(useful)
        except Exception, e:
            create_time = get_now()
            import_note += u'| 该订单时间有误, 请联系IT \n'
        order_dict['create_time'] = create_time

        # 其他订单规则
        # 如果订单的金额大于100美金, 则该订单为大额订单, 增加文字说明
        if order_dict['amount'] > 100:
            import_note += u'| 该订单金额超过100美金的大单 \n'
        # 如果订单支付了运费, 增加文字说明
        if order_dict['amount_shipping'] > 0:
            import_note += u'| 该订单支付了运费 %s 美金 \n' % order_dict['amount_shipping']

    except Exception, e:
        import_note += u'| 单身信息出错, 请联系IT %s \n' % ee(e)

    order_dict['import_note'] = import_note
    return order_dict


def get_smt_order():
    print "**START**", get_now()

    # 获取所有速卖有效通账号
    channel_accounts = get_accounts('Smt')
    for account in channel_accounts:
        print "\n *Account: %s Start" % account.name
        # 如果帐号尝试失败, 则继续下一个帐号
        success_num = 0
        for i in range(10):
            try:
                aliexpress = Aliexpress(
                                app_key=account.app_key,
                                app_pwd=account.app_pwd,
                                refresh_token=account.refresh_token,
                             )
                data = aliexpress.list_order(page=1, page_size=1)
                totalItem = data.get('totalItem') or '0'
                break
            except Exception, e:
                print ee(e)
                print "Failure %s , try numbers: %s" % (account.name, i + 1)
        else:
            print "**Failure %s" % account.name
            continue

        print "Total: ", totalItem
        # 如果没有订单, 则换帐号
        if int(totalItem) == 0:
            print account.name, "has no order."
            time.sleep(2)
            continue

        # 因为目的只是获取订单号, 所以page_size设置的较大
        page_size = 30
        order_info = []

        # pages向上取整, 使用(A+B-1)/B, range最右再加一页
        pages = int((int(totalItem) + page_size - 1) / page_size) + 1
        for i in range(1, pages):
            for k in range(3):
                try:
                    data = aliexpress.list_order(page=i, page_size=page_size)
                    break
                except Exception, e:
                    print 'Get page timeout.Numbers:%s Page:%s ' % (k, i)
            # 订单的备注信息只在这里有, 在订单的详细信息中没有, 但是有的订单会没有memo字段, 因此使用字典的get方法
            order_info += [(str(j['orderId']), j.get('memo', '')) for j in data['orderList']]
            time.sleep(1)
        # test 测试只使用前10单
        # order_info = order_info[:10]

        order_info_dict = dict(order_info)
        ordernum_list = [str(i) for i in order_info_dict.keys()]
        print "All number:", len(ordernum_list)

        # 只获取不在数据库中的order详细信息
        exist_order = list(Order.objects.filter(ordernum__in=ordernum_list).values_list("ordernum", flat=True))
        exist_order = [str(i) for i in exist_order]
        print "All exist:", len(exist_order)

        ordernum_list = list(set(ordernum_list) - set(exist_order))
        print "Unexisted Ordernum:", len(ordernum_list)

        # test 各种测试订单号, zhujoe帐号, 订单状态为 WAIT_SELLER_EXAMINE_MONEY
        # 依次为大金额, 发往美国, address2, 国家为UK, sku变更, 单位是a lot, 自付运费, 电话
        # ordernum_list = [70878873675402, 70744445186679, 71252953524918, 71248641158261, 70691272179277, 70544219095836, 70494953677631, 70544219115836, 70464214605637]
        failure_ordernum = []
        for ordernum in ordernum_list:
            order_item_list = []
            try:
                Order.objects.get(ordernum=ordernum)
                continue
            except Exception, e:
                for k in range(5):
                    try:
                        order_data = aliexpress.get_order(order_id=ordernum)
                        break
                    except Exception, e:
                        print 'Get order timeout.Numbers:%s ordernum:%s ' % (k, ordernum)
                else:
                    failure_ordernum.append(ordernum)
                    print "Get order failure. ordernum:%s" % ordernum
                    continue
                if 'id' not in order_data:
                    failure_ordernum.append(ordernum)
                    continue

                # 使用黑名单, 旧的指定订单不导入新系统
                if order_data.get('id', '') in black_ordernums:
                    continue

                order_dict = get_smt_order_dict(order_data, account, order_info_dict)
                r = import_order(order_dict)

                print "Success" if r['success'] else 'Failure',\
                      ordernum, get_now(), account.name, r['msg'].strip()

        print "Failure order", failure_ordernum

        connection.close()

        # 一个帐号结束
        time.sleep(2)

    print '***END work get order %s' % get_now()
    sys.stdout.flush()
