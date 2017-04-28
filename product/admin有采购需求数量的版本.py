# -*- coding: utf-8 -*-
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404,redirect
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from django.core.urlresolvers import reverse
import csv,StringIO
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.conf import settings
#from django.core.mail import send_mail,send_mass_mail
from django.utils.translation import ugettext_lazy as _
from django.contrib.admin import SimpleListFilter
import random

from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin

from dal import autocomplete
from django.db.models import Sum
from datetime import *

from product.models import *
from order.models import *
from django.conf.urls import url, include

import supply
import depot
import order
from lib.admin import NoDeleteActionModelAdmin, NoDeleteActionMPTTModelAdmin
from product.forms import *
from supply.forms import *
from django.contrib import messages
from django.template.response import TemplateResponse,HttpResponse


class ProductAttributeInline(admin.TabularInline):

   #def get_queryset(self, request):
   #    query_set = ProductAttribute.objects.filter(deleted=False)
   #    return query_set

    form = ProductAttributeAdminForm
    model = ProductAttribute

    fields = ['attribute', 'options',]
    readonly_fields =  ('attribute',)
    extra = 0
    max_num = 0
    can_delete = False


class ProductActionInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = ProductAction.objects.filter(deleted=False)
        return query_set

    form = ProductRequestAdminForm
    model = ProductAction

    # fields = ['attribute', 'options',]
    readonly_fields =  ('add_user',)
    extra = 0
    # max_num = 0
    can_delete = False


class SupplierProductInline(admin.TabularInline):

   #def get_queryset(self, request):
   #    query_set = supply.objects.Supply.objects.filter(delete=False)
   #    return query_set

    form = supply.forms.SupplierAdminForm
    model = supply.models.SupplierProduct
    #fields = ['qty', 'status', ]
    #readonly_fields =  ('sku',)
    extra = 0
    #max_num = 0
    can_delete = False

class ItemInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = Item.objects.filter(deleted=False)
        # attribute is inline:1
        return query_set


    def main_field(self, obj):
        if obj:
            try:
                label = " ".join([ Option.objects.get(id=int(option_id)).name for option_id in obj.key.split('-')[1:]])
            except:
                label = ""
            output = label
            output = output + u' <a href="%s" target="_blank">详情</a>' % obj.get_admin_url()
        else:
            output = u''
        return output

    main_field.allow_tags = True
    main_field.short_description = u"名称"

    def depot_qty(self,obj):
        output=""
        if obj:
            result=obj.depotitem_set.filter(deleted=False)
            if result:
                ditems={}
                for ditem in result:
                    iname= ditem.depot.name
                    iqty= int(ditem.qty)
                    if iname in ditems:
                        ditems[iname]+=iqty
                    else:
                        ditems[iname]=iqty
                output+='<table>'
                for (k,v) in ditems.items():
                    output+='<tr>'
                    output+='<td>'+k+'</td>'
                    output+='<td>'+str(v)+'</td>'
                    output+='</tr>'
                output+='</table>'
                # print output
        return output


    depot_qty.allow_tags = True
    depot_qty.short_description = u"采购库存量"

    def depot_qty_locked(self,obj):
        output=""
        if obj:
            result=obj.depotitem_set.filter(deleted=False)
            if result:
                ditems={}
                for ditem in result:
                    iname= ditem.depot.name
                    iqty= int(ditem.qty_locked)
                    if iname in ditems:
                        ditems[iname]+=iqty
                    else:
                        ditems[iname]=iqty
                output+='<table>'
                for (k,v) in ditems.items():
                    output+='<tr>'
                    output+='<td>'+k+'</td>'
                    output+='<td>'+str(v)+'</td>'
                    output+='</tr>'
                output+='</table>'
                # print output
        return output


    depot_qty_locked.allow_tags = True
    depot_qty_locked.short_description = u"占用库存量"

    def picked_qty(self,obj):
        output=""
        if obj:
            result=obj.pickitem_set.filter(deleted=False).aggregate(Sum('qty'))
            print result
            # if result:
            #     ditems={}
            #     for ditem in result:
            #         iname= ditem.depot.name
            #         iqty= int(ditem.qty_locked)
            #         if iname in ditems:
            #             ditems[iname]+=iqty
            #         else:
            #             ditems[iname]=iqty
            #     output+='<table>'
            #     for (k,v) in ditems.items():
            #         output+='<tr>'
            #         output+='<td>'+k+'</td>'
            #         output+='<td>'+str(v)+'</td>'
            #         output+='</tr>'
            #     output+='</table>'
            #     # print output
        return output


    picked_qty.allow_tags = True
    picked_qty.short_description = u"拣货量"

    def sale_qty(self,obj):
        output=""
        if obj:
            fromtime=datetime.datetime.now()-datetime.timedelta(days=3)
            # print fromtime
            result=obj.orderitem_set.filter(created__gt=fromtime).filter(deleted=False).filter(order__status=3).aggregate(Sum('qty'))
            # print result
            if not result.qty__sum:
                output=result.qty__sum
            # print result.qty__sum
        return output


    sale_qty.allow_tags = True
    sale_qty.short_description = u"近期销售量"

    model = Item
    fields = ['main_field', 'cost', 'weight', 'status', 'depot_qty', 'depot_qty_locked', 'picked_qty', 'sale_qty']
    readonly_fields =  ('main_field', 'sku', 'depot_qty', 'depot_qty_locked', 'picked_qty', 'sale_qty')
    extra = 0
    max_num = 0
    can_delete = False

