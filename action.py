import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()


from faker import Factory
from django.conf import settings
from lib.models import *


process_order()
do_package()
