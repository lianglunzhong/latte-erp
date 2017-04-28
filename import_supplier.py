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
from supply.models import *
from faker import Factory
from django.conf import settings

import requests


# 第一步先导入表格中的供应商资料
path = os.getcwd()
file2 = 'ky_supplier_new.csv'#D:\mywork\coding\latte\category.csv

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)

index = True
i = 0
for row in reader:

    i = i+1
    if index:
        index = False
        continue

    for j in range(0,9):
        row[j] = row[j].decode('gbk').encode('utf-8')#不要相信业务提供的表格
        row[j] = row[j].strip()

    # try:
    #
    #     try:
    #         # supply = Supplier.objects.get(name=row[0],id__gte=6296)
    #         supply = Supplier.objects.get(name=row[0])
    #         print supply.id
    #     except Supplier.DoesNotExist:
    #         supply = Supplier()
    #         supply.name = row[0]
    #         supply.manager_id = 1
    #         supply.site = row[3]
    #         supply.phone = row[7]
    #         supply.address = row[2]
    #         supply.note = row[1]
    #         supply.payment_information = row[8]
    #         supply.save()
    # except:
    #     print u'表格中的供应商保存失败：',row[0]

    try:

        try:
            supply = Supplier.objects.get(name=row[1])
            print supply.id
        except Supplier.DoesNotExist:
            supply = Supplier()
            supply.name = row[1]
            supply.status=1

            if row[6]=='D':
                supply.supplier_class=3
            elif row[6]=='C':
                supply.supplier_class=2
            elif row[6]=='B':
                supply.supplier_class=1
            else:
                supply.supplier_class=0

            if row[7]=='工厂':
                supply.type=2
            elif row[7]=='线上':
                supply.type=1
            else:
                supply.type=0

            if row[9]=='做货':
                supply.purchase_way=2
            else:
                supply.purchase_way=0
            supply.save()
    except:
        print u'表格中的供应商保存失败：%s'% row[1]
handle.close()

exit()
#第二步根据产品表中的供应商名称继续补充
# products = Product.objects.filter(id__gte=306).values('washing_mark')
products = Product.objects.all().values('washing_mark')
for product in products:
    if not product['washing_mark']:
        continue
    try:
        try:
            supply = Supplier.objects.get(name=product['washing_mark'],id__gte=0)
            # print supply.id
        except Supplier.DoesNotExist:
            supply = Supplier()
            supply.name = product['washing_mark']
            supply.manager_id = 1
            supply.save()
    except:
        print u'产品表中的供应商保存失败：%s' % product['washing_mark']
exit()



# url = 'http://ws.jinjidexiaoxuesheng.com/api/supplier/'
url = 'http://192.168.11.74:8001/api/supplier/'


def get_supplier(url):
    r = requests.get(url)
    result = r.json()
    for _supplier in result['results']:
        print _supplier
    
        name = _supplier['name']
        note = _supplier['arg1']
        _id = _supplier['id']
    
        #print _supplier['arg1'].split('\n')[0]
        #print _supplier['arg1'].split('\n')[0].split(' ')[-2]
        supplier, is_created = supply.models.Supplier.objects.get_or_create(name=name, manager_id=1)
        supplier.note = note
        supplier.site = _id
        # supplier.manager_id = 0
        supplier.save()

    if result['next']:
        get_supplier(result['next'])

get_supplier(url)

