# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os
import product

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.contrib.auth.models import User

path = os.getcwd()
file2 = 'category_new.csv'#D:\mywork\coding\latte\category.csv

handle = open(path + '/' + file2, 'rb')
reader = csv.reader(handle)

data_list=[]
for row in reader:
    row[0]=row[0].strip().capitalize()
    row[1]=row[1].strip().capitalize()
    row[2]=row[2].strip().capitalize()
    row[3]=row[3].strip().capitalize()
    tmp_dict={"before":row[0],"first":row[3],"second":row[2],}
    if row[2]!=row[1]:
        tmp_dict["third"]=row[1]
    data_list.append(tmp_dict)

for i in range(len(data_list)):
    if i==0:
        continue
    # print data_list[i]

    c1, created1 = product.models.Category.objects.get_or_create(name=data_list[i]["first"],level=0,code=1,manager_id=1,parent_id__isnull=True)
    c2, created2 = product.models.Category.objects.get_or_create(name=data_list[i]["second"],level=1,code=1,manager_id=1,parent=c1)
    if "third" in data_list[i]:
        c3, created3 = product.models.Category.objects.get_or_create(name=data_list[i]["third"],level=2,code=1,manager_id=1,parent=c2)

    if "third" in data_list[i]:
        cx=c3
    else:
        cx=c2

    bri=cx.brief
    if len(bri)==0:
        cx.brief=bri+data_list[i]["before"]
    else:
        cx.brief=bri+';'+data_list[i]["before"]
    cx.save()

handle.close()
