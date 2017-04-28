# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

reload(sys)
sys.setdefaultencoding('utf-8')
import csv

from product.models import *
from faker import Factory
from django.conf import settings

import supply
import requests

path = os.getcwd()
# file2 = 'product_new20160708.csv'#D:\mywork\coding\latte\category.csv
file2 = 'product_new20160709.csv'
handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)

index = True
i = 0
for row in reader:

    i = i+1
    if index:
        index = False
        continue

    for j in range(0,13):
        row[j] = row[j].decode('gbk').encode('utf-8')#不要相信业务提供的表格
        row[j] = row[j].strip()
        if j in [8, 10]:
            try:
                row[j] = float(row[j])
            except:
                row[j] = 0

        if j==12:
            try:
                row[j]=row[j].split('|')[0]
                row[j]=float(row[j])
            except:
                row[j]=0

    # print ro
    # cate = Category.objects.filter(brief__contains=row[5].capitalize()).order_by('id')[:1].values()
    cate = Category.objects.filter(brief__icontains =row[5]).order_by('id').first()
    if not cate:
        print row[0], row[5], u'无效的分类名称'
        continue
    
    p = Product.objects.filter(choies_sku=row[0]).first()

    if not p and cate:
        try:
            product = Product()
            product.category_id = cate.id
            product.name = row[3]
            product.cn_name = row[4]
            product.cost = row[8]
            product.manager_id = 1
            product.material = row[6]
            product.brief = row[11]
            product.choies_sku = row[0]
            product.weight = row[10]
            product.description = row[1]
            product.choies_supplier_name = row[7]
            product.choies_site_url = row[13]
            product.price=row[12]
            product.save()
        except Exception,e :
            print row[0],row[5], u"产品创建失败", str(e)


handle.close()
exit()

url = 'http://ws.jinjidexiaoxuesheng.com/api/item/'
none_category, is_created = product.models.Category.objects.get_or_create(name='none')

def get_product(url):
    r = requests.get(url)
    result = r.json()
    for _item in result['results']:
        model = _item['model']
        print model

        try:
            _product = product.models.Product.objects.get(brief=model)
            continue
        except product.models.Product.DoesNotExist:
            _product = product.models.Product()
            _product.brief = model

        _category = _item['category']
        if _category:
            category_url = 'http://ws.jinjidexiaoxuesheng.com/api/category/%s' % _category
            category_r = requests.get(category_url)
            category_name = category_r.json()['name'] + '/' + category_r.json()['cn_name']
            print category_name
            category, is_created = product.models.Category.objects.get_or_create(name=category_name)
        else:
            category = none_category

        _product.name = _item['name']
        _product.cost = _item['cost']
        _product.weight = _item['weight']
        _product.category = category
        _product.save()

            
        item_url = 'http://ws.jinjidexiaoxuesheng.com/api/item/?model=%s' % model
        item_r = requests.get(item_url)

        print item_r.json()
        print item_r.json()['count']

    if result['next']:
        get_product(result['next'])

get_product(url)

