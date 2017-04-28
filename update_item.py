# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
import csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()


from product.models import *
from order.models import *

# 根据产品和产品属性生成属性产品
products = Product.objects.all().order_by('id')
# products = Product.objects.filter(id=5393).order_by('id')
for p in products:
    p.update_items()
    for ii in Item.objects.filter(product_id=p.id,deleted=False):
        key_arrs = ii.key.split("-")[1:]
        # print 'key_arrs',key_arrs
        sku_str = p.choies_sku.upper()
        for k in key_arrs:
            k = int(k)
            if k==0:
                continue
            product_option = Option.objects.get(pk=k)
            # print product_option
            sku_str = sku_str+'-'+str(product_option.name.upper())
            # print 'sku_str',sku_str
        try:

            Alias.objects.get_or_create(sku=sku_str,channel_id=1,item_id=ii.id)
        except Exception,e:
            print p.id, 'key_arrs',e

exit()

