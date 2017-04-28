# coding: utf-8
'''
该文件保存速卖通所有账号的信息, 字段映射, 过期说明, 注意事项等, 可通过该文件生成渠道信息
注意事项: 
    服务器需要配置hosts: 110.75.69.81 gw.api.alibaba.com
    refresh_token updated: 2016-05-25
    request请求需要添加配置: requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'
'''
import textwrap
from order.models import Channel

class Accounts(object):
    field_map = {
        # channel => smt
        # "name": "name",
        "arg1": "account",
        "arg2": "app_key", 
        "arg3": "app_pwd", 
        "arg4": "refresh_token", 
    }

    notice = textwrap.dedent(u'''\
        1. 密码更换的时候, refresh_token会失效, 需要更换(员工离职需要更换密码)
        2. refresh_token的有效期是半年, 半年后需要重新申请
    '''
    )

    ###########正式上线后, 下面的无效##############
    
    # sophiaclothing@outlook.com, orge&0*ni6z2n9syg
    account1 = {
        "app_key"       : "5454682",
        "app_pwd"       : "cA4IhXwCJT",
        "refresh_token" : "c2cb6404-3072-4657-b665-3873683c72a6",
        "name"          : "NAE04",
        "account"       : "sophiaclothing@outlook.com",
    }

    # 411250218@qq.com, rene&062am9hdjjd
    account2 = {
        "app_key"       : "9925657",
        "app_pwd"       : "gQBrbHCgAFT",
        "refresh_token" : "5f98444e-583e-45f6-87ab-b5cb20166c45",
        "name"          : "NAE03",
        "account"       : "411250218@qq.com",
    }

    # zhujoe1234@hotmail.com, longp0629lmn*oroadq
    account3 = {
        "app_key"       : "7662707",
        "app_pwd"       : "5SzJb}UPzS",
        "refresh_token" : "e474aff6-723a-478e-a414-592a8f3c3af1",
        "name"          : "NAE01",
        "account"       : "zhujoe1234@hotmail.com",
    }

    # choies2015@outlook.com, snowi%tehyj0#wh629
    account4 = {
        "app_key"       : "5683288",
        "app_pwd"       : "CFNSv7duHf",
        "refresh_token" : "5b2ffb0b-c451-47b8-a297-d5acd0f3cb8a",
        "name"          : "NAE02",
        "account"       : "choies2015@outlook.com",
    }

    # itgirlchoies@outlook.com, rede#tifix062nb9zjt
    account5 = {
        "app_key"       : "4858341",
        "app_pwd"       : "ZO2dH9OUWrwa",
        "refresh_token" : "071377b8-8794-493d-ac44-43e4d9c33107",
        "name"          : "NAE05",
        "account"       : "itgirlchoies@outlook.com",
    }

    # Clothinkfashion520@outlook.com aftow062wwh9ser*nnt
    account6 = {
        "app_key"       : "27760999",
        "app_pwd"       : "yuJC7DNDKQ",
        "refresh_token" : "bad61e14-989a-4258-84f1-ad92da88f4f7",
        "name"          : "NAE06",
        "account"       : "Clothinkfashion520@outlook.com",
    }
    account_list = [account1, account2, account3, account4, account5, account6]

    # 创建smt的账号信息
    @staticmethod
    def create_smt_channel():
        for account in Accounts.account_list:
            c = Channel.objects.get(name=account['name'])
            reverse_field_map = {v: k for k, v in Accounts.field_map.iteritems()}
            # print {reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()}
            c.__dict__.update({reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()})
            c.type = 2
            c.note = account['account']
            c.save()


