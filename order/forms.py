# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django import forms
from django.forms import ModelForm

from order.models import *
from dal import autocomplete

class ProductSaleAdminForm(forms.ModelForm):

    class Meta:
        model = ProductSale
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                'channel': autocomplete.ModelSelect2(url='channel-autocomplete')
                }

class ChannelUserAdminForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # replace args verbose_name
        super(ChannelUserAdminForm, self).__init__(*args, **kwargs)
        try:
            channel_type = (
                (0, u'Choies'),
                (1, u'Amazon'),
                (2, u'Smt'),
                (3, u'Wish'),
                (4, u'Shopify'),
                (5, u'Cdiscount'),
                (6, u'Priceminister'),
                (7, u'Ebay'),
                (8, u'tmp1'),
                (9, u'tmp2'),
                (10, u'tmp3'),
            )
            platform = dict(channel_type).get(self.initial.get('type', -1), '').lower()
            work_module = __import__('zhuadan.{0}.accounts'.format(platform))
            channel = getattr(work_module, platform, None)
            the_field_map = channel.accounts.Accounts.field_map

            for key, value in the_field_map.iteritems():
                self.fields[key].label = value
        except Exception, e:
            pass


    class Meta:
        model = Channel
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                'manager': autocomplete.ModelSelect2(url='channelUser-autocomplete')
                }


class ProductsaleActionForm(forms.Form):
    TYPE = (
        ('change', u'修改产品上架状态'),
        ('outcsv', u'下载产品信息'),
    )
    productaction = forms.MultipleChoiceField(choices=TYPE, widget=forms.CheckboxSelectMultiple)


class UploadFileForm(forms.Form):
    file = forms.FileField()
