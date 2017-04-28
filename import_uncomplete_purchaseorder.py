# coding: utf-8
# 独立执行的django脚本, 需要添加这六行
import sys
import os
import django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import requests
from django.contrib.auth.models import User

from lib.utils import pp, eparse
from lib.iorder import import_order
from order.models import Alias
from supply.models import *

def import_uncomplete_purchaseorder():
    # url = 'http://192.168.11.40:8002/api/new_erp_get_purchaseorder/'
    url = 'http://ky.jinjidexiaoxuesheng.com:8888/api/new_erp_get_purchaseorder/'
    
    unknown_sku = []
    pos = requests.get(url).json()
    print len(pos)
    for po in pos:
        msg = ''
        # 先获取or创建supplier
        supplier = Supplier.objects.filter(name=po['supplier_name']).first()
        if not supplier:
            supplier = Supplier()
            supplier.__dict__.update(po['supplier'])
            supplier.save()

        purchase_order = PurchaseOrder()
        purchase_order.__dict__.update(po)
        purchase_order.supplier = supplier
        assigner = User.objects.filter(username=po['assigner_username']).first()
        purchase_order.manager = assigner
        purchase_order.depot_id = 2

        if po['assigner_username'] == "xing.cheng":
            purchase_order.type = 2
        else:
            purchase_order.type = 0

        purchase_order.save()

        for poi in po['purchase_order_items']:
            item = Alias.objects.filter(sku=poi['item_sku'].strip().upper()).first()
            if not item:
                unknown_sku.append(poi['item_sku'])
                msg += u'产品%s未找到\n' % poi['item_sku']
                continue

            purchase_order_item = PurchaseOrderItem()
            purchase_order_item.__dict__.update(poi)
            purchase_order_item.item = item.item
            purchase_order_item.purchaseorder = purchase_order
            purchase_order_item.save()

            if poi['action_status'] == 2:
                # 更新对单数量
                purchase_order_item.real_qty = purchase_order_item.qty
                purchase_order_item.save()

                # 创建一个新的对单
                poci = PurchaseOrderCheckedItem()
                poci.purchaseorder = purchase_order
                poci.purchaseorderitem = purchase_order_item
                poci.qty = purchase_order_item.qty
                poci.note = u'旧系统导入'
                poci.save()


        ky_id = u"ky中采购单id为:%s\n" % po['ky_id']
        purchase_order.note += ky_id + msg
        purchase_order.save()


    print len(unknown_sku)
    print set(unknown_sku)

if __name__ == '__main__':
    import_uncomplete_purchaseorder()