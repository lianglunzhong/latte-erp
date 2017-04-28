# -*- coding: utf-8 -*-
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.models import User, Group
from django.shortcuts import render

from rest_framework.renderers import JSONRenderer
from rest_framework.parsers import JSONParser

from product.models import Product, Category
from order.models import Order, OrderItem
from api.serializers import UserSerializer, CategorySerializer, ProductSerializer, GroupSerializer, OrderSerializer
from rest_framework import viewsets
from rest_framework import filters

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupSerializer

class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.filter(deleted=False)
    serializer_class = ProductSerializer

class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.filter(deleted=False)
    serializer_class = CategorySerializer
    filter_backends = (filters.DjangoFilterBackend,)
    filter_fields = ('name', 'id', 'status')

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.filter(deleted=False)
    serializer_class = OrderSerializer
    filter_backends = (filters.DjangoFilterBackend,)

#def category_list(request):
#    cate_list = CategorySerializer(Category.objects.all(), many=True)
#    return HttpResponse(cate_list.data)
#
#
#def product_list(request):
#    p = Product.objects.filter(pk=2)
#    pp = ProductSerializer(p, many=True)
#    for i in  pp.data:
#        cc2 = CategorySerializer(Category.objects.filter(pk=int(i['category'])), many=True)
#    return HttpResponse(pp.data,cc2.data)
