# coding: utf-8
# 独立执行的django脚本, 需要添加这六行
import sys
import os
import django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import requests
from lib.utils import pp, eparse
from lib.iorder import import_order
from order.models import Channel

def import_uncomplete_order():
    msg = ''
    # url = 'http://192.168.11.40:8002/api/new_erp_get_order/'
    url = 'http://ky.jinjidexiaoxuesheng.com:8888/api/new_erp_get_order/'
    
    orders = requests.get(url).json()
    for order in orders:
        channel = Channel.objects.filter(name=order['channel']).first()
        if not channel:
            print u"channel: %s not exist" % order['channel']
            continue
        

        order['channel'] = channel
        order['create_time'] = eparse(order['create_time'])
        try:
            order['latest_ship_date'] = eparse(order['latest_ship_date'])
        except:
            order['latest_ship_date'] = None

        res = import_order(order)
        if not res['success']:
            print res['msg']

if __name__ == '__main__':
    import_uncomplete_order()