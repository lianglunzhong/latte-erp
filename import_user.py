# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.contrib.auth.models import User

path = os.getcwd()
file = 'user.csv'

handle = open(path + '/' + file) 
handle = path + '/' + file 
reader = csv.reader(open(handle, 'rb'))

index = True
for row in reader:
    if index:
        index = False
        continue

    name = row[0].strip()
    email = row[1].strip()
    if row[2]:
        user_name = row[2].strip()
    else:
        user_name = email.split('@')[0]
    try:
        user = User.objects.get(username=user_name)
    except User.DoesNotExist:
        user = User.objects.create_user(user_name, email, '123456')

    user.first_name = name
    user.is_staff = True
    user.is_active = True
    print user.email
    user.save()
