# coding: utf-8
from order.models import Channel

def _obj_set_attr(obj, field_map):
    try:
        for key, value in field_map.iteritems():
            setattr(obj, value, getattr(obj, key))
    except Exception, e:
        print e
    return obj

def get_accounts(channel_type_name):
    try:
        channel_type = (
            (0, u'Choies'),
            (1, u'Amazon'),
            (2, u'Smt'),
            (3, u'Wish'),
            (4, u'Shopify'),
            (5, u'Cdiscount'),
            (6, u'Priceminister'),
            (7, u'Ebay'),
            (8, u'tmp1'),
            (9, u'tmp2'),
            (10, u'tmp3'),
        )
        channel_type_name = channel_type_name.lower()
        name_code = {j.lower():i for i, j in channel_type}
        work_module = __import__('zhuadan.{0}.accounts'.format(channel_type_name))
        channel = getattr(work_module, channel_type_name, None)
        the_field_map = channel.accounts.Accounts.field_map

        channel_accounts = Channel.objects.filter(type=name_code[channel_type_name]).filter(deleted=False)
        # 排除关键参数缺失的账号
        for arg, custom_name in the_field_map.iteritems():
            kwargs = {arg:''}
            channel_accounts = channel_accounts.exclude(**kwargs)

        channel_accounts = [_obj_set_attr(i, the_field_map) for i in channel_accounts]

    except Exception, e:
        print e
        channel_accounts = []

    return channel_accounts

