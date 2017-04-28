# -*- coding: utf-8 -*-
from django.contrib import admin
from django.conf.urls import url, include
from django.conf.urls import patterns
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404,redirect
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import reverse
from django.core.paginator import Paginator
import csv
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
from lib.utils import pp, get_now, eu, write_csv, eparse, add8
#from django.core.mail import send_mail,send_mass_mail
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
import random
from django.template import Context, loader, RequestContext, Template
from django.template.response import TemplateResponse,HttpResponse
from django.contrib.auth.models import User

from django.contrib.contenttypes.admin import  GenericTabularInline
from product.models import *
from supply.models import *
from depot.models import *
from lib.admin import NoDeleteActionModelAdmin, NoDeleteActionMPTTModelAdmin
from supply.forms import *
from product.forms import *
from product.admin import ItemInline,ProductImageInline,ProductAttributeInline, SupplierProductInline, ProductSaleInline, ProductFeedbackInline
from django.contrib import messages
import json
from django.views.decorators.csrf import csrf_exempt
from django.contrib.admin import SimpleListFilter

class PurchaseManagerFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'manager'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_assigner', '(None)'])
        # assigner_ids = ProductAction.objects.values_list("manager_id").distinct()
        # users = User.objects.filter(id__in=assigner_ids).order_by('username')
        users = User.objects.filter(groups__name='[采购组]').filter(is_staff=1).order_by('username')
        for user in users:
            name = u"%s[%s]" % (user.first_name, user.last_name)
            user_list.append([user.id, name])
        return user_list
    def queryset(self, request, queryset):
        if self.value() and self.value()!='No_assigner':
            return queryset.filter(manager_id=self.value())
        elif self.value() == 'No_assigner':
            return queryset.filter(manager_id__isnull=True)
        else:
            return queryset.all()

class PurchaseCheckorderManagerFilter(SimpleListFilter):
    title = u'对单人'
    parameter_name = 'add_user'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_assigner', '(None)'])
        # assigner_ids = ProductAction.objects.values_list("manager_id").distinct()
        # users = User.objects.filter(id__in=assigner_ids).order_by('username')
        users = User.objects.filter(groups__name='[采购组]').filter(is_staff=1).order_by('username')
        for user in users:
            name = u"%s[%s]" % (user.first_name, user.last_name)
            user_list.append([user.id, name])
        return user_list
    def queryset(self, request, queryset):
        if self.value() and self.value()!='No_assigner':
            return queryset.filter(add_user_id=self.value())
        elif self.value() == 'No_assigner':
            return queryset.filter(add_user_id__isnull=True)
        else:
            return queryset.all()

class SupplyImageInline(admin.TabularInline):
    model = SupplyImage
    extra = 0

    def get_queryset(self, request):
        query_set = SupplyImage.objects.filter(deleted=False)
        return query_set

    def thumb(self, obj):

        # images = product.models.ProductImage.objects.filter(product_id=obj.product.id).order_by('-id').all()
        # url = ""
        if obj.image:
            output =u'<img src="/media/%s" width="100px"/>' % (obj.image)
        else:
            url = "http://placehold.it/100x100"
            output =u'<img src="%s" width="100px"/>' % (url)
        return output

    thumb.allow_tags = True
    thumb.short_description = u"预览图"

    fields = ['thumb','image', 'img_adder', 'created', 'updated', 'deleted']
    readonly_fields = ('thumb', 'img_adder', 'created', 'updated',)
    extra = 0

#class SupplierAdmin(NoDeleteActionModelAdmin):
class SupplierAdmin(admin.ModelAdmin):

    form = SupplierAdminManagerForm

    def save_formset(self, request, form, formset, change):

        if formset.model != SupplyImage:
            return super(SupplierAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)

        for instance in instances:
            if not instance.pk:
                instance.img_adder = request.user
            instance.save()
        formset.save_m2m()

    def supplier_product_list(self, obj):
        sp_num = SupplierProduct.objects.filter(deleted=False,supplier=obj.id).count()
        if obj.id:
            output =u'<a href="/admin/supply/supplierproduct?supplier=%s" target="_blank">产品列表:%d</a>' % (obj.id,sp_num)
        else:
            output =u''
        return output

    supplier_product_list.allow_tags = True
    supplier_product_list.short_description = u"供应商产品列表"

    save_as = True
    save_on_top = True
    search_fields = ['name','phone' ]
    list_filter = ('type','status','purchase_way','supplier_class')
    list_display = ('id', 'name','supplier_class','type','status','purchase_way','supplier_product_list', 'site', 'phone', 'address','tax_id', 'note', 'manager', 'created', 'updated', 'deleted')
    #list_editable = ('status', 'cost', 'price' ,'weight')
    fields = ['name','manager','supplier_class','type','status','purchase_way','category','site','phone','address','tax_id','note','payment_information','login_user']

    inlines = [SupplyImageInline,]

    def get_urls(self):
        urls = super(SupplierAdmin, self).get_urls()
        my_urls = [
            url(r'^supplier_list/$', self.supplier_list),
            url(r'^test2/(?P<id>\d+)$', self.test2),
            # url(r'^supplier_product/(?P<id>\d+)$', self.test2),
        ]
        return my_urls + urls

    def supplier_list(self, request):

        from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

        search = request.GET.get('search')
        if not search:
            search = ''
        page_want = request.GET.get('p')
        supplier = Supplier()
        list = supplier.supplier_list(search,request.user.id)#根据负责人筛选供应商列表

        paginator = Paginator(list, 10)

        try:
            page_info = paginator.page(page_want)
        except PageNotAnInteger:
            page_info = paginator.page(1)
        except EmptyPage:
            page_info = paginator.page(paginator.num_pages)

        return TemplateResponse(request, "supplier_list.html",{'info':page_info,'search':search, 'opts': self.model._meta,'root_path': self.get_urls(),})

    def test2(self, request,id):
        supply = Supplier.objects.get(pk=id)

        return TemplateResponse(request, "test.html",{'title':'Review entry: %s' % supply.name,'entry':supply, 'opts': self.model._meta,'root_path': self.get_urls(),})

admin.site.register(Supplier, SupplierAdmin)


