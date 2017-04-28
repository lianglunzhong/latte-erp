# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from supply import views

urlpatterns = [
    #供应商管理

    url(r'^supplier/add/$', views.SupplierEdit.as_view(),{'id':0,'flag':'add'}, name='supplier_add',),
    url(r'^supplier/edit/(?P<id>\d+)/$', views.SupplierEdit.as_view(),{'flag':'edit'}, name='supplier_edit'),
    url(r'^supplier/list/$', views.supplier_list, name='supplier_list'),
    url(r'^supplier/delete/$', views.supplier_delete, name='supplier_delete'),

    url(r'^supplier/ajax_item_weight', views.ajax_item_weight, name='ajax_item_weight'),
    url(r'^supplier/ajax_update_poi_trackingNo', views.ajax_update_poi_trackingNo, name='ajax_update_poi_trackingNo'),
    url(r'^supplier/ajax_update_checkorder_num', views.ajax_update_checkorder_num, name='ajax_update_checkorder_num'),

    url(r'^create_purchaseorder/$', views.create_purchaseorder, name='create_purchaseorder'),
    #
    # #供应商角色
    # # url(r'^supplier/info/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^supplier/publish/list/$', views.supplier_delete, name='supplier_delete'),#供应商下架产品
    # url(r'^supplier/publish/add/$', views.supplier_delete, name='supplier_delete'),#供应商发布产品
    # url(r'^supplier/purchaseorder/$', views.supplier_delete, name='supplier_delete'),#供应商被指定的采购单列表
    # url(r'^supplier/publish/delete/$', views.supplier_delete, name='supplier_delete'),#供应商下架产品,删除绑定记录
    #
    # #采购需求
    # url(r'^purchase/need/list/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/need/add/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/need/edit/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/need/delete/$', views.supplier_delete, name='supplier_delete'),#批量删除
    #
    # #采购单
    # url(r'^purchase/order/list/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/order/add/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/order/edit/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/order/delete/$', views.supplier_delete, name='supplier_delete'),#批量删除
    # url(r'^purchase/item/list/$', views.supplier_delete, name='supplier_delete'),
    # url(r'^purchase/item/edit/$', views.supplier_delete, name='supplier_delete'),






]
