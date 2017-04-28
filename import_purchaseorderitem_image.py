# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
import csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
import os
from django.core.files import File
import urllib2
from urlparse import urlparse
import urllib2
from django.core.files import File
  #add imprt of content file wrapper
from django.core.files.base import ContentFile
import django
django.setup()
import requests

from product.models import ProductImage,Product
from supply.models import PurchaseOrderItem
from order.models import OrderItem
from depot.models import DepotItem

# photo = ProductImage()
# photo.product_id = 306
# image_url = 'http://d1cr7zfsu1b8qs.cloudfront.net/pimg/o/246205.jpg'
# photo.choies_url = image_url
# name = urlparse(image_url).path.split('/')[-1]
#   #wrap your file content
# content = ContentFile(urllib2.urlopen(image_url).read())
# photo.image.save(name, content, save=True)
# exit()

# image_url = 'http://d1cr7zfsu1b8qs.cloudfront.net/pimg/o/246205.jpg'
# photo = ProductImage()
# photo.product_id = 306
# photo.choies_url = image_url
# result = urllib.urlretrieve(image_url)
# photo.image.save(
#     os.path.basename(image_url),
#     File(open(result[0]))
#     )
# photo.save()
#
# exit()
#采购单产品图片
print 'start product image'
products = set(PurchaseOrderItem.objects.all().values_list('item__product_id', flat=True))
pp = Product.objects.filter(id__in=products).order_by('id')


for p in pp:
    p_old = ProductImage.objects.filter(product_id=p.id,deleted=False).first()
    if p_old:
        print 'exist',p.id
        continue

    try:
        product_url = 'http://www.choies.com/api/item?sku=%s' % p.choies_sku
        product_r = requests.get(product_url)
    except Exception,e:
        continue
        print 'error',p.id,e

    # print product_r.json()
    try:
        images = product_r.json()[0]['images']
    except:
        images = []
        continue

    photo = ProductImage()
    photo.product_id = p.id

    photo.choies_url = images[0]
    name = urlparse(images[0]).path.split('/')[-1]
    content = ContentFile(urllib2.urlopen(images[0]).read())
    photo.image.save(name, content, save=True)
    print photo.product_id

print 'end product image'
print 'start orderitem image'
#订单产品图片
products = set(OrderItem.objects.all().values_list('item__product_id', flat=True))
pp = Product.objects.filter(id__in=products).order_by('id')


for p in pp:
    p_old = ProductImage.objects.filter(product_id=p.id,deleted=False).first()
    if p_old:
        print 'exist',p.id
        continue
    try:
        product_url = 'http://www.choies.com/api/item?sku=%s' % p.choies_sku
        product_r = requests.get(product_url)
    except Exception,e:
        continue
        print 'error',p.id,e

    # print product_r.json()
    try:
        images = product_r.json()[0]['images']
    except:
        images = []
        continue

    photo = ProductImage()
    photo.product_id = p.id

    photo.choies_url = images[0]
    name = urlparse(images[0]).path.split('/')[-1]
    content = ContentFile(urllib2.urlopen(images[0]).read())
    photo.image.save(name, content, save=True)
    print photo.product_id
print 'end orderitem image'
print 'start DepotItem image'
#库存产品图片
products = set(DepotItem.objects.all().values_list('item__product_id', flat=True))
pp = Product.objects.filter(id__in=products).order_by('id')


for p in pp:
    p_old = ProductImage.objects.filter(product_id=p.id,deleted=False).first()
    if p_old:
        print 'exist',p.id
        continue
    try:
        product_url = 'http://www.choies.com/api/item?sku=%s' % p.choies_sku
        product_r = requests.get(product_url)
    except Exception,e:
        continue
        print 'error',p.id,e

    # print product_r.json()
    try:
        images = product_r.json()[0]['images']
    except Exception,e:
        images = []
        continue

    photo = ProductImage()
    photo.product_id = p.id

    photo.choies_url = images[0]
    name = urlparse(images[0]).path.split('/')[-1]
    content = ContentFile(urllib2.urlopen(images[0]).read())
    photo.image.save(name, content, save=True)
    print photo.product_id

print 'end DepotItem image'
