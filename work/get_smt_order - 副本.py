# coding: utf-8
# 独立执行的django脚本, 需要添加这六行
import sys
import os
import django
sys.path.append("E:\python\latte")
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

from lib.utils import manage_script
from zhuadan.smt.get_smt_order import get_smt_order

manage_script(get_smt_order)