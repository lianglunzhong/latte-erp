# -*- coding: utf-8 -*-
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import reverse
import csv
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
#from django.core.mail import send_mail,send_mass_mail
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
import random
from django.template import Context, loader, RequestContext, Template

from django.contrib.auth.models import User


admin.site.site_header = u"wxzeshang"
#admin.site.site_header = u"（╯' - ')╯︵ ┻━┻   ┬─┬ ノ( ' - 'ノ)   (╯°Д°)╯︵ ┻━┻"

from lib.models import *

class NotifyAdmin(admin.ModelAdmin):
    ordering = ['-id']
    date_hierarchy = 'created'
    save_as = True
    save_on_top = True
    list_display = ('id','title', 'action', 'is_read', 'created', 'read_time', ) 

admin.site.register(Notify, NotifyAdmin)

class CountryAdmin(admin.ModelAdmin):
    def get_actions(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
    #Disable delete
        return False

    save_as = True
    save_on_top = True
    search_fields = ['name','code','cn_name' ]
    list_display = ('id', 'name', 'cn_name', 'code', 'number', 'created', 'updated', 'deleted')

admin.site.register(Country, CountryAdmin)

class NoDeleteActionModelAdmin(admin.ModelAdmin):

    def get_actions(self, request):
        #Disable delete
        actions = super(NoDeleteActionModelAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        #Disable delete
        return False

class NoDeleteActionMPTTModelAdmin(MPTTModelAdmin):

    def get_actions(self, request):
        #Disable delete
        actions = super(MPTTModelAdmin, self).get_actions(request)
        del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        #Disable delete
        return False

def search_fun(search_keys, search_term, queryset):
    id_list = []
    search_term = search_term.strip()
    #外键不使用模糊搜索
    #如果search_term无法转化成整形, 则不是外键
    try:
        int(search_term)
    except:
        search_keys = [i for i in search_keys if "id" not in i]

    #根据输入条件, 判断是什么样的模糊搜索
    if search_term and search_term[-1] == '%':
        search_term = search_term[:-1]
        search_type = '__istartswith'
    elif search_term and search_term[0] == '%':
        search_term = search_term[1:]
        search_type = '__icontains'
    else:
        search_type = ''

    #循环获取不同字段的id
    for search_field in search_keys:
        search_dict = {}
        search_dict['%s%s'%(search_field, search_type)] = search_term
        search_ids = list(queryset.filter(**search_dict).values_list('id', flat=True))
        id_list += search_ids
    return id_list

class ShippingAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    list_display = ('id', 'name', 'label', 'brief', 'link', 'sort', 'active', 'default', 'price', 'off',)
admin.site.register(Shipping, ShippingAdmin)

class ShippingZoneAdmin(admin.ModelAdmin):

    # hide Delete Action
    def get_actions(self, request):
        actions = super(ShippingZoneAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    list_display = ('id', 'name', 'shipping')
    filter_horizontal = ['countries']
    readonly_fields = ['shipping']
    #inlines = [ProductPromotionConditionInline]

    save_as = True
    save_on_top = True
admin.site.register(ShippingZone, ShippingZoneAdmin)


class ShippingPriceAdmin(admin.ModelAdmin):

    # hide Delete Action
    def get_actions(self, request):
        actions = super(ShippingPriceAdmin, self).get_actions(request)
        if not request.user.is_superuser:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        else:
            return False

    ordering = ['weight','shipping_zone']
    list_display = ('id', 'weight', 'price', 'offset_price', 'shipping_zone')
    #filter_horizontal = ['countries']
    #inlines = [ProductPromotionConditionInline]

    save_as = True
    save_on_top = True
admin.site.register(ShippingPrice, ShippingPriceAdmin)


class ShippingCostAdmin(admin.ModelAdmin):
    save_as = False
    save_on_top = True
    search_fields = ('id', 'tracking_no' , 'invoice_no')
    list_display = ('id', 'tracking_no', 'invoice_no', 'map_status', 'check_status')
    list_filter = ('map_status', 'check_status')

admin.site.register(ShippingCost, ShippingCostAdmin)