class ProductImageInline(admin.TabularInline):
    #ordering = ['order']
    model = ProductImage

    def thumb(self, obj):
        if obj.image:
            output =u'<img src="%s%s" width="100px"/>' % (settings.STATIC_URL, obj.image)
        else:
            url = "http://placehold.it/100x100"
            output =u'<img src="%s" width="100px"/>' % (url)
        return output

    thumb.allow_tags = True
    thumb.short_description = u"预览图"


    extra = 0
    fields = ('thumb', 'image',)
    readonly_fields =  ('thumb',)
    can_delete = False
   #max_num = 0
   #can_delete = False
   #filter_horizontal = [ 'options']
   ##filter_horizontal = [ 'options']
   ##fields = ['attribute', 'options', ]

class ProductSaleInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = ProductSale.objects.filter(deleted=False)
        return query_set

    # form = ProductAttributeAdminForm
    model = ProductSale

    fields = ['channel', 'status', 'note' ,'created']
    readonly_fields =  ('created',)
    extra = 0
    #max_num = 0
    can_delete = False

class ProductFeedbackInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = ProductFeedback.objects.filter(deleted=False)
        return query_set

    model = ProductFeedback

    fields = ['type', 'add_user', 'note', 'created']
    readonly_fields = ('created','add_user')
    extra = 0
    #max_num = 0
    can_delete = False


class ProductRequestInline(admin.TabularInline):

    # form = ProductRequestNameAdminForm
    model = ProductRequest.products.through

    # def get_queryset(self, request):
    #     query_set = ProductRequest.products.objects.order_by('-productrequest')
    #     return query_set

    def show_status(self, obj):

        print obj.productrequest_id
        pr = ProductRequest.objects.get(pk=obj.productrequest_id)
        output = u'%s--%s' %(pr.get_status_display(),pr.active_time)
        return output

    show_status.allow_tags = True
    show_status.short_description = u"组货方案状态——有效时间"

    fields = ['id','productrequest','show_status']
    readonly_fields = ('id', 'show_status')
    extra = 0
    # max_num = 0
    can_delete = False
    verbose_name = u" 产品组货方案"
    verbose_name_plural = u"产品组货方案"


def update_related_products(modeladmin, request, queryset):
    for product in queryset:
        products = Product.objects.filter(visibility=1, status=1, category=product.category).exclude(id=product.id).filter(model=product.model)
        random_products = random.sample(products, 6)
        product.related_products.clear()
        for random_product in random_products:
            product.related_products.add(random_product)
update_related_products.short_description = "update related products"


def set_develop_steam_products(modeladmin, request, queryset):

    if 'do_action' in request.POST:
        form = ProductActionForm(request.POST)
        if form.is_valid():
            productaction = form.cleaned_data['productaction']
            add_uesr = request.user
            for paction in productaction:
                for pd in queryset:
                    ProductAction.objects.get_or_create(product=pd,type=paction,status=0,manager=pd.category.manager,add_user=add_uesr)

            messages.success(request, '选择的操作动作执行成功')
            return redirect('/admin/product/productaction/?status__exact=0')
    else:
        form = ProductActionForm()

        return TemplateResponse(request, 'set_develop_steam_products.html',
            {'title': u'选择需要操作的动作',
             'objects': queryset,
             'form':form,
             'action':'set_develop_steam_products'})

