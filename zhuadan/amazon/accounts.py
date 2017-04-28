# coding: utf-8
'''
该文件保存亚马逊所有账号的信息, 字段映射, 注意事项等, 可通过该文件生成渠道信息
注意事项: 
    不能在本地登录亚马逊账号, 只能使用虚拟机进行远程登录, 防止产生关联
    api的测试, 当使用开发者账号进行抓单和回传的时候, 可以在本地进行
'''

import textwrap
from order.models import Channel

class Accounts(object):
    '''亚马逊的授权原理: 每个卖家账号对开发者账号进行授权, 然后获得auth_token
    开发者账号使用auth_token和卖家的account_id, 以及开发者自身的access_key和secret_key进行抓单
    目前我们只有美国的开发者账号, 欧洲的开发者账号等多渠道那里
    '''

    field_map = {
        # channel => amazon
        "name": "name",
        "arg1": "continent",
        "arg2": "account_id", 
        "arg3": "marketplaceids", 
        "arg4": "auth_token", 
    }

    notice = textwrap.dedent(u'''\
        1. 必须要使用远程服务器才能登陆亚马逊账号(防关联)
        2. 使用开发者账号通过api进行抓单, 可本地执行
        3. 开发者账号是分美洲, 欧洲的
    '''
    )

    @staticmethod
    def obj_set_attr(obj):
        try:
            for key, value in Accounts.field_map.iteritems():
                setattr(obj, value, getattr(obj, key))
        except Exception, e:
            print e   

    developers = {}
    developers['America'] = {
                "account"       : "America",
                "account number": "4120-1352-2179",
                "access_key"    : "AKIAJCZD4ZNPVBU36WKQ",
                "secret_key"    : "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",
                #开发者的下面三个数据没什么作用, 只作记录
                "account_id"    : "A2S5GUYABT3LJL",
                "marketplaceids": ["ATVPDKIKX0DER",],
    }
    developers['Europe'] = {
                "account"       : "Europe",
                "account number": "",
                "access_key"    : "",
                "secret_key"    : "",
                #开发者的下面三个数据没什么作用, 只作记录
                "account_id"    : "",
                "marketplaceids": [],
    }


    ###########正式上线后, 下面的无效##############

    account1 = {
                "name"          : "NAM01",
                "continent"     : "America",
                # "access_key"    : "AKIAJE7QKBLWVEGMZRJQ",
                # "secret_key"    : "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",
                "account_id"    : "A3THBIK7QYKUUV",
                "marketplaceids": ["ATVPDKIKX0DER",],
                "auth_token"    : "amzn.mws.7ea98e1b-7f63-e99e-e945-72d8ee6099ae",
                "shop_id"       : 2,
                "admin_id"      : 40,
                "rules"         : ['CHOIES000',],
                # "config_type"   : 'SKU_MAP_Amazon_amazon',
    }

    account2 = {
                "name"          : "NAM02",
                "continent"     : "America",
                # "access_key"    : "AKIAI45PGDQ6STTVZRBA",
                # "secret_key"    : "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",
                "account_id"    : "A3KBE96P1K0C2M",
                "marketplaceids": ["ATVPDKIKX0DER",],
                "auth_token"    : "amzn.mws.3aa98e22-9c22-c54e-6c9e-fa3812aa9017",
                "shop_id"       : 25,
                "admin_id"      : 40,
                "rules"         : ['C', 'P'],
                # "config_type"   : 'SKU_MAP_Amazon_Clothink',
    }

    account3 = {
                "name"           : "Joeoy",
                "continent"     : "America",
                # "access_key"    : "",
                # "secret_key"    : "",
                "account_id"    : "A1MEOVZHZDZLVI",
                "marketplaceids": ["ATVPDKIKX0DER",],
                "auth_token"    : "amzn.mws.18a98e23-8270-b3dc-1a4d-7db8df73b21d",
                "shop_id"       : 26,
                "admin_id"      : 40,
                "rules"         : ['JY', ],
                # "config_type"   : 'SKU_MAP_Amazon_Joeoy',
    }

    account4 = {
                "name"          : "amazonpersun",
                "continent"     : "America",
                # "access_key"    : "AKIAJ4SA3NAF72K7NP3A",
                # "secret_key"    : "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",
                "account_id"    : "ATH55QXWHZ5C9",
                "marketplaceids": ["ATVPDKIKX0DER",],
                "auth_token"    : "amzn.mws.eaa9c439-9595-054e-726a-169a65647253",
                "shop_id"       : 13,
                "admin_id"      : 68,
                "rules"         : ['PS', ],
    }

    account5 = {
                "name"          : "AmazonVS",
                "continent"     : "America",
                # "access_key"    : "",
                # "secret_key"    : "",
                "account_id"    : "A2GX98PBXR883J",
                "marketplaceids": ["ATVPDKIKX0DER",],
                "auth_token"    : "amzn.mws.68aa2ae2-9287-c095-6e41-3f774f753b4b",
                "shop_id"       : 28,
                "admin_id"      : 68,
                "rules"         : ['CR', ],
    }

    account6 = {
                "name"          : "AmazonChoiesEU",
                "continent"     : "Europe",
                # "access_key"    : "AKIAJKLQSM6CWOBO5D4A",
                # "secret_key"    : "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",
                "account_id"    : "A342WRA4JV8SY3",
                "marketplaceids": ["A1F83G8C2ARO7P",],
                "auth_token"    : "",
                "shop_id"       : 2,
                "admin_id"      : 40,
    }

    account_list = [account1, account2]

    # 创建amazon的账号信息
    @staticmethod
    def create_amazon_channel():
        for account in Accounts.account_list:
            c, flag = Channel.objects.get_or_create(name=account['name'])
            reverse_field_map = {v: k for k, v in Accounts.field_map.iteritems()}
            # print {reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()}
            account['marketplaceids'] = '#'.join(account['marketplaceids'])
            print account
            c.__dict__.update({reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()})
            c.type = 1
            # c.note = Accounts.notice
            c.save()
