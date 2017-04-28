# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django import forms
from django.forms import ModelForm

from supply.models import *
from dal import autocomplete

class SupplyAddForm(ModelForm):
    class Meta:
        model = Supplier
        fields = ['name', 'site', 'phone','address','note',]

class PurchaseOrderAdminForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                'supplier': autocomplete.ModelSelect2(url='supplier-autocomplete'),
                'depot': autocomplete.ModelSelect2(url='depot-autocomplete'),
                'manager': autocomplete.ModelSelect2(url='purchaseUser-autocomplete'),
                'parent': autocomplete.ModelSelect2(url='purchaseOrder-autocomplete'),
                }


class SupplyPurchaseAdminForm(forms.ModelForm):

    class Meta:
        model = SupplierProduct
        fields = '__all__'
        widgets = {
                'supplier': autocomplete.ModelSelect2(url='supplier-autocomplete'),
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                }



class SupplierAdminForm(forms.ModelForm):

    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
                'supplier': autocomplete.ModelSelect2(url='supplier-autocomplete')
                }

class PurchaseOrderQualityTestingInlineForm(forms.ModelForm):

    class Meta:
        model = PurchaseOrderQualityTesting
        fields = '__all__'
        widgets = {
                'add_user': autocomplete.ModelSelect2(url='purchaseUser-autocomplete'),
                'purchaseorderitem': autocomplete.ModelSelect2(url='purchaseOrderItem-autocomplete'),
                }

class SupplierAdminManagerForm(forms.ModelForm):

    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
                'manager': autocomplete.ModelSelect2(url='purchaseUser-autocomplete'),
                'login_user': autocomplete.ModelSelect2(url='supplierUser-autocomplete'),
                }

class ForSupplierAdminForm(forms.ModelForm):

    class Meta:
        model = Supplier
        fields = '__all__'
        widgets = {
                'supplier': autocomplete.ModelSelect2(url='forSupplier-autocomplete')
                }

class PurchaseRequestAdminForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequest
        fields = '__all__'

        widgets = {
            'item': autocomplete.ModelSelect2(url='item-autocomplete'),
        }

class PurchaseRequestItemAdminForm(forms.ModelForm):

    class Meta:
        model = PurchaseRequestItem
        fields = '__all__'

        widgets = {
            'manager': autocomplete.ModelSelect2(url='purchaseUser-autocomplete'),
        }

class PurchaseOrderItemCheckForm(forms.Form):

    ACTION_STATUS = (
        (99, u'未处理and部分对单'),
        (0, u'未处理'),
        (1, u'部分对单'),
        (2, u'全部对单'),
        (100,u'全部'),

            )
    status = forms.ChoiceField(choices=ACTION_STATUS,)

class PurchaseOrderActionUserForm(forms.Form):

    manager = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='[采购组]'))