set_develop_steam_products.short_description = u"选中状态的产品批量新增产品任务"

#
# def set_action_info_products(modeladmin, request, queryset):
#
#     user=User.objects.filter(id=request.user.id).first()
#
#     for product in queryset:
#         if product.status==2:
#             manager= product.category.manager
#             ProductAction.objects.get_or_create(product=product,type=0,status=0,manager=manager,add_user=user)
#         else:
#             messages.add_message(request, messages.ERROR, u'%s新增任务失败' %product.sku)
#
# set_action_info_products.short_description = u"选中状态产品批量添加资料编辑任务"
#
#
# def set_action_take_photo_products(modeladmin, request, queryset):
#
#     user=User.objects.filter(id=request.user.id).first()
#
#     for product in queryset:
#         if product.status==2:
#             manager= product.category.manager
#             ProductAction.objects.get_or_create(product=product,type=1,status=0,manager=manager,add_user=user)
#         else:
#             messages.add_message(request, messages.ERROR, u'%s新增任务失败' %product.sku)
#
# set_action_take_photo_products.short_description = u"选中状态产品批量添加拍照任务"
#
#
# def set_action_ps_products(modeladmin, request, queryset):
#
#     user=User.objects.filter(id=request.user.id).first()
#
#     for product in queryset:
#         if product.status==2:
#             manager= product.category.manager
#             ProductAction.objects.get_or_create(product=product,type=2,status=0,manager=manager,add_user=user)
#         else:
#             messages.add_message(request, messages.ERROR, u'%s新增任务失败' %product.sku)
#
# set_action_ps_products.short_description = u"选中状态产品批量添加修图任务"


