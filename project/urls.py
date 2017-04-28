"""project URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.9/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.conf.urls import url
from django.contrib import admin
from django.conf.urls import url, include
from lib.views import *

urlpatterns = [
    url(r'^$', index, name='index'),
    url(r'^product-autocomplete/$', ProductAutocomplete.as_view(), name='product-autocomplete'),
    url(r'^category-autocomplete/$', CategoryAutocomplete.as_view(), name='category-autocomplete'),
    url(r'^categoryAll-autocomplete/$', CategoryAllAutocomplete.as_view(), name='categoryAll-autocomplete'),
    url(r'^supplier-autocomplete/$', SupplierAutocomplete.as_view(), name='supplier-autocomplete'),
    url(r'^item-autocomplete/$', ItemAutocomplete.as_view(), name='item-autocomplete'),
    url(r'^depot-autocomplete/$', DepotAutocomplete.as_view(), name='depot-autocomplete'),
    url(r'^channel-autocomplete/$', ChannelAutocomplete.as_view(), name='channel-autocomplete'),
    url(r'^itUser-autocomplete/$', ItUserAutocomplete.as_view(), name='itUser-autocomplete'),

    url(r'^productUser-autocomplete/$', ProductUserAutocomplete.as_view(), name='productUser-autocomplete'),
    url(r'^purchaseUser-autocomplete/$', PurchaseUserAutocomplete.as_view(), name='purchaseUser-autocomplete'),
    url(r'^depotUser-autocomplete/$', DepotUserAutocomplete.as_view(), name='depotUser-autocomplete'),
    url(r'^channelUser-autocomplete/$', ChannelUserAutocomplete.as_view(), name='channelUser-autocomplete'),
    url(r'^supplierUser-autocomplete/$', SupplierUserAutocomplete.as_view(), name='supplierUser-autocomplete'),
    url(r'^forSupplier-autocomplete/$', ForSupplierAutocomplete.as_view(), name='forSupplier-autocomplete'),#ForSupplierSupplierProductInline

    url(r'^purchaseOrder-autocomplete/$', PurchaseOrderAutocomplete.as_view(), name='purchaseOrder-autocomplete'),
    url(r'^purchaseOrderItem-autocomplete/$', PurchaseOrderItemAutocomplete.as_view(), name='purchaseOrderItem-autocomplete'),
    # url(r'^productRequestName-autocomplete/$', ProductRequestNameAutocomplete.as_view(), name='productRequestName-autocomplete'),
    url(r'^product/', include('product.urls')),
    url(r'^supply/', include('supply.urls')),
    url(r'^pick/', include('shipping.urls')),
    url(r'^tongguan/', include('tongguan.urls')),
    url(r'^api/', include('api.urls')),
    url(r'^fba/', include('fba.urls')),
    url(r'^admin/', admin.site.urls),
    url(r'^depot/', include('depot.urls')),
    url(r'^order/', include('order.urls')),
]
