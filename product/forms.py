# -*- coding: utf-8 -*-
# from __future__ import unicode_literals
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext, ugettext_lazy as _
from django.conf import settings
from django import forms
from django.forms import ModelForm

from product.models import *
import supply
import depot
from dal import autocomplete

class ProductAddForm(ModelForm):

    class Meta:
        model = Product
        fields = ['category','name', 'cost', 'status', 'brief', 'weight', ]

        widgets = {
            'category': forms.Select(),
            'options': forms.CheckboxSelectMultiple(),
        }   

class ItemAdminForm(ModelForm):

    class Meta:
        model = Item
        fields = '__all__'

        widgets = {
            'item': autocomplete.ModelSelect2(url='item-autocomplete')
        }


class ItemForm(ModelForm):

    class Meta:
        model = Item 
        fields = ['cost', 'qty', ]

class ImgUploadForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()


#class ProductAttributeForm(ModelForm):
#
#    class Meta:
#        model = Product
#        fields = []
#        widgets = {}   
#
#    def __init__(self ,category, *args, **kwargs):
#        super(ProductAttributeForm, self).__init__(*args, **kwargs)
#        _attributes = {}
#        for attribute in category.attributes.all():
#            CHOICES = ((option.id, option.name) for option in attribute.option_set.all())
#            _attributes["ATTRIBUTE_" + str(attribute.id)] = forms.MultipleChoiceField(choices=CHOICES, widget=forms.CheckboxSelectMultiple, label=attribute.name)
#
#        self.fields.update(_attributes)

class ProductAttributeAdminForm(forms.ModelForm):

    class Meta:
        model = ProductAttribute
        fields = '__all__'
        widgets = {
                'options':forms.CheckboxSelectMultiple,
                }

    def __init__(self, *args, **kwargs):
        super(ProductAttributeAdminForm, self).__init__(*args, **kwargs)
        if self.instance.attribute_id:
            self.fields['options'].queryset = Option.objects.filter(deleted=False).filter(attribute_id=self.instance.attribute_id)
            #filter(attribute=self.instance.attribute)


class ProductAdminForm(forms.ModelForm):

    class Meta:
        model = Product
        fields = '__all__'
        exclude = ['options',]
        widgets = {
                'options':forms.CheckboxSelectMultiple,
                'category': autocomplete.ModelSelect2(url='category-autocomplete'),
                'manager': autocomplete.ModelSelect2(url='productUser-autocomplete'),
                }


class ProductFeedbackAdminForm(forms.ModelForm):

    class Meta:
        model = ProductFeedback
        fields = '__all__'
        # exclude = ['options','sku']
        widgets = {
                # 'options':forms.CheckboxSelectMultiple,
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                'manager': autocomplete.ModelSelect2(url='productUser-autocomplete'),
                }


class CategoryAdminForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
                'parent': autocomplete.ModelSelect2(url='category-autocomplete'),
                'manager': autocomplete.ModelSelect2(url='productUser-autocomplete'),
                }

class CategoryAllAdminForm(forms.ModelForm):

    class Meta:
        model = Category
        fields = '__all__'
        widgets = {
                'parent': autocomplete.ModelSelect2(url='categoryAll-autocomplete'),
                'manager': autocomplete.ModelSelect2(url='productUser-autocomplete'),
                }


class ProductRequestAdminForm(forms.ModelForm):

    class Meta:
        model = ProductRequest
        fields = '__all__'
        widgets = {
                'manager': autocomplete.ModelSelect2(url='productUser-autocomplete'),
                }


class ProductRequestProductAdminForm(forms.ModelForm):

    class Meta:
        model = ProductRequest
        fields = '__all__'
        widgets = {
                'product': autocomplete.ModelSelect2(url='product-autocomplete'),
                }


# class ProductRequestNameAdminForm(forms.ModelForm):
#
#     class Meta:
#         model = ProductRequest
#         fields = '__all__'
#         widgets = {
#                 'name': autocomplete.ModelSelect2(url='productRequestName-autocomplete'),
#                 }


class ProductActionUserForm(forms.Form):

    manager = forms.ModelChoiceField(queryset=User.objects.filter(groups__name='[产品组]'))


class ProductActionForm(forms.Form):

    TYPE = (
        (0,u'资料编辑'),
        (1,u'拍照'),
        (2,u'图片编辑'),
    )
    productaction = forms.MultipleChoiceField(choices=TYPE, widget=forms.CheckboxSelectMultiple)