#class ProductAdmin(NoDeleteActionModelAdmin):
class ProductAdmin(admin.ModelAdmin):

    form = ProductAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.adder_id:
            obj.adder = request.user
        #obj.updater = request.user
        super(ProductAdmin, self).save_model(request, obj, form, change)


    def save_related(self, request, form, formsets, change, **kwargs):
        super(ProductAdmin, self).save_related(request, form, formsets, change, **kwargs)
        print form.instance.update_items()

    inlines = [ProductAttributeInline, ItemInline, ProductImageInline, SupplierProductInline, ProductSaleInline, ProductFeedbackInline,ProductRequestInline,ProductActionInline]

    def save_formset(self, request, form, formset, change):

        if formset.model != ProductFeedback and formset.model != ProductAction:
            return super(ProductAdmin, self).save_formset(request, form, formset, change)
        instances = formset.save(commit=False)

        for instance in instances:
            if not instance.pk:
                instance.add_user = request.user
            instance.save()
        formset.save_m2m()

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.get_images()
        url = ""
        output = ""
        if images:
            for image in images:
                url = '/static/' + str(image.image)
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
    sku_view.short_description = "model"

    # date_hierarchy = 'created'#时区
    ordering = ['-id']
    list_filter = ('status', 'category')
    #filter_horizontal = ['categories',]
    save_as = True
    save_on_top = True
    search_fields = ['sku', 'name', 'note',]
    list_display = ('id', 'sku_view', 'cost', 'note', 'weight', 'name', 'thumb', 'status', 'category','adder', 'created')
    readonly_fields =  ('sku','adder', 'color', 'size')
    #list_editable = ('status', 'cost', 'weight')
    actions = [set_develop_steam_products]

    class Media:
        js = ("admin/js/product.js", )


    def get_urls(self):
        urls = super(ProductAdmin, self).get_urls()
        my_urls = [
            url(r'^import_buyer_product/$', self.import_buyer_product),
        ]
        return my_urls + urls

    def import_buyer_product(self, request):
        if not request.user.has_perm('lib.import_buyer_product'):
            raise Http404(
                    '您没有批量导入产品界面的权限！')

        if request.POST:
            data_error = ''
            data ={}
            if not request.FILES:
                data_error = u'请选择文件后再提交'
            else:
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)

                headers = next(reader)#去掉首行

                std_header = ['\xef\xbb\xbf产品分类','产品中文名称','颜色','尺码','产品净重','尺码描述','材质','供应商ID','供应商名称','供应商货号','择尚拿货价','供应商提供的参考库存','快递费用','[备注]','[是否有弹性(0:否,1:是)]','[拉链(0:无,1:前拉链,2:侧,3后)]','[是否透明(0:否,1:是)]','[配件说明]']
                field_header = ['category','cn_name','color','size','weight','description','material','supplier_ID','supplier_name','supplier_sku','supplier_cost','supplier_inventory','shipping_fee','note','note1','note2','note3','note4',]

                # for i in range(1,18):
                #     # print i
                #     if std_header[i] != headers[i]:
                #         data_error +=u',%s表格与范本不一致,可能是没有另外为utf-8'
                if headers != std_header:
                    data_error +=u"表格与范本不一致,可能是没有另外为utf-8\n"
                print headers,'____________________'
                print std_header
                j = 0
                for row in reader:
                    j +=1
                    row = [i.strip() for i in row]
                    res = dict(zip(field_header, row))
                    for key in res.keys():

                        if key in ['weight','supplier_ID','supplier_cost','supplier_inventory','shipping_fee']:
                            # print key
                            res[key] = res[key] or 0
                        if key=='size':
                            res['size'] = res['size'].upper()
                        if key in ['category','color']:
                            res[key] = res[key].capitalize()
                    #验证供应商id
                    supplier = Supplier.objects.filter(deleted=False,id=res['supplier_ID']).first()
                    if not supplier:
                        data_error +=u'第%d行的%s供应商id系统不存在'% (j+1,res['supplier_ID'])
                    #验证分类和属性
                    cate = Category.objects.get(deleted=False,name=res['category'])
                    try:
                        if res['color']:
                            # attr = cate.attributes.filter(attribute_id=11).values_list('attribute_id', flat=True)
                            option = Option.objects.filter(deleted=False,attribute_id=11,name=res['color']).first()
                            if not option:
                                data_error +=u'第%d行的%s颜色系统不存在'% (j+1,res['color'])

                        if res['size']:
                            diff_size = []
                            table_size = list(set(res['size'].split('#')))
                            attr = cate.attributes.filter(id=cate.id).values_list('id', flat=True)

                            option2 = Option.objects.filter(deleted=False,attribute_id__in=attr).values_list('name', flat=True)
                            diff_size = list(set(table_size).difference(set(option2)))
                            diff_size_str = ','.join(diff_size)
                            if diff_size:
                                data_error +=u'第%d行的%s尺码系统不存在'% (j+1,diff_size_str)
                    except Category.DoesNotExist:
                        data_error +=u'第%d行的%s产品分类名称系统不存在'% (j+1,res['category'])
                    data[j] = res


                #验证结束
            if data_error:
                messages.add_message(request, messages.ERROR, data_error)
            else:
                # print data
                # 插入数据
                add_user_id = request.user.id
                for table_p in data:
                    category = Category.objects.get(deleted=False,name=data[table_p]['category'])
                    note_str = '[备注]=='+data[table_p]['note']+'\n[是否有弹性(0:否,1:是)]==      '+data[table_p]['note1']+'\n[拉链(0:无,1:前拉链,2:侧,3后)]==      '+data[table_p]['note2']+'\n[是否透明(0:否,1:是)]==      '+data[table_p]['note3']+'\n[配件说明]==      '+data[table_p]['note4']
                    p = Product.objects.create(category_id=category.id,cn_name=data[table_p]['cn_name'],cost=data[table_p]['supplier_cost'],manager_id=category.manager_id,material=data[table_p]['material'],description=data[table_p]['description'],note=note_str,weight=data[table_p]['weight'],adder_id=add_user_id)
                    #新增供应商产品
                    supplier = Supplier.objects.get(deleted=False,id=data[table_p]['supplier_ID'])
                    SupplierProduct.objects.create(supplier=supplier,product=p,supplier_cost=data[table_p]['supplier_cost'],supplier_sku=data[table_p]['supplier_sku'],supplier_inventory=data[table_p]['supplier_inventory'],supplier_shipping_fee=data[table_p]['shipping_fee'])

                    sizes = data[table_p]['size'].split('#')
                    for attribute in category.attributes.filter(deleted=False).order_by('-sort'):
                        product_attribute, is_created = ProductAttribute.objects.get_or_create(attribute_id=attribute.id,product_id=p.id)
                        if product_attribute.attribute_id==11:
                            if data[table_p]['color']:
                                option_color = Option.objects.get(name=data[table_p]['color'],attribute_id=product_attribute.attribute_id)
                                product_attribute.options.add(option_color)
                                if not data[table_p]['size']:#尺码为空的item
                                    item_str = str(p.id) +str(option_color.id)
                                    item_sku = u"%s-%s"% (p.sku,option_color.name)
                                    item, is_created = Item.objects.get_or_create(product_id=p.id, key=item_str,sku=item_sku)
                        else:
                            for op in sizes:
                                option = Option.objects.get(name=op,attribute_id=product_attribute.attribute_id)
                                product_attribute.options.add(option)
                                if data[table_p]['color']:#颜色不为空的item
                                    item_str = str(p.id) +'-'+str(option_color.id)+'-'+str(option.id)
                                    item_sku = u"%s-%s-%s"% (p.sku,option_color.name,option.name)
                                else:#颜色为空的item
                                    item_str = str(p.id)+'-0-'+str(option.id)
                                    item_sku = u"%s-0-%s"% (p.sku,option.name)

                                item, is_created = Item.objects.get_or_create(product_id=p.id, key=item_str,sku=item_sku)
                    #如果尺码和颜色都不存在
                    if not data[table_p]['color'] and not data[table_p]['size']:
                        item_str = str(p.id)+'-'
                        item_sku = u"%s-"%p.sku
                        item, is_created = Item.objects.get_or_create(product_id=p.id, key=item_str,sku=item_sku)

                    # print data[table_p]
                messages.add_message(request, messages.SUCCESS, u'%s表格中的产品已全部上传：%d'% (filename,j))

        return TemplateResponse(request, "import_buyer_product.html",{'opts': self.model._meta,'root_path': self.get_urls(),})



