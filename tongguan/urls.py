# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from tongguan import views

urlpatterns = [
    # 拣货页面
    url(r'^index/$', views.index, name='tongguan_index'),
    url(r'^product_3bao/$', views.product_3bao, name='tongguan_product_3bao'),
    url(r'^package_3bao/$', views.package_3bao, name='tongguan_package_3bao'),
    url(r'^k_tongguan/$', views.k_tongguan, name='tongguan_k_tongguan'),
    url(r'^bulk_action/$', views.bulk_action, name='tongguan_bulk_action'),
    url(r'^shouji/$', views.shouji, name='tongguan_shouji'),
    url(r'^export_upload_format/$', views.export_upload_format, name='tongguan_export_upload_format'),    

    url(r'^print_barcode/$', views.print_barcode, name='print_barcode'),
]
