# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from product.models import Category

for category in Category.objects.all():
    #category.cn_name = category.name

    try:
        color = category.attributes.filter(name__startswith=u'颜色')[0]
    except IndexError:
        color = None
    print color
    category.color = color

    try:
        size = category.attributes.exclude(name__startswith=u'颜色')[0]
    except IndexError:
        size = None
    print size
    category.size = size

    category.save()