admin.site.register(Product, ProductAdmin)

# class ProductForSaleAdmin(admin.ModelAdmin):
#     form = ProductAdminForm
#
#     def save_related(self, request, form, formsets, change, **kwargs):
#         super(ProductForSaleAdmin, self).save_related(request, form, formsets, change, **kwargs)
#         print form.instance.update_items()
#
#     inlines = [ProductAttributeInline, ItemInline, ProductImageInline, SupplierProductInline, ProductSaleInline, ProductFeedbackInline,]
#
#     def save_formset(self, request, form, formset, change):
#
#         if formset.model != ProductFeedback:
#             return super(ProductForSaleAdmin, self).save_formset(request, form, formset, change)
#         instances = formset.save(commit=False)
#
#         for instance in instances:
#             if not instance.pk:
#                 instance.add_user = request.user
#             instance.save()
#         formset.save_m2m()
#
#     def thumb(self, obj):
#         #output =u'<img src="%s"/>' % (obj.get_simage())
#         images = obj.get_images()
#         url = ""
#         output = ""
#         if images:
#             for image in images:
#                 url = '/static/' + str(image.image)
#                 output = output + u'<img src="%s" width="100px"/>' % (url)
#                 break
#         else:
#             url = "http://placehold.it/100x100"
#             output =u'<img src="%s" width="100px"/>' % (url)
#         return output
#
#     thumb.allow_tags = True
#     thumb.short_description = u"缩略图"
#
#     def sku_view(self, obj):
#         # alias = "<br/>".join(obj.alias_set.filter(deleted=False).values_list('sku', flat=True))
#         alias = ""
#         output =u'%s<br/>%s' % (obj.sku, alias)
#         return output
#
#     sku_view.allow_tags = True
#     sku_view.short_description = "SKU"
#
#     # date_hierarchy = 'created'#时区
#     ordering = ['-id']
#     list_filter = ('status', 'category')
#     readonly_fields = ('sku', )
#     #filter_horizontal = ['categories',]
#     save_as = True
#     save_on_top = True
#     search_fields = ['name', 'note']
#     list_display = ('id', 'sku_view', 'cost', 'note', 'weight', 'name', 'thumb', 'status', 'category', 'created')
#     readonly_fields = ('sku',)
#     #list_editable = ('status', 'cost', 'weight')
#     actions = [set_develop_steam_products,set_action_info_products,set_action_take_photo_products,set_action_ps_products,]
#
#     class Media:
#         js = ("admin/js/product.js", )
#
# admin.site.register(ProductForSale, ProductForSaleAdmin)


