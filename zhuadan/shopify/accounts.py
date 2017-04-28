# coding: utf-8
'''
该文件保存shopify所有账号的信息, 字段映射, 注意事项等, 可通过该文件生成渠道信息
注意事项: 
    暂无
'''

import textwrap
from order.models import Channel

class Accounts(object):
    '''授权使用的是app模式
    在本地使用卖家账号登录https://www.shopify.com/login
    apps => installed => private apps => create private app
    根据提示, 创建即可
    '''

    field_map = {
        # channel => amazon
        "name": "name",
        "arg1": "shop_name",
        "arg2": "api_key", 
        "arg3": "password", 
        "arg4": "shared_secret", 
    }

    notice = textwrap.dedent(u'''\
        1. 可以在本地登录多个账号的后台管理
        2. 务必: 新账号要设置订单号的前缀, 否则订单号会发生重复
           settings => general => 最下面的prefix, suffix可根据需求设置
        3. 产品的sku需要包含size属性
        4. 获得密钥步骤: apps => installed => private apps => create private app
    '''
    )


    account1 = {
        'name': 'nystyle',
        'domain': 'nystyle.myshopify.com',
        'api_key': '8e44c7694f0328701a748b83f3276855',
        'password': 'a204f2c062a814ff90049b8f02078fe2',
        'shared_secret': '2aa2cf8acb835ce075a71e09adc89562',
    }

    account2 = {
        'name': 'chiclookcloset',
        'domain': 'chiclookcloset.myshopify.com',
        'api_key': '6583c8a84db8d7a5c11768d8f02151e8',
        'password': '727ce7f5de634911f873546b2ffcf652',
        'shared_secret': 'f0354257f961b30c780660ccd1421b79',
    }
    account3 = {
        'name': 'halofashion',
        'domain': 'halofashion.myshopify.com',
        'api_key': '2e8e57b53af610eccacd770b5e17e528',
        'password': '0dbf4f863de690fdeb6c858229711ac6',
        'shared_secret': 'fe002e90807ff3805dc4e6752f9c7f2a',
    }
    account4 ={
        'name': 'stayinsummer',
        'domain': 'stayinsummer.myshopify.com',
        'api_key': '1616c25a5ed6d5025b7ab93e653c7f96',
        'password': 'ec5c3bae5e40f3f2b1c157adeb52c174',
        'shared_secret': 'c03c24215d4ddccae906e06a9d451b23',
    }

    account_list = [account1, account2, account3, account4] 

    # 创建shopify的账号信息
    @staticmethod
    def create_shopify_channel():
        for account in Accounts.account_list:
            c, flag = Channel.objects.get_or_create(name=account['name'])
            reverse_field_map = {v: k for k, v in Accounts.field_map.iteritems()}
            # print {reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()}
            c.__dict__.update({reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()})
            c.type = 4
            c.note = Accounts.notice
            c.save()
