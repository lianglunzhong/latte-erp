# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from fba import views

urlpatterns = [
   url(r'^$', views.index, name='fba_index',),
   url(r'^import_data/$', views.import_data, name='fba_import_data'),
   url(r'^forecast/$', views.forecast, name='fba_forecast'),
   url(r'^ajax_process/$', views.ajax_process, name='fba_ajax_process'),
]