#class CategoryAdmin(NoDeleteActionMPTTModelAdmin):
class CategoryAdmin(MPTTModelAdmin):

    form = CategoryAllAdminForm

    def product_count(self, obj):
        output = str(Product.objects.filter(category=obj,deleted=False).filter(deleted=False).count())
        return output

    product_count.allow_tags = True
    product_count.short_description = u"产品数目"
    def category_product_list(self, obj):
        if obj.id:

            attributes = obj.attributes.all()
            attributes_view = '/'.join([attribute.name for attribute in attributes])
            output =u'<a href="/admin/product/product/?category=%s" target="_blank">产品列表</a>' % (obj.id)
            output = output + '<br/>' + attributes_view
        else:
            output =u''
        return output

    category_product_list.allow_tags = True
    category_product_list.short_description = u"分类产品列表"

    save_as = True
    save_on_top = True
    search_fields = ['name']
    #ordering = ['id']
    filter_horizontal = ['attributes',]
    list_editable = ('cn_name',)
    list_display = ('id', 'name', 'cn_name', 'color', 'size', 'parent', 'level', 'product_count', 'manager', 'code','category_product_list')
    #exclude = ['products']
admin.site.register(Category, CategoryAdmin)

class OptionInline(admin.TabularInline):
    model = Option
    can_delete = False

class AttributeAdmin(NoDeleteActionModelAdmin):

    inlines = [OptionInline, ]
    save_as = True
    save_on_top = True
    #search_fields = ['key', 'currency']
    list_display = ('id', 'name', )
admin.site.register(Attribute, AttributeAdmin)

class OptionAdmin(NoDeleteActionModelAdmin):

    #inlines = [OptionInline, ]
    save_as = True
    save_on_top = True
    #search_fields = ['key', 'currency']
    list_editable = ('code', 'note')
    list_filter = ('attribute', )
    list_display = ('id', 'name', 'code', 'note', 'attribute')
admin.site.register(Option, OptionAdmin)

class AliasInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = order.models.Alias.objects.filter(deleted=False)
        return query_set

    model = order.models.Alias

    fields = ['sku', 'channel']
    #readonly_fields =  ('attribute',)
    extra = 0
    #max_num = 0
    #can_delete = False


class DepotItemInline(admin.TabularInline):

    def get_queryset(self, request):
        query_set = depot.models.DepotItem.objects.filter(deleted=0)
        return query_set

    model = depot.models.DepotItem

    fields = ['qty', 'qty_locked', 'depot', 'position']
    readonly_fields = ('qty', 'qty_locked', 'depot')
    extra = 0
    max_num = 0
    can_delete = False



