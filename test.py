import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from faker import Factory
from django.conf import settings

#from lib.action import order_do_package, order_verify, package_get_items
import order as _order
from order.models import Alias

aliass = Alias.objects.filter(channel_id=1)
    
print 'product_name,choies_model,sku,choies_sku'
for alias in aliass:
    print "%s,%s,%s,%s" % (alias.item.product.name,alias.item.product.choies_sku, alias.item.sku , alias.sku,)

