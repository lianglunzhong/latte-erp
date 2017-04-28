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

#更新分类表中的color和size
for cate in _product.models.Category.objects.all().order_by('id'):
    cas = cate.attributes.all()
    for ca in cas:
        print ca.id
        if ca.id == 11:
            cate.color_id=ca.id
        else:
            cate.size_id=ca.id
    cate.save()


for pro in _product.models.Product.objects.all().order_by('id'):
    proas = _product.models.ProductAttribute.objects.filter(product_id=pro.id)
    print pro.id
    for proa in proas:
        if proa.attribute_id == 11:
            pro.color_id=proa.id
        else:
            pro.size_id=proa.id
    pro.save()

