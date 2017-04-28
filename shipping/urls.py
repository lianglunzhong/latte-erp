# -*- coding: utf-8 -*-
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include

from shipping import views

urlpatterns = [
    # 拣货页面
    url(r'^index/$', views.index, name='pick_index'),
    url(r'^list/(?P<pick_parm>[^/]*)/$', views.pick_list, name='pick_list'),
    url(r'^assign_shipping/(?P<assign_parm>[^/]*)/$', views.assign_shipping, name='assign_shipping'),
    url(r'^get_tracking_no/$', views.get_tracking_no, name='get_tracking_no'),
    url(r'^create/$', views.pick_create, name='pick_create'),
    url(r'^sort/$', views.pick_sort, name='pick_sort'),
    url(r'^packaging/$', views.pick_packaging, name='pick_packaging'),
    url(r'^print_label/$', views.print_label, name='print_label'),
    url(r'^ajax_sort/$', views.ajax_sort, name='ajax_sort'),
    url(r'^abnormal/$', views.pick_abnormal, name='pick_abnormal'),
    url(r'^re_print/$', views.pick_re_print, name='pick_re_print'),
    url(r'^manual_deliver/$', views.manual_deliver, name='pick_manual_deliver'),
    url(r'^execute_deliver/(?P<status>[^/]*)/$', views.execute_deliver, name='pick_execute_deliver'),
    url(r'^assign/$', views.assign_assigner, name='pick_assign_assigner'),
    
]
