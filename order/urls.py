# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import include

from order import views

urlpatterns = [
    url(r'^handle/$', views.handle, name='order_handle'),
]
