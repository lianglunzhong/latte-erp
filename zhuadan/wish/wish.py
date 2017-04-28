# -*- coding: utf-8 -*-
import requests
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

import pprint
pp = pprint.PrettyPrinter(indent=4)

class Wish(object):

    def __init__(self, client_id, client_secret, refresh_token):
        self.base_url = "https://merchant.wish.com/api/v2"
        self.client_id = client_id
        self.client_secret = client_secret
        self.refresh_token = refresh_token
        self.access_token = ''
        self._get_new_access_token()

    # 获取新的access_token, wish每次调用之前生成access_token
    def _get_new_access_token(self):
        # api_name = 'oauth/refresh_token'
        url = "{base_url}/oauth/refresh_token".format(base_url=self.base_url)
        data = {
            'client_id'     : self.client_id,
            'client_secret' : self.client_secret,
            'refresh_token' : self.refresh_token,
            'grant_type'    : "refresh_token",
        }

        r = requests.post(url, data=data, verify=False)
        access_token = r.json().get('data', {}).get('access_token', '')
        self.access_token = access_token

    def list_order(self, since, start=0, limit=50):
        api_name = 'order/get-fulfill'
        url = "{base_url}/{api_name}?start={start}&limit={limit}&since={since}&access_token={access_token}"\
              .format(base_url=self.base_url, api_name=api_name, start=start, limit=limit, since=since, access_token=self.access_token)
        r = requests.get(url)
        print url
        # pp.pprint(r.json())
        return r.json()

    def list_order_by_next_page(self, next_page):
        print next_page
        r = requests.get(next_page) 
        # pp.pprint(r.json())
        return r.json()

    def possback_trackingno(self, tracking_provider, tracking_number, ordernum):
        api_name = 'order/fulfill-one'
        url = "{base_url}/{api_name}"\
              .format(base_url=self.base_url, api_name=api_name)
        data = {
            'tracking_provider' :tracking_provider,
            'tracking_number'   :tracking_number,
            'id'                :ordernum,
            'access_token'      :self.access_token,
        }
        r = requests.post(url, data=data, verify=False)
        return r.json()
