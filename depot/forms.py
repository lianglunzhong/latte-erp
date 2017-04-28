from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django import forms
from django.forms import ModelForm

from depot.models import *
from dal import autocomplete


class DepotInLogAdminForm(forms.ModelForm):

    class Meta:
        model = DepotInLog
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'depot': autocomplete.ModelSelect2(url='depot-autocomplete'),
                'item': autocomplete.ModelSelect2(url='item-autocomplete'),
                }

class DepotOutLogAdminForm(forms.ModelForm):

    class Meta:
        model = DepotOutLog
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'depot': autocomplete.ModelSelect2(url='depot-autocomplete'),
                'item': autocomplete.ModelSelect2(url='item-autocomplete'),
                }

class DepotManagerAdminForm(forms.ModelForm):

    class Meta:
        model = User
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'manager': autocomplete.ModelSelect2(url='depotUser-autocomplete'),
                }

class DepotAdminForm(forms.ModelForm):

    class Meta:
        model = Depot
        fields = '__all__'

        widgets = {
            'depot': autocomplete.ModelSelect2(url='depot-autocomplete')
        }


class DepotinlogAddForm(ModelForm):
    class Meta:
        model = DepotInLog
        # item_sku = models.CharField(u'', max_length=50, db_index=True, default="")
        fields = ['depot', 'item', 'qty','cost','note','type']
