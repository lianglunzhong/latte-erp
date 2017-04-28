# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from product.models import Product, Item , Category, Attribute, Option
from django.contrib.auth.models import User
from order.models import ChannelGroup,Channel,Order,OrderItem
from depot.models import Depot
from lib.models import COUNTRIES,Country

## init attributes
#attribute_data = [
#        { 'id': 1, 'name':u'颜色', 'options': u'红,白,蓝,黑' },
#        { 'id': 2, 'name':u'尺码', 'options': 'X,M,L,XL,XXL'},
#    ]
#
#for _data in attribute_data:
#    try:
#        attribute = Attribute.objects.get(id=_data['id'])
#        attribute.name = _data['name']
#        attribute.save()
#    except:
#        attribute,is_created = Attribute.objects.get_or_create(id=_data['id'], name=_data['name'])
#
#    for _option in _data['options'].split(','):
#        option, is_created = Option.objects.get_or_create(name=_option, attribute=attribute)
#
#
## init category
#category_data = [
#        { 'id': 1, 'name':u'女装',  },
#        { 'id': 2, 'name':u'裙子',  },
#        { 'id': 3, 'name':u'鞋子',  },
#        { 'id': 4, 'name':u'箱包',  },
#    ]
#
#for _data in category_data:
#    try:
#        product = Category.objects.get(id=_data['id'])
#        product.name = _data['name']
#        product.save()
#    except:
#        Category.objects.get_or_create(id=_data['id'], name=_data['name'])

# #init channel & group
# channelgroup_data=[
#     {'id':1,'name':u'销售1组','channel':[{'name':u'1号','type':0},{'name':u'2号','type':1}]},
#     {'id':2,'name':u'销售2组','channel':[{'name':u'1号','type':0},{'name':u'2号','type':1}]},
#     {'id':3,'name':u'销售3组','channel':[{'name':u'1号','type':0},{'name':u'2号','type':1}]},
# ]
# users=User.objects.all()
# user=users[0]
# for _data in channelgroup_data:
#     try:
#         channelgroup = ChannelGroup.objects.get(id=_data['id'])
#         channelgroup.name = _data['name']
#         channelgroup.manager = user
#         channelgroup.save()
#     except:
#         channelgroup,is_created = ChannelGroup.objects.get_or_create(id=_data['id'], name=_data['name'],manager=user)
#
#     for _dat in _data['channel']:
#         _dat['name']=channelgroup.name+_dat['name']
#         try:
#             channel = Channel.objects.get(name=_dat['name'])
#             channel.manager = user
#             channel.type = _dat['type']
#             channel.channel_group=channelgroup
#             channel.save()
#         except:
#             channel,is_created = Channel.objects.get_or_create(name=_dat['name'],manager=user,type= _dat['type'],channel_group=channelgroup)
#
# #init depot
# users=User.objects.all()
# user=users[0]
#
# depot_data=[
#     {'id':1,'name':u'虚拟仓库1'},
#     {'id':2,'name':u'虚拟仓库2'},
# ]
# for _data in depot_data:
#     try:
#         depot = Depot.objects.get(id=_data['id'])
#         depot.name = _data['name']
#         depot.manager = user
#         depot.save()
#     except:
#         depot,is_created = Depot.objects.get_or_create(id=_data['id'], name=_data['name'],manager=user)
#
# #init product
#
# categorys=Category.objects.all()

#product_data=[
#    {'id':1,'name':'SKU0001','category':0,'options':u'红,白,蓝,黑,X,M,L,XL,XXL'},
#    {'id':2,'name':'SKU0002','category':1,'options':u'红,白,蓝,黑,X,M,L,XL,XXL'},
#    {'id':3,'name':'SKU0003','category':2,'options':u'红,白,蓝,黑,X,M,L,XL,XXL'},
#    {'id':4,'name':'SKU0004','category':3,'options':u'红,白,蓝,黑,X,M,L,XL,XXL'},
#]
#
#for _data in product_data:
#    _data['category'] = categorys[_data['category']]
#
#    try:
#        product = Product.objects.get(id=_data['id'])
#        product.name = _data['name']
#        product.category = _data['category']
#        product.save()
#    except:
#        product,is_created = Product.objects.get_or_create(id=_data['id'], name=_data['name'],category=_data['category'])
#
#
#
#    product.options.clear()
#
#    for _option in _data['options'].split(','):
#        option,is_created=Option.objects.get_or_create(name=_option)
#
#
#
#        product.options.add(option)
#
#
#
##product item (product ,key ,sku)
#productitem_data=[
#    {"id":1,"product_id":1,"key":"1-1"},
#    {"id":2,"product_id":2,"key":"2-2"},
#    {"id":3,"product_id":3,"key":"3-3"},
#    {"id":4,"product_id":4,"key":"4-4"},
#]
#
#for _data in productitem_data:
#    product=Product.objects.get(id=_data['product_id'])
#    try:
#        item = Item.objects.get(id=_data['id'])
#        item.product=product
#        item.key = _data['key']
#        item.sku = product.sku
#        item.save()
#    except:
#        item,is_created = Item.objects.get_or_create(id=_data['id'], product=product,key=_data['key'],sku=product.sku)
#
#
#
#
##init order
#users=User.objects.all()
#user=users[0]
#channels = Channel.objects.all()
#
#order_data = [
#    {'id':1,'ordernum':'abc0000000001','channel':1},
#    {'id':2,'ordernum':'abc0000000002','channel':2},
#    {'id':3,'ordernum':'abc0000000003','channel':3},
#]
#
#for _data in order_data:
#    try:
#        order = Order.objects.get(id=_data['id'])
#        order.ordernum = _data['ordernum']
#        order.channel = channels[_data['channel']]
#        order.manager = user
#        order.save()
#    except:
#        order,is_created = Order.objects.get_or_create(id=_data['id'], ordernum=_data['ordernum'],channel=channels[_data['channel']],manager=user)
#
#
#
##order item (order ,item)
#orderitem_data=[
#    {"id":1,"order_id":1,"item_id":1},
#    {"id":2,"order_id":1,"item_id":2},
#    {"id":3,"order_id":2,"item_id":3},
#]
#
#for _data in orderitem_data:
#    order=Order.objects.get(id=_data['order_id'])
#    item=Item.objects.get(id=_data['item_id'])
#    try:
#        orderitem = OrderItem.objects.get(id=_data['id'])
#        orderitem.order = order
#        orderitem.item = item
#        orderitem.save()
#    except:
#        orderitem,is_created = OrderItem.objects.get_or_create(id=_data['id'], order=order,item=item)

#init country
country_data=COUNTRIES

for i in country_data:
    try:
        country = Country.objects.get(code=i[0])
        country.name = i[1]
        country.save()
    except:
        country,is_created = Country.objects.get_or_create(code=i[0], name=i[1])






