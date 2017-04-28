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

from product.models import *
from supply.models import *


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

# 产品绑供应商
print 'image start'
pp = Product.objects.filter(id__gte=1000).order_by('id')
for p in pp:
    try:
        product_url = 'http://www.choies.com/api/item?sku=%s' % p.choies_sku
        product_r = requests.get(product_url)
    except Exception,e:
        print 'error get choies image:',e
        continue

    # print product_r.json()
    try:
        images = product_r.json()[0]['images']
    except Exception,e:
        images = []
        continue

    for p_image in images:
        try:
            p_old = ProductImage.objects.get(product_id=p.id,choies_url=p_image)
            print 'exist:',p_old.product_id,'###',p_old.id
        except ProductImage.DoesNotExist:

            photo = ProductImage()
            photo.product_id = p.id

            photo.choies_url = p_image
            name = urlparse(p_image).path.split('/')[-1]
            content = ContentFile(urllib2.urlopen(p_image).read())
            photo.image.save(name, content, save=True)
            print photo.product_id


print 'image end'