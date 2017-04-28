# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.conf import settings

import supply as _supply
import product as _product
# 生成供应商产品
for product in _product.models.Product.objects.all().order_by('id'):
    # print product.washing_mark
    try:
        supplier = _supply.models.Supplier.objects.get(name=product.choies_supplier_name)
    except _supply.models.Supplier.DoesNotExist:
        print u'产品中的供应商名称不存在:%s'% product.choies_supplier_name
        supplier = ''

    if supplier:
        try:
            _supply.models.SupplierProduct.objects.get_or_create(product=product,supplier=supplier,site_url=product.brief,)
        except Exception,e:
            print product.sku,e



