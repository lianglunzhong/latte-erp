# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from product import views

urlpatterns = [
    #url(r'^add/$', views.product_add, name='product_add',),
    #url(r'^add/$', views.ProductEdit.as_view(),{'id':0,'flag':'add'}, name='product_add',),
    #url(r'^edit/(?P<id>\d+)/$', views.ProductEdit.as_view(),{'flag':'edit'}, name='product_edit'),#产品审核在此处,修改供应商顺序,绑定供应商
    #url(r'^list/$', views.product_list, name='product_list'),#筛选产品审核状态功能
    #url(r'^delete/$', views.product_delete, name='product_delete'),
    #url(r'^item/list/$', views.product_delete, name='product_item'),
    #url(r'^item/edit/(?P<id>\d+)/$', views.product_delete, name='product_item'),
    #url(r'^item/list/$', views.product_delete, name='product_item'),
    # url(r'^temp/$', views.temp),
    # url(r'^upload/$', views.upload_img),

    url(r'^handle/$', views.handle, name='product_handle'),
    url(r'^import_update_product/$', views.import_update_product, name='import_update_product'),
    url(r'^import_buyer_product/$', views.import_buyer_product, name='import_buyer_product'),
    url(r'^import_ws_product/$', views.import_ws_product, name='import_ws_product'),
]
