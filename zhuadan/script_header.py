# coding:utf-8

# 独立执行的django脚本, 需要添加这四行
import sys
import os
import django
sys.path.append(os.getcwd()[:os.getcwd().index('zhuadan')])
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

