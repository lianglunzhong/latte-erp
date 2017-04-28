import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()


from product.models import *
from faker import Factory
from django.conf import settings