class SupplyImageAdmin(NoDeleteActionModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.img_adder_id:
            obj.img_adder_id = request.user.id
        super(SupplyImageAdmin, self).save_model(request, obj, form, change)

    form = SupplierAdminForm
    save_as = True
    save_on_top = True
    search_fields = ['supply__name', ]
    list_display = ('id', 'supplier', 'img_adder', 'created', 'updated', 'deleted')
    readonly_fields = ('created', 'updated','img_adder')
    #list_editable = ('status', 'cost', 'price' ,'weight')

admin.site.register(SupplyImage, SupplyImageAdmin)


class ProductInline(admin.TabularInline):
    model = product.models.Product
    extra = 0
    fields = ['sku','category', 'name', 'cost', 'manager', 'status']
    # readonly_fields = ('thumb', 'img_adder', 'created', 'updated',)
    extra = 0


class SupplierProductAdmin(NoDeleteActionModelAdmin):

    form =SupplyPurchaseAdminForm

    def thumb(self, obj):

        images = product.models.ProductImage.objects.filter(product_id=obj.product.id).order_by('-id').all()
        url = ""
        output = ''
        if images:
            for image in images:
                url = '/media/' + str(image.image)
                output = output + u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.product.get_admin_url(),url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.product.get_admin_url(),url)
        output+=u'</a>'
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    # TODO clear， error
    def p_link_category_filed(self,obj):
        if obj:
            category_name = product.models.Category.objects.filter(product=obj.product.category.id).values('name')
            output = u'<a href="%s" target="_blank">%s.%s</a><br/><br/><a href="%s" target="_blank">%s</a>'% (obj.product.get_admin_url(),obj.product.id,obj.product.name,obj.product.category.get_admin_url(), "")
            #output = u'<a href="%s" target="_blank">%s.%s</a><br/><br/><a href="%s" target="_blank">%s</a>'% (obj.product.get_admin_url(),obj.product.id,obj.product.name,obj.product.category.get_admin_url(), category_name[0]['name'])
        else:
            output = u''

        return output

    p_link_category_filed.allow_tags = True
    p_link_category_filed.short_description = "产品名称/分类"

    def p_link_supply_filed(self,obj):
        if obj:
            output = u'<a href="%s" target="_blank">%s.%s</a>'% (obj.supplier.get_admin_url(),obj.supplier.id,obj.supplier.name)
        else:
            output = u''

        return output

    p_link_supply_filed.allow_tags = True
    p_link_supply_filed.short_description = "供应商名称"

    save_as = True
    save_on_top = True
    search_fields = ['supplier__name','product__name', ]
    list_filter = ('deleted',)
    list_display = ('id', 'p_link_supply_filed', 'p_link_category_filed','supplier_sku','thumb', 'order', 'supplier_period', 'supplier_cost', 'supplier_min_qty','created', 'updated', 'deleted')
    # inlines = [ForSupplierProductInline, ]
admin.site.register(SupplierProduct, SupplierProductAdmin)


class PurchaseOrderItemInline(admin.TabularInline):

    form = ItemAdminForm

    def thumb(self, obj):
        # images = obj.get_images()
        # output = ""
        # if images:
        #     for image in images:
        #         url = '/media/' + str(image.image)
        #         output = output + u'<img src="%s" width="100px"/>' % (url)
        #         break
        # else:
        #     url = "http://placehold.it/100x100"
        #     output =u'<img src="%s" width="100px"/>' % (url)
        output = u'<img src="%s" width="100px"/>' % (obj.item.product.get_image_thumb())
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    def purchase_request_filed(self, obj):
        pr = PurchaseRequestItem.objects.filter(purchaseorderitem_id=obj.id,deleted=False).first()
        if pr:
            # output = u'%s'%pr.purchaserequest
            output = u'<a href="/admin/supply/purchaserequest/%d/change/" target="_blank">%s</a>'% (pr.purchaserequest_id,pr.purchaserequest)
        else:
            output = u''
        return output

    purchase_request_filed.allow_tags = True
    purchase_request_filed.short_description = u"采购方案"


    model = PurchaseOrderItem
    fields = ['id','item', 'thumb', 'purchaseorder', 'cost', 'qty','real_qty','depotinlog_qty', 'status', 'action_status', 'estimated_date', 'in_status', 'purchase_request_filed' ]
    readonly_fields = ('id','purchaseorder', 'thumb', 'real_qty','depotinlog_qty','purchase_request_filed',)
    extra = 0
    # max_num = 0
    can_delete = False

class DepotInLogInline(GenericTabularInline):

    model = DepotInLog
   #ct_field_name = 'content_type'
   #id_field_name = 'object_id'

    readonly_fields = ('depot', 'item', 'qty', 'type', 'operator','deleted')
    extra = 0
    max_num = 0 #入库记录不可以手动填写
    can_delete = False #入库记录手动删除

class DepotOutLogInline(GenericTabularInline):

    model = DepotOutLog
    readonly_fields = ('depot', 'item', 'qty', 'type', 'operator','deleted')
    extra = 0
    max_num = 0 #入库记录不可以手动填写
    can_delete = False #入库记录手动删除

class PurchaseOrderCheckedItemInline(admin.TabularInline):

    model = PurchaseOrderCheckedItem

    def get_queryset(self, request):

      query_set = PurchaseOrderCheckedItem.objects.filter(deleted=False)
      return query_set

    readonly_fields = ('purchaseorderitem', 'qty', 'add_user', 'depotinlog_qty', 'status','deleted')
    extra = 0
    max_num = 0
    can_delete = False

class PurchaseOrderQualityTestingInline(admin.TabularInline):


    form = PurchaseOrderQualityTestingInlineForm
    model = PurchaseOrderQualityTesting
    fields = ['purchaseorder', 'purchaseorderitem','qty','status','deleted','note', 'add_user','created','updated']
    readonly_fields = ('created','updated')
    extra = 0
    #max_num = 0
    can_delete = False


def update_purchaseorder_status_1(modeladmin, request, queryset):
    for po in queryset:
        if po.status == 0:
            po.status=1
            po.save()

update_purchaseorder_status_1.short_description = u"批量修改采购单状态为开始采购"


