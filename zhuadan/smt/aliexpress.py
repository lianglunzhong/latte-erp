#!/usr/bin/env python
# -*- coding: utf-8 -*-
from hashlib import sha1
import hmac
import requests
requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS = 'ALL'

import pprint
pp = pprint.PrettyPrinter(indent=4)

class Aliexpress(object):

    def __init__(self, app_key, app_pwd, refresh_token):
        # 参数必须不能是unicode
        self.app_key = str(app_key)
        self.app_pwd = str(app_pwd)
        self.access_token = ""
        self.refresh_token = str(refresh_token)
        self.url = "http://gw.api.alibaba.com/openapi/param2/1/aliexpress.open/"
        self._refresh_token()

    def _refresh_token(self):
    	url = 'https://gw.api.alibaba.com/openapi/param2/1/system.oauth2/getToken/' + self.app_key
        url = url + '?grant_type=refresh_token&client_id=' + self.app_key + '&client_secret=' + self.app_pwd + '&refresh_token=' + self.refresh_token
        data = {
            'grant_type' : 'refresh_token',
            'client_id' : self.app_key,
            'client_secret' : self.app_pwd,
            'refresh_token' : self.refresh_token
        }
        r = requests.post(url, data=data)
        access_token = r.json().get('access_token')
        self.access_token = access_token

    def _signature(self, url, secret_key):
        url_path = url[34:]
        s = url_path.replace('?', '')
        s = s.replace('=', '')
        s = s.replace('&', '')
        # print s
        return hmac.new(secret_key, s, sha1).digest().encode('hex').upper()

    def list_order(self, page=1, page_size=20):
        api_name = 'api.findOrderListSimpleQuery'
        url = self.url + api_name + '/' + self.app_key + "?access_token="+self.access_token+"&orderStatus=WAIT_SELLER_SEND_GOODS"+"&page="+ str(page) + "&pageSize=" + str(page_size)
        url = url + "&_aop_signature="+ self._signature(url=url, secret_key=self.app_pwd)
        r = requests.get(url, timeout=5)
        # pp.pprint(r.json())
        return r.json()

    def get_order(self, order_id):
        api_name = 'api.findOrderById'
        url = self.url + api_name + '/' + self.app_key + "?access_token="+self.access_token+"&orderId="+ str(order_id)
        url = url + "&_aop_signature="+ self._signature(url=url, secret_key=self.app_pwd)
        r = requests.get(url, timeout=30)
        # pp.pprint(r.json())
        return r.json()

    def shipment(self, order_id, service_name="", no="", send_type="all"):
        # sent_type: all, part
        api_name = 'api.sellerShipment'
        url = self.url + api_name + '/' + self.app_key + "?access_token="+self.access_token+ \
                "&logisticsNo=" + no + \
                "&outRef=" + str(order_id) + \
                "&sendType=" + send_type + \
                "&serviceName=" + service_name\

        url = url + "&_aop_signature="+ self._signature(url=url, secret_key=self.app_pwd)
        r = requests.get(url, timeout=10)
        # pp.pprint(r.json())
        return r.json()

    def list_logistics_service(self):
        api_name = 'api.listLogisticsService'
        url = self.url + api_name + '/' + self.app_key + "?access_token="+self.access_token
        url = url + "&_aop_signature="+ self._signature(url=url, secret_key=self.app_pwd)
        # r = requests.get(url)
        return r.json()
   

if __name__ == '__main__':
    #test
    app_key         = "5454682"
    app_pwd         = "cA4IhXwCJT"
    refresh_token   = "fb4f377d-089d-4a7f-9430-757caf19b716"
    aliexpress = Aliexpress(app_key=app_key, app_pwd=app_pwd, refresh_token=refresh_token)

    order_data = aliexpress.list_order()
    # order_data = aliexpress.get_order('75240744144158')
    
