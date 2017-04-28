# -*- coding: utf-8 -*-
from hashlib import sha1
import hmac
import requests

import pprint
pp = pprint.PrettyPrinter(indent=4)


class Shopify(object):
    def __init__(self, shop_name, api_key, password):
        self.shop_name = shop_name
        self.api_key = api_key
        self.password = password
        self.base_url = "https://{api_key}:{password}@{shop_name}.myshopify.com/admin".format(
            api_key = self.api_key,
            password = self.password,
            shop_name = self.shop_name,
        )

    def get_order_list(self, page=1, limit=20, from_time='', order_ids=None):
        '''get方式抓取订单, 其他可选参数见网址
        https://help.shopify.com/api/reference/order#index
        这里的order_ids保存在order的channel_ordernum中, 是list类型
        '''
        url = "{base_url}/orders.json".format(base_url=self.base_url)
        params = {
            'created_at_min': from_time,
            'limit': limit,
            'page': page,
        }
        if order_ids:
            params['ids'] = '.'.join(order_ids)
        r = requests.get(url, params=params, timeout=10)
        return r.json()

    def upload_tracking(self, order_id=None, tracking_number='', tracking_url='',
                        line_items_ids=None, tracking_company='Other', notify_customer=True):
        """回传物流号
        'order_id': 315636, # shopify的order id, 保存在order的channel_ordernum中
        'tracking_no': '9604078875',
        'tracking_company': 'Other',
        'tracking_urls': 'http://www.dhl.com/en.html',
        'line_items_ids': orderitem_id组成的列表
        notify_customer: 是否发邮件通知客户

        其他数据参见: https://docs.shopify.com/api/reference/fulfillment
        """
        data = {}
        data['fulfillment'] = {
            "tracking_company": str(tracking_company),
            "tracking_number": str(tracking_number),
            "tracking_url": str(tracking_url),
            "notify_customer": notify_customer,
            "line_items": [{'id': i} for i in line_items_ids],
        }

        url = '{base_url}/orders/{id}/fulfillment.json'.format(base_url=self.base_url, id=order_id)
        r = requests.post(url=url, data=json.dumps(data), headers={"content-type": "application/json"}, verify=False)
        return r.json()

