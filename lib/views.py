# -*- coding: utf-8 -*-
from django.shortcuts import render

from dal import autocomplete
from django.template import Context, loader, RequestContext, Template
from django.shortcuts import render_to_response, get_object_or_404,redirect

from product.models import Category, Product,Item,ProductRequest
from supply.models import Supplier,PurchaseOrder,PurchaseOrderItem
from depot.models import Depot
from order.models import Channel
from django.contrib.auth.models import User
from mptt.models import MPTTModel, TreeForeignKey

def index(request):
    data = {}
    return redirect("/admin")
    # return render_to_response('index.html', data, context_instance=RequestContext(request))

class ProductAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Product.objects.none()

        qs = Product.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs

class CategoryAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Category.objects.none()

        qs = Category.objects.filter(deleted=False,children__isnull=True)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

class CategoryAllAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Category.objects.none()

        qs = Category.objects.filter(deleted=False)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

class SupplierAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Supplier.objects.none()

        qs = Supplier.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs

class DepotAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Depot.objects.none()

        qs = Depot.objects.all()

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class ItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Item.objects.none()

        qs = Item.objects.all()

        if self.q:
            qs = qs.filter(sku__istartswith=self.q)

        return qs


class ChannelAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Channel.objects.none()

        qs = Channel.objects.filter(deleted=False)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


class ItUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[开发组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class ProductUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[产品组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class PurchaseUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[采购组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class DepotUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[仓库组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class ChannelUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[渠道销售组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class SupplierUserAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return User.objects.none()

        qs = User.objects.filter(groups__name='[供应商组]')

        if self.q:
            qs = qs.filter(first_name__istartswith=self.q)

        return qs


class ForSupplierAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return Supplier.objects.none()
        current_user_id = self.request.user.id
        qs = Supplier.objects.filter(login_user_id=current_user_id,deleted=False)

        if self.q:
            qs = qs.filter(name__istartswith=self.q)

        return qs


# class ProductRequestNameAutocomplete(autocomplete.Select2QuerySetView):
#     def get_queryset(self):
#         # Don't forget to filter out results depending on the visitor !
#         if not self.request.user.is_authenticated():
#             return ProductRequest.objects.none()
#         qs = ProductRequest.objects.filter(deleted=False)
#
#         if self.q:
#             qs = qs.filter(name__istartswith=self.q)
#
#         return qs

class PurchaseOrderAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return PurchaseOrder.objects.none()

        qs = PurchaseOrder.objects.all()

        if self.q:
            qs = qs.filter(id__istartswith=self.q)

        return qs


class PurchaseOrderItemAutocomplete(autocomplete.Select2QuerySetView):
    def get_queryset(self):
        # Don't forget to filter out results depending on the visitor !
        if not self.request.user.is_authenticated():
            return PurchaseOrderItem.objects.none()

        qs = PurchaseOrderItem.objects.all()

        if self.q:
            qs = qs.filter(id__istartswith=self.q)

        return qs