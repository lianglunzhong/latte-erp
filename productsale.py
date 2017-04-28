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
from order.models import OrderItem, ProductSale

for orderitem in OrderItem.objects.filter(deleted=False):
    item = orderitem.item
    channel = orderitem.order.channel

    if not item:
        continue

    product = item.product
    print orderitem.sku

    productsale, is_created = ProductSale.objects.get_or_create(product=product, channel=channel)
    productsale.status = 2 
    productsale.note = orderitem.sku
    productsale.save()
