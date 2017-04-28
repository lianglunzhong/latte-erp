# coding: utf-8
'''
该文件保存部分账号信息, 字段映射, 过期说明, 注意事项等, 可通过该文件生成渠道信息
注意事项: 
    !!!不能在本地登录账号
    wish的订单数据, 一个order只对应一个产品. 如果顾客一次下单多个产品, 也会被分拆成多个订单
    为了节省成本, 抓单时需要进行合单, 根据电话(用户ID)进行合单, 独立的ordernum记录在channel_od_id中
'''

import textwrap
from order.models import Channel

class Accounts(object):
    field_map = {
        # channel => wish
        # "name": "name",
        "arg1": "app_key",
        "arg2": "app_pwd", 
        "arg3": "refresh_token", 
        "arg4": "client_id", 
        "arg5": "client_secret",
    }

    notice = textwrap.dedent(u'''\
        1. !!!不能在本地登录账号
        2. Wish会进行合单
    '''
    )
    
    ###########正式上线后, 下面的无效##############

    account1 = {
                "app_key"       : "invogueplus",
                "app_pwd"       : "147852IV2015",
                "refresh_token" : "bd128242690e43b7b7d15340dbd0565d",
                'grant_type'    : "refresh_token",
                "admin_id"      : 253,
                "admin_email"   : "wang.lu@wxzeshang.com",
                "account"       : "invogueplus",
                "client_id"     : "570f063e1b4ca7214e21bb29",
                "client_secret" : "c274feec59f549e698e4494fec38ed50",
    }
    account_list = [account1]

    # 创建smt的账号信息
    @staticmethod
    def create_smt_channel():
        for account in Accounts.account_list:
            c, flag = Channel.objects.get_or_create(name=account['account'])
            reverse_field_map = {v: k for k, v in Accounts.field_map.iteritems()}
            # print {reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()}
            c.__dict__.update({reverse_field_map.get(k, 'nothing'):v for k, v in account.iteritems()})
            c.type = 3
            c.note = Accounts.notice
            c.save()