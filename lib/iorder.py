# -*- coding: utf-8 -*-
import copy
from django.core.exceptions import ValidationError

from lib.models import Country
from product.models import Item
from order.models import Order, OrderItem, Channel, Alias

ORDER_DICT = {
    # 必填字段
    'channel': None, # Channel obj
    'ordernum': '', # str
    # orderitem list, 
    'order_items': [
        {
            'sku': '', # str 
            'qty': 0, # 0
            'price': 0.0, # float
            'note': '', # str
            'deleted': False, # boolean
            'channel_oi_id': '', # str
        },
    ],

    # 导单备注 important
    'import_note': '', # str

    # 对象字段
    'add_user_id': None, # User obj
    'order_manager_id': None, # User obj

    # 订单信息
    'channel_ordernum': '', # str 渠道ordernum 或者id, 或者额外的ordernum别名
    'email': '', # str
    'comment': '', # str
    'note': '', # str
    'create_time': None, # utc datetime
    'latest_ship_date': None, # utc datetime
    'import_type': 1, # 默认为api导入, 0为手工导入
    'is_fba': False, # 是否为fba单, 默认为False
    
    # 金额信息
    'currency': '', # str
    'rate': 1.0, # float
    'amount': 0, # float
    'amount_shipping': 0, # float 运费
    'shipping_type': 0, # int
    'payment': '', # 支付方式

    # 地址信息
    'shipping_firstname': '', # str
    'shipping_lastname': '', # str
    'shipping_address': '', # str
    'shipping_address1': '', # str
    'shipping_city': '', # str
    'shipping_state': '', # str
    'shipping_country_code': '', # str
    'shipping_zipcode': '', # str
    'shipping_phone': '', # str

    'is_fba': False, #是否为FBA订单 boolean
}


def import_order(order_dict):
    '''
    创建一个模板dict, 包含order的所有字段
    orderitem的对象是一个list, 每个orderitem是一个字典
    外键关系传递对象
    返回值是一个字典, 包含状态, 和消息

    作用: 校验通用信息的完整性
    特殊: 如果api有特殊备注, 请检查好后写入import_note中传递过来
    '''
    # 初始化关键信息
    standard_dict = copy.deepcopy(ORDER_DICT)
    standard_dict.update(order_dict) # 防止key_error
    order_dict = standard_dict

    result = {
        'success': False,
        'msg'    : order_dict['import_note'],
    }

    if order_dict['ordernum'] and order_dict['channel']:
        ordernum = order_dict['ordernum']
    else:
        result['msg'] += u'ordernum和channel的信息不全'
        return result

    # 判断是否重复订单
    try:
        order = Order.objects.get(ordernum=ordernum)
        result['msg'] += u'ordernum: {0} 已存在'.format(ordernum)
        return result
    except Exception, e:
        pass

    # 判断渠道信息是否有误
    if not isinstance(order_dict['channel'], Channel):
        result['msg'] += u'ordernum: {0} 的渠道账号有误'.format(ordernum)
        return result

    # 创建订单信息
    order = Order.objects.create(ordernum=order_dict['ordernum'],
                                 channel=order_dict['channel']
                                )

    # 先处理单身信息
    order_items = order_dict.get('order_items', [])
    if not order_items:
        result['msg'] += u'| 订单中没有产品\n'

    for order_item in order_items:
        # 
        # 先将传来的sku先在choies的alias中进行搜索
        the_alias = Alias.objects.filter(sku=order_item['sku'], channel_id=1).first()

        # 再将传来的sku在渠道的别名中进行搜索
        if not the_alias:
            the_alias = Alias.objects.filter(sku=order_item['sku'], channel=order_dict['channel']).first()

        # 如果找到, 那么直接使用item, 否在在item中进行搜索
        if the_alias:
            item = the_alias.item
        else:
            item = Item.objects.filter(sku=order_item['sku']).first()

        if not item:
            result['msg'] += u'| sku为 {0} 的产品不存在\n'.format(order_item['sku'])
            if 'note' in order_item:
                order_item['note'] += u'该order_item对应的item不存在\n'
            else:
                order_item['note'] = u'该order_item对应的item不存在\n'

        try:
            OrderItem.objects.create(order=order,
                                     item=item,
                                     qty=order_item.get('qty', 0),
                                     sku=order_item.get('sku', 'Error'),
                                     note=order_item.get('note', ''),
                                     price=order_item.get('price', 0),
                                     deleted=order_item.get('deleted', False),
                                     channel_oi_id=order_item.get('channel_oi_id', '')
                                    )
        except Exception, e:
            result['msg'] += u'| OrderItem创建出错 %s \n' % e

    # 处理单头信息
    order.__dict__.update(order_dict)

    # 处理国家信息
    try:
        country = Country.objects.get(code=order.shipping_country_code)
    except Exception, e:
        country = None
        result['msg'] += u'| 国家CODE %s 不存在\n' % order.shipping_country_code
    order.shipping_country = country

    # 检测关键信息的完整性
    for key in ['email', 'amount', 'shipping_firstname', 'shipping_city', 'shipping_state', 'shipping_zipcode']:
        if not order_dict.get(key, ''):
            result['msg'] += u'|%s 信息缺失\n' % key

    # 校验订单的其他信息
    try:
        order.full_clean()
        order.status = 1 # 认为订单信息正确
        order.save()
    except ValidationError, e:
        errors = e.message_dict
        for field, info in errors.iteritems():
            result['msg'] += u'| {0} : {1}\n'.format(field, '; '.join(info))

    if result['msg']:
        # 将报错信息展示在前台, 并设置状态为未处理
        order = Order.objects.get(ordernum=ordernum)
        order.status = 0
        order.import_note = result['msg']

        order.save()
    else:
        result['success'] = True

    return result