def update_purchaseorder_manager(modeladmin, request, queryset):

    if 'do_action' in request.POST:
        form = PurchaseOrderActionUserForm(request.POST)
        if form.is_valid():
            manager_id = form.cleaned_data['manager']
            for pd in queryset:
                pd.manager = manager_id
                pd.save()

            messages.success(request, '执行成功')
    else:
        form = PurchaseOrderActionUserForm()

        return TemplateResponse(request, 'update_purchaseorder_manager.html',
            {'title': u'选择正确的采购人',
             'objects': queryset,
             'form':form,
             'action':'update_purchaseorder_manager'})

update_purchaseorder_manager.short_description = u"批量修改采购人"


def output_purchaseorder(modeladmin, request, queryset):

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="filename.csv"'

    writer = csv.writer(response)
    writer.writerow(['purchaseorder_id', 'purchaseorder_supplier'])
    for po in queryset:
        writer.writerow([po.id,po.supplier.name])

    return response

output_purchaseorder.short_description = u"下载采购单"


class PurchaseOrderAdmin(NoDeleteActionModelAdmin):

    def save_formset(self, request, form, formset, change):
        if formset.model != PurchaseOrderItem:
            return super(PurchaseOrderAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)

        for instance in instances:
            # if not instance.pk:
            instance.depot = instance.purchaseorder.depot
            instance.supplier = instance.purchaseorder.supplier

            instance.save()
        formset.save_m2m()

    def save_model(self, request, obj, form, change):
        if not obj.creater_id:
            obj.creater = request.user

        if not obj.manager:
            supplier = Supplier.objects.get(id=obj.supplier_id)
            obj.manager = supplier.manager#采购人员就是供应商绑定的用户
        obj.updater = request.user
        super(PurchaseOrderAdmin, self).save_model(request, obj, form, change)

    def supplier_link(self,obj):
        str = u'<a href="%s" target="_blank">供应商详情</a>' %obj.supplier.get_admin_url()
        return str
    supplier_link.allow_tags = True
    supplier_link.short_description = "供应商详情"

    def export_purchaseorder(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF') 
        response['Content-Disposition'] = 'attachment; filename="print_purchaseorder.csv"'
        writer = csv.writer(response)
        writer.writerow(["采购ID","采购列表ID","货品入库状态","item","渠道别名sku","Model","Size","Links","供应商名称","供应商sku","备注","负责人","采购单状态","结算状态","采购条目状态","对单状态","数量","对单数量","未对单数量","入库数量","单价","物流号"])
        for query in queryset:
            purchase_order_items = PurchaseOrderItem.objects.filter(purchaseorder_id=query.id).exclude(status=0).exclude(purchaseorder__status=4)
            for purchase_order_item in purchase_order_items:
                csvlist = []
                order_alias = order.models.Alias.objects.filter(channel_id=1,item_id=purchase_order_item.item_id,deleted=False).first()
                sku_alias =u""
                if order_alias:
                    sku_alias=order_alias.sku
                supplier_product = SupplierProduct.objects.filter(supplier_id=query.supplier_id,product_id=purchase_order_item.item.product_id).first()
                if not supplier_product:
                    supplier_sku = u'供应商sku不存在'
                else:
                    supplier_sku = supplier_product.supplier_sku
                    if not supplier_sku:
                        supplier_sku = " "
                csvlist.append(str(query.id))
                csvlist.append(str(purchase_order_item.id))
                csvlist.append(purchase_order_item.get_in_status_display())                
                csvlist.append(purchase_order_item.item.sku)
                csvlist.append(sku_alias)
                if purchase_order_item.item.product.sku:
                    model = purchase_order_item.item.product.sku
                else:
                    model = " "
                csvlist.append(model)
                size_id = purchase_order_item.item.key.split("-")[2]
                product_option = Option.objects.filter(id =size_id,deleted=False).first()
                if product_option:
                    size = product_option.name
                else:
                    size=''
                csvlist.append(size)
                if purchase_order_item.item.product.brief:
                    links = purchase_order_item.item.product.brief
                else:
                    links = " "
                csvlist.append(links)
                if query.supplier:
                    name = query.supplier.name
                else:
                    name = " "
                csvlist.append(name)
                csvlist.append(supplier_sku)
                if purchase_order_item.note:
                    note = purchase_order_item.note
                else:
                    note = "none"
                csvlist.append(note)
                if query.manager:
                    username = purchase_order_item.purchaseorder.manager.first_name
                else:
                    username = " "
                csvlist.append(username)
                csvlist.append(query.get_status_display())
                csvlist.append(query.get_close_status_display())
                csvlist.append(purchase_order_item.get_status_display())
                csvlist.append(purchase_order_item.get_action_status_display())
                csvlist.append(str(purchase_order_item.qty))
                not_real_qty = purchase_order_item.qty - purchase_order_item.real_qty
                csvlist.append(str(purchase_order_item.real_qty))
                csvlist.append(str(not_real_qty))
                csvlist.append(str(purchase_order_item.depotinlog_qty))
                csvlist.append(str(purchase_order_item.item.cost))
                csvlist.append(str(query.tracking))
                csvlist.append(str(" "))
                csvlist = [ info.encode('utf-8') for info in csvlist if info]
                writer.writerow(csvlist)
        return response

    export_purchaseorder.short_description = u"导出采购列表"

    form = PurchaseOrderAdminForm

    save_as = True
    save_on_top = True
    list_display = ('id', 'supplier', 'note', 'manager', 'type', 'status', 'close_status', 'created', 'creater','shipping_fee','tracking', 'supplier_link')
    list_filter = ('status', 'close_status', 'type',PurchaseManagerFilter)
    inlines = [PurchaseOrderItemInline, PurchaseOrderQualityTestingInline,PurchaseOrderCheckedItemInline, DepotInLogInline, DepotOutLogInline, ]
    readonly_fields = ('creater', 'updater')
    date_hierarchy = 'created'
    search_fields = ['supplier__name','id']
    actions = [update_purchaseorder_manager,update_purchaseorder_status_1,output_purchaseorder,export_purchaseorder]

admin.site.register(PurchaseOrder, PurchaseOrderAdmin)


class PurchaseOrderItemManagerFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'manager'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_Manager', '(None)'])
        po_manager_ids = list(PurchaseOrder.objects.all().values_list('manager_id', flat=True))
        users = User.objects.filter(is_staff=1).filter(id__in=po_manager_ids).order_by('username')
        for user in users:
            name = u"%s[%s]" % (user.first_name, user.last_name)
            user_list.append([user.id, name])
        return user_list
    def queryset(self, request, queryset):
        if self.value() and self.value()!='No_Manager':
            return queryset.filter(purchaseorder__manager_id=self.value())
        elif self.value() == 'No_Manager':
            return queryset.filter(purchaseorder__manager_id__isnull=True)
        else:
            return queryset.all()

class PurchaseOrderItemAdmin(NoDeleteActionModelAdmin):

 # editing an existing object 区分add和change界面，change设置只读
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('status', 'purchaseorder', 'item', 'qty', 'real_qty','depotinlog_qty','depot','supplier')
        return self.readonly_fields

    def purchase_item_id(self,obj):
        str = ''
        order_alias = order.models.Alias.objects.filter(channel_id=1,item=obj.item,deleted=False).first()
        sku_alias =u""
        if order_alias:
            sku_alias=order_alias.sku
        if obj.purchaseorder:
            str = u'<a href="%s" target="_blank">%s</a><br /><br /><a href="%s" target="_blank">%s</a><br />%s' % (obj.purchaseorder.get_admin_url(),obj.purchaseorder,obj.item.get_admin_url(), obj.item,sku_alias)
        return str
    purchase_item_id.allow_tags = True
    purchase_item_id.short_description = "采购单ID/采购物品/渠道别名sku"

    # def purchase_qty(self,obj):
    #     str = u'%s / %s' % (obj.qty, obj.real_qty)
    #     return str
    # purchase_qty.allow_tags = True
    # purchase_qty.short_description = "采购量/入库量"

    def thumb(self, obj):
        output =u'<img src="%s"  width="100px"/>' % (obj.item.product.get_image_thumb())
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    def supplier(self, obj):
        if obj.item.supplier:
            output =u'<a href="%s" target="_blank">%s</>' % (obj.item.supplier.id, obj.item.supplier.name)
        else:
            output = "None"
        return output
    supplier.allow_tags = True
    supplier.short_description = u"Supplier"

    def manager(self, obj):
        #output = (obj.purchaseorder.manager and obj.purchaseorder.manager.first_name) or ''
        if obj.purchaseorder.manager:
            output = obj.purchaseorder.manager.first_name
        else:
            output = ''
        return output
    manager.allow_tags = True
    manager.short_description = u"采购负责人员"

    def item_qty(self, obj):
        return obj.item.qty
    item_qty.short_description = u"库存"

    def input_qty(self,obj):
        str = u'%s' % (obj.real_qty)
        return str
    input_qty.allow_tags = True
    input_qty.short_description = "已对单量"

    def supplier_sku(self,obj):
        supplier_product = SupplierProduct.objects.filter(supplier_id=obj.purchaseorder.supplier.id,product_id=obj.item.product.id).first()
        if not supplier_product:   
            supplier_sku = u''
        else:
            supplier_sku = supplier_product.supplier_sku
        return supplier_sku
    supplier_sku.allow_tags = True
    supplier_sku.short_description = "供应商sku"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(PurchaseOrderItemAdmin, self).get_search_results(request, queryset, search_term)
        q = request.GET.get('q', '')
        if search_term:
            alias_sku = order.models.Alias.objects.filter(sku=q,deleted=False,channel_id=1).first()
            if alias_sku:
                queryset = PurchaseOrderItem.objects.filter(item_id=alias_sku.item.id)
        return queryset, use_distinct

    form = ItemAdminForm

    save_as = True
    save_on_top = True
    list_filter = ('action_status',PurchaseOrderItemManagerFilter,'in_status','purchaseorder__status')
    list_display = ('id','purchase_item_id','thumb','action_status','in_status','status','note','supplier','supplier_sku','manager','item_qty', 'qty','input_qty','real_qty','depotinlog_qty', 'cost','created', )
    #search_fields = ['supplier__name','item__product__sku', 'item__sku','id']
    search_fields = ['id','purchaseorder__id','item__sku']
    # inlines = [DepotInLogInline, ]
    # readonly_fields = ('purchaser',)

    def get_urls(self):
        urls = super(PurchaseOrderItemAdmin, self).get_urls()
        my_urls = [
            url(r'^itemin/$', self.itemin),
            url(r'^itemin_single/$', self.itemin_single),
            url(r'^all_list/$', self.all_list),
            url(r'^all_list_export/$', self.all_list_export),
            url(r'^purchaseorderitem_check/$', self.purchaseorderitem_check),
            url(r'^purchaseorderitem_error_notice/$', self.purchaseorderitem_error_notice),
            url(r'^update_purchaseorderitem_cost/$', self.update_purchaseorderitem_cost),
        ]
        return my_urls + urls

    def all_list(self, request):
        import copy     #对于字典和列表, 需要使用copy方法, 获得一份copy
        data = {}
        #TODO
        data['title'] = u'全部采购订单'
        obj_list = PurchaseOrderItem.objects.filter(purchaseorder__manager_id=request.user.id).filter(action_status=0,purchaseorder__status=1,status=1).exclude(status__in=[0,2]).\
                values('purchaseorder__id','id','supplier__name','item__product__sku','cost','qty','real_qty','item__sku','purchaseorder__manager__first_name', 'note','purchaseorder__supplier__name','purchaseorder__supplier_id','item__product_id','item__key')
        content_dict = {'model':'','po_id':'','poi_id':'','supplier':'','supplier_sku':'','size_qty':{},'image':'','manager':'','note':'','price':0,'all_price':0, 'all_qty':0}
        print_info = {}
        for obj in obj_list:
            #供应商SKU
            supplier_product = SupplierProduct.objects.filter(supplier_id=obj['purchaseorder__supplier_id'],product_id=obj['item__product_id']).first()
            if not supplier_product:   
                supplier_sku = u'不存在供应商sku'
            else:
                supplier_sku = supplier_product.supplier_sku
            model = obj['item__product__sku']
            size_id = obj['item__key'].split("-")[2]
            product_option = Option.objects.filter(id =size_id,deleted=False).first()
            if product_option:
                size = product_option.name
            else:
                size=''
            not_real_qty = obj['qty']-obj['real_qty']
            if model not in print_info:
                print_info[model] = {
                    'purchaseorder_id':[obj['purchaseorder__id'],],
                    'purchaseorderitem_id':[obj['id'],],
                    'supplier':obj['purchaseorder__supplier__name'].encode('utf-8'),
                    'supplier_sku':supplier_sku,
                    'size_qty':{size:obj['qty'],},
                    'model':model,
                    'item':[obj['item__sku'],],
                    'image':Product.objects.get(sku=obj['item__product__sku']).get_image_thumb(),
                    'manager':obj['purchaseorder__manager__first_name'],
                    'price':obj['cost'],
                    'all_qty':obj['qty'],
                    'depotinlog_qty':{size:obj['real_qty'],},
                    'not_depotinlog_qty':{size:not_real_qty,},
                    'all_price':obj['qty'] * obj['cost'],
                    'note':[obj['note'][x:x+10] for x in range(0, len(obj['note']), 10)] if obj['note'] else ''
                }
            else:
                print_info[model]['purchaseorder_id'].append(obj['purchaseorder__id'])
                print_info[model]['purchaseorderitem_id'].append(obj['id'])
                print_info[model]['item'].append(obj['item__sku'])
                print_info[model]['all_qty'] += obj['qty']
                print_info[model]['all_price'] += obj['qty'] * obj['cost']
                if size in print_info[model]['size_qty']:
                    print_info[model]['size_qty'][size] += obj['qty']
                else:
                    print_info[model]['size_qty'][size] = obj['qty']
                if size in print_info[model]['depotinlog_qty']:
                    print_info[model]['depotinlog_qty'][size] += obj['real_qty']
                else:
                    print_info[model]['depotinlog_qty'][size] = obj['real_qty']
                if size in print_info[model]['not_depotinlog_qty']:
                    print_info[model]['not_depotinlog_qty'][size] += not_real_qty
                else:
                    print_info[model]['not_depotinlog_qty'][size] = not_real_qty


        for i in print_info:
            print_info[i]['purchaseorder_id_str'] = set([str(j) for j in print_info[i]['purchaseorder_id']])
            print_info[i]['purchaseorderitem_id_str'] = [str(j) for j in print_info[i]['purchaseorderitem_id']]
        paginator = Paginator(print_info, 300)
        # p = int(request.GET.get('p','')) if request.GET.get('p','').isdigit() else 1
        # print print_info
        # try:
        #     objs = paginator.page(p)
        # except(EmptyPage, InvalidPage):
        #     objs = paginator.page(paginator.num_pages)
        data['objs'] = sorted(print_info.values(), key=lambda x:x["supplier"])
        data['msg'] = u'共计 ( %s 条), 可点击右边的叉叉关闭该提示信息' % len(print_info)
        # return render_to_response('/supply/all_list.html', data, context_instance=RequestContext(request)) 
        return TemplateResponse(request, "all_list.html",{'opts': self.model._meta,'root_path': self.get_urls(),'data':data})

    def all_list_export(self, request):
        import copy     #对于字典和列表, 需要使用copy方法, 获得一份copy
        data = {}
        #TODO
        data['title'] = u'全部采购订单'
        obj_list = PurchaseOrderItem.objects.filter(purchaseorder__manager_id=request.user.id).filter(action_status=0,purchaseorder__status=1,status=1).exclude(status__in=[0,2]).\
                values('purchaseorder__id','id','supplier__name','item__product__sku','cost','qty','real_qty','item__sku','purchaseorder__manager__first_name', 'note','purchaseorder__supplier__name','purchaseorder__supplier_id','item__product_id','item__key')
        content_dict = {'model':'','po_id':'','poi_id':'','supplier':'','supplier_sku':'','size_qty':{},'image':'','manager':'','note':'','price':0,'all_price':0, 'all_qty':0}
        print_info = {}
        for obj in obj_list:
            #供应商SKU
            supplier_product = SupplierProduct.objects.filter(supplier_id=obj['purchaseorder__supplier_id'],product_id=obj['item__product_id']).first()
            if not supplier_product:   
                supplier_sku = u'不存在供应商sku'
            else:
                supplier_sku = supplier_product.supplier_sku
            model = obj['item__product__sku']
            size_id = obj['item__key'].split("-")[2]
            product_option = Option.objects.filter(id =size_id,deleted=False).first()
            if product_option:
                size = product_option.name
            else:
                size=''
            # if model not in print_info:
            print_info[obj['id']] = {
                'purchaseorder_id':obj['purchaseorder__id'],
                'purchaseorderitem_id':obj['id'],
                'supplier':obj['purchaseorder__supplier__name'].encode('utf-8'),
                'supplier_sku':supplier_sku,
                'size_qty':{size:obj['qty'],},
                'model':model,
                'item':obj['item__sku'],
                'manager':obj['purchaseorder__manager__first_name'],
                'price':obj['cost'],
                'all_qty':obj['qty'],
                'all_price':obj['qty'] * obj['cost'],
                'depotinlog_qty':obj['real_qty'],
                'not_depotinlog_qty':obj['qty']-obj['real_qty'],
                'note':[obj['note'][x:x+10] for x in range(0, len(obj['note']), 10)] if obj['note'] else ''
            }

        data['objs'] = sorted(print_info.values(), key=lambda x:x["supplier"])
        response, writer = write_csv("export_purchaseorderitem")
        writer.writerow(["采购单ID","采购条目ID","供货商","供应商SKU","Model","item","size * qty","总数","单价","总价","已对单数量","未对单数量","manager","备注"])
        for j in data['objs']:
            print j['size_qty'].iteritems()
            row = [
                j['purchaseorder_id'],
                j['purchaseorderitem_id'],
                j['supplier'],
                j['supplier_sku'],
                j['model'],
                j['item'],
                ' '.join(['%s:%s' % (size,qty) for size,qty in j['size_qty'].iteritems()]),
                j['all_qty'],
                j['price'],
                j['all_price'],
                j['depotinlog_qty'],
                j['not_depotinlog_qty'],
                j['manager'],
                j['note'],
            ]
            writer.writerow(row)
        return response
        #data['msg'] = u'共计 ( %s 条), 可点击右边的叉叉关闭该提示信息' % len(print_info)
        # return render_to_response('/supply/all_list.html', data, context_instance=RequestContext(request)) 
        # return TemplateResponse(request, "all_list.html",{'opts': self.model._meta,'root_path': self.get_urls(),'data':data})
 #处理历史的采购物品成本
    def update_purchaseorderitem_cost(self, request):
        # pois = PurchaseOrderItem.objects.all()
        # i=0
        # for poi in pois:
        #     p = Product.objects.filter(id=poi.item.product.id).first()
        #     if p and poi.cost == 0:
        #         poi.cost = p.cost
        #         poi.save()
        #         i+=1
        # msg=u'用产品的参考成本修改历史采购物品成本  完成条数%s'% i
        # messages.add_message(request, messages.ERROR, msg)
        # return TemplateResponse(request, "ready_itemin_single.html",{'opts': self.model._meta,'root_path': self.get_urls(),})
         #修改历史采购单的状态
        from supply.models import PurchaseOrderItem
        i=0
        pois = PurchaseOrderItem.objects.exclude(status=0).exclude(in_status=0)
        for poi in pois:
            poi.save()
            poi.update_purchaseorder_status()
            i+=1

        messages.add_message(request, messages.ERROR, i)
        return TemplateResponse(request, "ready_itemin_single.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    def itemin(self, request):
        if not request.user.has_perm('lib.itemin'):
            raise Http404(
                    '您没有采购货品多件扫描入库的权限！')
        if request.POST:
            # print 'request.POST',request.POST
            from supply.views import itemin_action
            return_tag = itemin_action(request.POST.get('sku'),request.POST.get('itemin_number'),request.POST.get('depot'),request.user)
            # print u'%s-%s'% (return_tag['msg'],return_tag['success'])

            if return_tag['success']:
                messages.add_message(request, messages.SUCCESS, return_tag['msg'])
            else:
                messages.add_message(request, messages.ERROR, return_tag['msg'])

        return TemplateResponse(request, "ready_itemin.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    def itemin_single(self, request):
        if not request.user.has_perm('lib.itemin_single'):
            raise Http404(
                    '您没有采购货品单件扫描入库界面的权限！')

        if request.POST:
            from supply.views import itemin_action
            return_tag = itemin_action(request.POST.get('sku'),1,request.POST.get('depot'),request.user)
            # print u'%s-%s'% (return_tag['msg'],return_tag['success'])

            if return_tag['success']:
                messages.add_message(request, messages.SUCCESS, return_tag['msg'])
            else:
                messages.add_message(request, messages.ERROR, return_tag['msg'])
        return TemplateResponse(request, "ready_itemin_single.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    def purchaseorderitem_check(self, request):
        if not request.user.has_perm('lib.purchaseorderitem_check'):
            raise Http404(
                    '您没有采购对单界面的权限！')

        form = PurchaseOrderItemCheckForm(request.POST)
        data ={}
        if request.method == "POST":
            if 'type' in request.POST and request.POST['type'] and request.POST['type'] == 'do_check':
                from supply.views import checkorder_select
                data = checkorder_select(request)
                # print data
            elif  'type' in request.POST and request.POST['type'] and request.POST['type']=='export_csv':
                response = HttpResponse(content_type='text/csv')
                response.write('\xEF\xBB\xBF')
                response['Content-Disposition'] = 'attachment; filename="export_checkorder.csv"'
                writer = csv.writer(response)
                writer.writerow(["采购单ID","采购产品ID","SKU","数量","生成时间","采购状态","对单状态","供应商","国内物流号","备注","采购人(assigner)","purhcaser","最后更新人",])
                # purchase_item_ids = request.POST.getlist('purchase_item_id')
                # for purchase_item_id in purchase_item_ids:
                #     try:
                #         purchaseOrderItem = PurchaseOrderItem.objects.get(id=purchase_item_id)
                #     except Exception, e:
                #         continue
                #     rowList = []
                #     rowList.append(str(purchaseOrderItem.purchase_order_id))
                #     rowList.append(str(purchaseOrderItem.id))
                #     rowList.append(str(purchaseOrderItem.item.sku))
                #     rowList.append(str(purchaseOrderItem.qty))
                #     rowList.append(str(purchaseOrderItem.purchase_order.created))
                #     rowList.append(purchaseOrderItem.purchase_order.get_status_display())
                #     rowList.append(purchaseOrderItem.get_checked_display())
                #     rowList.append(purchaseOrderItem.purchase_order.supplier.name)
                #     rowList.append(purchaseOrderItem.purchase_order.shipping)
                #     rowList.append("`" + str(purchaseOrderItem.purchase_order.tracking))
                #     rowList.append(purchaseOrderItem.purchase_order.note)
                #     rowList.append(purchaseOrderItem.purchase_order.assigner.username)
                #     if purchaseOrderItem.purchaser:
                #         rowList.append(purchaseOrderItem.purchaser.username)
                #     else:
                #         rowList.append(" ")
                #     rowList.append(str(purchaseOrderItem.updater))
                #     rowList = [item.encode("utf-8") for item in rowList]
                #     writer.writerow(rowList)
                return response
                pass
        elif request.GET.get('type') == 'show_checked':
            from supply.views import checkorder_select
            from django.core.paginator import Paginator
            poi_ids = request.GET.get('poi_ids').split(',')
            data = checkorder_select(request)
            pois = PurchaseOrderItem.objects.filter(id__in=poi_ids)
            paginator = Paginator(pois,len(pois) + 1)

            page_info = paginator.page(1)
            for purchaseorderitem in page_info:
                supplierproduct_sku = SupplierProduct.objects.filter(supplier=purchaseorderitem.purchaseorder.supplier,product=purchaseorderitem.item.product).filter(deleted=False,order=1).first()
                if supplierproduct_sku:
                    purchaseorderitem.supplier_sku = supplierproduct_sku.supplier_sku
                else:
                    purchaseorderitem.supplier_sku = ''

                depotitem = DepotItem.objects.filter(deleted=False,depot=purchaseorderitem.purchaseorder.depot,item=purchaseorderitem.item).first()
                if depotitem:
                    purchaseorderitem.depotitem_id = depotitem.id
                else:
                    purchaseorderitem.depotitem_id = 0

                size_array = purchaseorderitem.item.key.split('-')
                op_size = Option.objects.filter(id=size_array[2],deleted=False).first()
                if op_size:
                    purchaseorderitem.item_size = op_size.name
                else:
                    purchaseorderitem.item_size=''
            data['page_info'] = page_info

        elif request.method == "GET":
            from supply.views import checkorder_select
            data = checkorder_select(request)
            print data

        return TemplateResponse(request, "purchaseorderitem_check.html",{'opts': self.model._meta,'root_path': self.get_urls(),'form':form,'info':data['page_info'],'search_condition':data['search_condition']})


    def purchaseorderitem_error_notice(self, request):
        if not request.user.has_perm('lib.purchaseorderitem_error_notice'):
            raise Http404(
                    '您没有采购异常界面的权限！')

        data_temp = {}
        data_temp["not_weights"] = []
        data_temp["not_locations"] = []
        depot=1
        pois = PurchaseOrderItem.objects.filter(purchaseorder__deleted=False).exclude(action_status=4).exclude(status__in=[0,2]).exclude(purchaseorder__status__in=[0,4]).values('id','purchaseorder_id','item_id','depot_id','item__weight','item__sku').order_by('-id')
        # pois = PurchaseOrderItem.objects.filter(status=0, checked=1).values('id', 'cost_approved', 'item__weight', 'item__location', 'item__sku', 'item__id', 'item__model').order_by('-id')
        for poi in pois:
            if poi['item__weight'] == 0:
                data_temp["not_weights"].append(dict(poi))
            depotitem = DepotItem.objects.filter(depot__code=depot,item__sku=poi['item__sku'],deleted=False).first()
            if not depotitem or not depotitem.position:
                data_temp["not_locations"].append(poi['item__sku'])
        if 'type' in request.POST and request.POST['type'] and request.POST['type']=='export_no_location':
            response = HttpResponse(content_type='text/csv')
            response.write('\xEF\xBB\xBF')
            response['Content-Disposition'] = 'attachment; filename="no_location_sku.csv"'
            writer = csv.writer(response)
            writer.writerow(["sku"])
            for i in data_temp["not_locations"]:
                writer.writerow([i])
            return response

        print data_temp
        return TemplateResponse(request, "purchaseorderitem_error_notice.html",{'opts': self.model._meta,'root_path': self.get_urls(),'not_weights':data_temp['not_weights'],})

    def export_purchaseorderitem(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="purchaseOrderItem.csv"'
        writer = csv.writer(response)
        writer.writerow(["采购单ID","采购单状态","采购条目状态","采购条目ID","sku","颜色","尺码","item数量","对单数量","实际入库数量","未对单数量","采购价","供应商","供应商SKU","备注","采购单生成时间","负责人","采购link","处理状态","处理状态","Model"])
        for query in queryset:
            supplier_product = SupplierProduct.objects.filter(supplier_id=query.purchaseorder.supplier.id,product_id=query.item.product.id).first()
            if not supplier_product:
                supplier_sku = u'不存在供应商sku'
            else:
                supplier_sku = supplier_product.supplier_sku
            if query.purchaseorder.manager:
                first_name = query.purchaseorder.manager.first_name
            else:
                first_name = u''
            not_depotinlog_qty = query.qty - query.real_qty
            size_id = query.item.key.split("-")[2]
            color_id = query.item.key.split("-")[1]
            if color_id:
                product_option_color = Option.objects.filter(id =color_id,deleted=False).first()
                if product_option_color:
                    color = product_option_color.name   
                else:
                    color = ''
            else:
                color = ''
            if size_id:
                product_option = Option.objects.filter(id =size_id,deleted=False).first()
                size = product_option.name
            else:
                size=''
            writer.writerow([
                str(query.purchaseorder.id).encode('utf-8'),
                query.purchaseorder.get_status_display().encode('utf-8'),
                query.get_action_status_display().encode('utf-8'),
                str(query.id).encode('utf-8'),
                str(query.item.sku).encode('utf-8'),
                str(color).encode('utf-8'),
                str(size).encode('utf-8'),
                str(query.qty).encode('utf-8'),
                str(query.real_qty).encode('utf-8'),
                str(query.depotinlog_qty).encode('utf-8'),
                str(not_depotinlog_qty).encode('utf-8'),
                str(query.cost).encode('utf-8'),
                str(query.purchaseorder.supplier.name).encode('utf-8'),
                #供应商sku
                str(supplier_sku).encode('utf-8'),
                str(query.note).encode('utf-8'),
                str(query.created).encode('utf-8'),
                str(first_name).encode('utf-8'),
                str(query.item.product.brief).encode('utf-8'),
                query.get_status_display().encode('utf-8'),
                query.get_in_status_display().encode('utf-8'),
                str(query.item.product.sku).encode('utf-8'),
                # query.comment1.encode('utf-8'),
            ])
        return response
    export_purchaseorderitem.short_description = u"CSV导出采购单货品"

    actions = [export_purchaseorderitem]
admin.site.register(PurchaseOrderItem, PurchaseOrderItemAdmin)


class PurchaseOrderCheckedItemAdmin(NoDeleteActionModelAdmin):
    model = PurchaseOrderCheckedItem
    save_as = True
    save_on_top = True
    list_filter = ('status', PurchaseCheckorderManagerFilter)
    list_display = ('id','purchaseorder','purchaseorderitem', 'qty','depotinlog_qty','status', 'note', 'add_user','created','updated','deleted')
    fields = ['id','purchaseorder','purchaseorderitem', 'qty','depotinlog_qty','status', 'note', 'add_user','created','updated','deleted']
    readonly_fields = ('id','purchaseorder','purchaseorderitem', 'qty','depotinlog_qty','status', 'note', 'add_user','created','updated')
    search_fields = ['purchaseorder__id','purchaseorderitem__id','purchaseorder__supplier__name','purchaseorderitem__item__product__sku', 'purchaseorderitem__item__sku',]

admin.site.register(PurchaseOrderCheckedItem, PurchaseOrderCheckedItemAdmin)


class PurchaseOrderQualityTestingAdmin(NoDeleteActionModelAdmin):
    model = PurchaseOrderQualityTesting
    save_as = True
    save_on_top = True
    list_filter = ('status',PurchaseCheckorderManagerFilter)
    list_display = ('id','purchaseorder','purchaseorderitem', 'status','qty','note', 'add_user', 'created','updated','deleted',)
    fields = ['id','purchaseorder','purchaseorderitem', 'status','qty','note', 'add_user', 'created','updated','deleted']
    readonly_fields = ('id','purchaseorder','purchaseorderitem', 'status','qty','note', 'add_user', 'created','updated','deleted')
    search_fields = ['purchaseorder__id','purchaseorderitem__id','purchaseorder__supplier__name','purchaseorderitem__item__product__sku', 'purchaseorderitem__item__sku',]

admin.site.register(PurchaseOrderQualityTesting, PurchaseOrderQualityTestingAdmin)


class ForSupplierSupplierProductInline(admin.TabularInline):

   # def get_queryset(self, request):
   #    query_set = SupplierProduct.objects.filter(delete=False)
   #    return query_set

    form = ForSupplierAdminForm
    model = SupplierProduct
    fields = ['supplier','supplier_period', 'supplier_cost', 'supplier_min_qty', 'supplier_sku']
    # readonly_fields = ('order',)
    extra = 0
    #max_num = 0
    can_delete = False

    verbose_name = u'供应商产品信息'
    verbose_name_plural = u'供应商产品信息'

class ProductForSupplierAdmin(admin.ModelAdmin):

    form = ProductAdminForm

    def get_queryset(self, request):
        current_user_id = request.user.id
        supplier = Supplier.objects.filter(login_user_id=current_user_id,deleted=False).values_list('id',flat=True)
        sp = SupplierProduct.objects.filter(supplier_id__in=supplier,deleted=False).values_list('product_id',flat=True)
        query_set = Product.objects.filter(deleted=False,id__in=sp)
        return query_set

    def save_related(self, request, form, formsets, change, **kwargs):
        super(ProductForSupplierAdmin, self).save_related(request, form, formsets, change, **kwargs)
        print form.instance.update_items()


    # inlines = [ProductAttributeInline, ItemInline, ProductImageInline, SupplierProductInline, ProductSaleInline, ProductFeedbackInline,]
    inlines = [ForSupplierSupplierProductInline, ProductImageInline,]

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.get_images()
        url = ""
        output = ""
        if images:
            for image in images:
                url = '/media/' + str(image.image)
                output = output + u'<img src="%s" width="100px"/>' % (url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<img src="%s" width="100px"/>' % (url)
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    def sku_view(self, obj):
        # alias = "<br/>".join(obj.alias_set.filter(deleted=False).values_list('sku', flat=True))
        alias = ""
        output =u'%s<br/>%s' % (obj.sku, alias)
        return output

    sku_view.allow_tags = True
    sku_view.short_description = "SKU"

    # date_hierarchy = 'created'#时区
    ordering = ['-id']
    list_filter = ('status', 'category')
    readonly_fields =  ('sku', )
    #filter_horizontal = ['categories',]
    save_as = True
    save_on_top = True
    search_fields = ['name', 'note']
    list_display = ('id', 'sku_view', 'note', 'weight', 'name', 'thumb', 'status', 'category', 'created')
    fields = ['category', 'cn_name', 'description',]
    readonly_fields = ('sku',)
    #list_editable = ('status', 'cost', 'weight')
    # actions = [set_develop_steam_products,set_action_info_products,set_action_take_photo_products,set_action_ps_products,]

    class Media:
        js = ("admin/js/product.js", )

admin.site.register(ProductForSupplier, ProductForSupplierAdmin)


class PurchaseRequestItemInline(admin.TabularInline):

    def thumb(self, obj):
        images = obj.item.product.get_image_thumb()
        output =u'<img src="%s" width="100px"/>' % (images)
        return output
    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    form = PurchaseRequestAdminForm
    model = PurchaseRequestItem
    fields = ['item','thumb', 'qty', 'note','purchaseorderitem','created','updated','deleted']
    readonly_fields = ('thumb','purchaseorderitem','created','updated',)
    can_delete = False
    extra = 0
    #max_num = 0


class PurchaseRequestAdmin(admin.ModelAdmin):

   #def p_link(self,obj):
   #    p=obj.product
   #    link= p.get_admin_url()
   #    str='<a href="%s">' %(link)
   #    str+=p.sku
   #    str+='</a>'

   #    return str
   #p_link.allow_tags = True
   #p_link.short_description = "产品名称"

    def save_model(self, request, obj, form, change):
        if not obj.add_user_id:
            obj.add_user = request.user
        if obj.related_sku_note:
            re_tag = form.instance.related_item()
            obj.related_sku_note = re_tag
        super(PurchaseRequestAdmin, self).save_model(request, obj, form, change)

    form = PurchaseRequestItemAdminForm
    save_as = True
    save_on_top = True
    #search_fields = ['key', 'sku']
    list_display = ('id', 'name','status','add_user','manager','created','updated','deleted' )
    readonly_fields = ('add_user',)
    list_filter = ('status',PurchaseManagerFilter)
    inlines = [PurchaseRequestItemInline, ]
admin.site.register(PurchaseRequest, PurchaseRequestAdmin)

class ItemForSupplierAdmin(admin.ModelAdmin):

    form = ItemAdminForm

    def get_queryset(self, request):
        current_user_id = request.user.id#显示当前登录用户绑定的供应商的产品
        supplier = Supplier.objects.filter(login_user_id=current_user_id,deleted=False).values_list('id',flat=True)
        sp = SupplierProduct.objects.filter(supplier_id__in=supplier,deleted=False).values_list('product_id',flat=True)
        query_set = Item.objects.filter(deleted=False, product_id__in=sp)
        # attribute is inline:1
        return query_set

    def p_link(self,obj):
        p=obj.product
        link= p.get_admin_url()
        str='<a href="%s">' %(link)
        str+=p.sku
        str+='</a>'

        return str
    p_link.allow_tags = True
    p_link.short_description = "产品名称"

    # inlines = [ AliasInline, DepotItemInline, ]
    save_as = True
    save_on_top = True
    search_fields = ['key', 'sku']
    list_display = ('id', 'p_link', 'key', 'cost', 'status', )
    readonly_fields = ('product', 'key', 'sku', 'qty', 'deleted')
    list_filter = ('status',)
admin.site.register(ItemForSupplier, ItemForSupplierAdmin)

class MadeOrderAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    #search_fields = ['key', 'sku']
    list_display = ('id', 'purchaseorder','status','process', 'manager', 'created', 'factory_date', 'check_template_date', 'material_prepare_date','produce_date', 'estimated_date', 'end_date','note' )
    readonly_fields = ('purchaseorder',)
    list_filter = ('status', 'process')
admin.site.register(MadeOrder, MadeOrderAdmin)