class ItemAdmin(NoDeleteActionModelAdmin):

    form = ItemAdminForm

    def get_queryset(self, request):
        query_set = Item.objects.filter(status=True,deleted=False)
        # attribute is inline:1
        return query_set

    def p_link(self,obj):
        p=obj.product
        link = p.get_admin_url()
        # str = u' %s ' %p.__unicode__
        str = u'%s<br><a href="%s">产品详情</a>' % (p.__unicode__(),link)
        return str
    p_link.allow_tags = True
    p_link.short_description = "产品名称"

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.product.get_images()
        url = ""
        output = ""
        if images:
            for image in images:
                url = '/static/' + str(image.image)
                output = output + u'<img src="%s" width="100px"/>' % (url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<img src="%s" width="100px"/>' % (url)
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    def needpurchase_qty(self, obj):
        # depot_all = depot.models.Depot.objects.all()

        # for idepot in depot_all:
        depot_qty_gz = depot.models.DepotItem.objects.filter(item_id=obj.id,depot_id=1).aggregate(models.Sum('qty'),models.Sum('qty_locked'))
        depot_qty_nj = depot.models.DepotItem.objects.filter(item_id=obj.id,depot_id=2).aggregate(models.Sum('qty'),models.Sum('qty_locked'))

        purchaseorder_qty_gz =  PurchaseOrderItem.objects.filter(status=1).filter(depot_id=1).filter(item_id=obj.id).filter(purchaseorder__status__in = [0,1]).aggregate(models.Sum('qty'))
        purchaseorder_qty_nj =  PurchaseOrderItem.objects.filter(status=1).filter(depot_id=2).filter(item_id=obj.id).filter(purchaseorder__status__in = [0,1]).aggregate(models.Sum('qty'))

        purchaseorder_real_qty = PurchaseOrderItem.objects.filter(status=3).filter(item_id = obj.id).filter(purchaseorder__status__in = [0,1]).aggregate(models.Sum('real_qty')) 

        return u'广州默认仓库: %s / %s / %s / %s<br>南京默认仓库: %s / %s / %s / %s' % (depot_qty_gz.get('qty__sum') or 0,depot_qty_gz.get('qty_locked__sum') or 0, purchaseorder_qty_gz.get('qty__sum') or 0,purchaseorder_real_qty.get('qty__sum') or 0,depot_qty_nj.get('qty__sum') or 0,depot_qty_nj.get('qty_locked__sum') or 0, purchaseorder_qty_nj.get('qty__sum') or 0,1)
    needpurchase_qty.allow_tags = True
    needpurchase_qty.short_description = u"在库数量/锁库数量/采购中数量/采购需求数量"

    inlines = [ AliasInline, DepotItemInline, ]
    save_as = True
    save_on_top = True
    search_fields = ['key', 'sku']
    list_display = ('id', 'p_link', 'needpurchase_qty','sku','thumb','key', 'cost', 'status', )
    readonly_fields = ('product', 'key', 'sku', 'qty', 'deleted')
    list_filter = ('status',)
admin.site.register(Item, ItemAdmin)


class ProductManagerFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'manager'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_assigner', '(None)'])
        # assigner_ids = ProductAction.objects.values_list("manager_id").distinct()
        # users = User.objects.filter(id__in=assigner_ids).order_by('username')
        users = User.objects.filter(groups__name='[产品组]').filter(is_staff=1).order_by('username')
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


class ProductRequestProductInline(admin.TabularInline):

    form = ProductRequestProductAdminForm
    model = ProductRequest.products.through

    def show_extra_filed(self,obj):

        p = Product.objects.get(pk=obj.product_id)
        images = ProductImage.objects.filter(product_id=obj.product_id).order_by('-id').all()
        if images:
            for image in images:
                url = '/static/' + str(image.image)
        else:
            url = "http://placehold.it/100x100"
        str_image = u'%s <br/> <img src="%s" width="100px"/><a href="%s" target="_blank">产品详情</a>' % (p.name,url,obj.product.get_admin_url())
        return str_image
    show_extra_filed.allow_tags = True
    show_extra_filed.short_description = "产品中文名称、图片、产品详情"

    fields = ['product','show_extra_filed',]
    readonly_fields = ('show_extra_filed',)
    extra = 0
    # max_num = 0
    verbose_name = u"组货方案已绑产品"
    verbose_name_plural = u"组货方案已绑产品"

class ProductRequestImageInline(admin.TabularInline):

    model = ProductRequestImage

    extra = 0
    verbose_name = u" 图片"
    verbose_name_plural = u"图片"

class ProductRequestAdmin(NoDeleteActionModelAdmin):

    #def get_queryset(self, request):
       #query_set = ProductRequest.objects.filter(deleted=False)
       #return query_set

    form = ProductRequestAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.add_user_id:
            obj.add_user = request.user
        if obj.related_sku_note:
            re_tag = form.instance.related_product()
            obj.related_sku_note = re_tag
            # if re_tag:
            #     print re_tag
            #     messages.add_message(request, messages.ERROR,u'组货方案绑定产品失败的产品是：%s'% re_tag)
        super(ProductRequestAdmin, self).save_model(request, obj, form, change)

    def delete_model(self, request, obj):
        obj.deleted = True
        obj.save()

    inlines = [ProductRequestProductInline, ProductRequestImageInline, ]
    date_hierarchy = 'created'
    save_as = True
    save_on_top = True
    #search_fields = ['key', 'sku']
    readonly_fields = ('add_user', 'deleted', 'products')
    list_display = ('id', 'name', 'manager', 'add_user', 'status', 'created',)
    list_filter = ('status',ProductManagerFilter)
    search_fields = ('name',)
admin.site.register(ProductRequest, ProductRequestAdmin)


def set_develop_undo_products(modeladmin, request, queryset):
    for pd in queryset:
        pd.status=0
        pd.save()

set_develop_undo_products.short_description = u'设置未处理'

def set_develop_start_products(modeladmin, request, queryset):

        if 'do_action' in request.POST:
            form = ProductActionUserForm(request.POST)
            if form.is_valid():
                manager_id = form.cleaned_data['manager']
                # updated = queryset.update(manager_id=manager_id)
                for pd in queryset:
                    pd.status = 1
                    pd.manager_id = manager_id
                    pd.save()
                messages.success(request, '选中产品已设置开始处理，并分配给对应的负责人')
                return
        else:
            form = ProductActionUserForm()

        return TemplateResponse(request, 'action_set_develop_start_products.html',
            {'title': u'选择当前产品任务的执行人/负责人',
             'objects': queryset,
             'form': form})

set_develop_start_products.short_description = u'设置开始处理'

def set_develop_finish_products(modeladmin, request, queryset):
    for pd in queryset:
        pd.status=2
        pd.save()

set_develop_finish_products.short_description = u'设置处理完成'

def set_develop_del_products(modeladmin, request, queryset):
    for pd in queryset:
        pd.status=3
        pd.save()

set_develop_del_products.short_description = u'设置废除'


class ProductActionAdmin(NoDeleteActionModelAdmin):

    form = ProductFeedbackAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.add_user_id:
            obj.add_user = request.user
        super(ProductActionAdmin, self).save_model(request, obj, form, change)

    def p_link(self,obj):
        p=obj.product
        link= p.get_admin_url()
        # str = u'%s'% p.__unicode__()
        str = u'%s<br><a href="%s">产品详情</a>' % (p.__unicode__(),link)
        # str+='</a>'

        return str
    p_link.allow_tags = True
    p_link.short_description = "产品名称"

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.product.get_images()
        url = ""
        output = ""
        if images:
            for image in images:
                url = '/static/' + str(image.image)
                output = output + u'<img src="%s" width="100px"/>' % (url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<img src="%s" width="100px"/>' % (url)
        return output

    thumb.allow_tags = True
    thumb.short_description = "Image"



    ordering = ['status','-id']
    list_filter = ('type',)
    #filter_horizontal = ['categories',]
    save_as = True
    save_on_top = True
    list_display = ('id', 'p_link', 'thumb', 'type', 'status', 'manager' , 'created')
    #list_editable = ('status', 'cost', 'weight')
    readonly_fields =  ('add_user', )
    list_filter = ('type','status',ProductManagerFilter)
    search_fields = ('name','sku')
    actions = [set_develop_undo_products,set_develop_start_products,set_develop_finish_products,set_develop_del_products,]

    # class Media:
    #     js = ("admin/js/tiny_mce/tiny_mce.js", "admin/js/textareas.js",)

    # inlines = [ItemInline, ProductImageInline, SupplierProductInline, ]
    #actions = [make_products_visiable, update_related_products, make_products_invisiable]
admin.site.register(ProductAction, ProductActionAdmin)

class ProductFeedbackAdmin(NoDeleteActionModelAdmin):

    form = ProductFeedbackAdminForm

    def save_model(self, request, obj, form, change):
        if not obj.add_user_id:
            obj.add_user = request.user
        super(ProductFeedbackAdmin, self).save_model(request, obj, form, change)

    def p_link(self,obj):
        p=obj.product
        link= p.get_admin_url()
        # str='<a href="%s">' %(link)
        # str+=p.__unicode__()
        # str+='</a>'
        str = u'%s<br><a href="%s">产品详情</a>' % (p.__unicode__(),link)
        return str
    p_link.allow_tags = True
    p_link.short_description = "产品名称"



    #form = ProductAdminForm
    ordering = ['type','-id']
    list_filter = ('type',)
    #filter_horizontal = ['categories',]
    save_as = True
    save_on_top = True
    # search_fields = ['sku', 'name', 'note']
    list_display = ('id','p_link', 'type', 'add_user',  'created')
    #list_editable = ('status', 'cost', 'weight')
    readonly_fields = ('add_user',)
    #formfield_overrides = {models.TextField: {'widget': RichTextEditorWidget},}
    # actions = [set_develop_undo_products,set_develop_start_products,set_develop_finish_products,set_develop_del_products,]

    class Media:
        js = ("admin/js/tiny_mce/tiny_mce.js", "admin/js/textareas.js",)

    # inlines = [ItemInline, ProductImageInline, SupplierProductInline, ]
admin.site.register(ProductFeedback, ProductFeedbackAdmin)
