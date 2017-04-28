# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from depot import views

urlpatterns = [
    #仓库模块

    url(r'^export_depotitem_cost_inventory/$', views.export_depotitem_cost_inventory, name='export_depotitem_cost_inventory'),
    url(r'^import_depotitem_location/$', views.import_depotitem_location, name='import_depotitem_location'),
    url(r'^bulk_print_barcode/$', views.bulk_print_barcode, name='bulk_print_barcode'),
    url(r'^import_depotinlog/$', views.import_depotinlog, name='import_depotinlog'),
    url(r'^import_depotoutlog/$', views.import_depotoutlog, name='import_depotoutlog'),
]
