# -*- coding: utf-8 -*-
from django.contrib import admin
from mptt.admin import MPTTModelAdmin
from django import forms
from datetime import datetime
from django.shortcuts import render_to_response, get_object_or_404,redirect
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
from django.contrib.auth.admin import UserAdmin
from django.core.urlresolvers import reverse
import StringIO,csv
from dal import autocomplete
from lib.admin import NoDeleteActionModelAdmin, NoDeleteActionMPTTModelAdmin
from order.export_invoice import export_order_invoice

from order.models import *
import depot as _depot
import shipping as _shipping
import product as _product
from depot.forms import DepotAdminForm
from product.forms import ItemAdminForm
from order.forms import *
from django.contrib import messages
from django.template.response import TemplateResponse,HttpResponse
from django.conf.urls import url, include
from django.contrib.admin import SimpleListFilter


class OrderManagerFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'manager'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_assigner', '(None)'])
        # assigner_ids = ProductAction.objects.values_list("manager_id").distinct()
        # users = User.objects.filter(id__in=assigner_ids).order_by('username')
        users = User.objects.filter(groups__name='[渠道销售组]').filter(is_staff=1).order_by('username')
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


class OrderItemInline(admin.TabularInline):
    form = ItemAdminForm
    model = OrderItem
    extra = 0
    can_delete = False

class PackageInline(admin.TabularInline):
    model = _shipping.models.Package
    extra = 0

   #def get_queryset(self, request):
   #    query_set = _shipping.models.Package.objects.filter(deleted=False)
   #    return query_set

    def main_field(self, obj):
        output = u'<a href="%s">详情</a>' % obj.get_admin_url()
        return output

    main_field.allow_tags = True
    main_field.short_description = "包裹"

    fields = ['status', 'main_field', 'shipping', 'note', ]
    readonly_fields =  ('main_field',)
    can_delete = False

class OrderAdmin(NoDeleteActionModelAdmin):

    def update_status_to_3(modeladmin, request, queryset):
        for query in queryset:
            if query.status==1:
                query.status = 3
                query.save()

    update_status_to_3.short_description = '订单单人工审核通过，状态修改成开始处理'

    def save_model(self, request, obj, form, change):
        super(OrderAdmin, self).save_model(request, obj, form, change)
        obj.update_package_address()

    def make_order_ready(modeladmin, request, queryset):
        # queryset.filter(status=0).update(status=1)
        pass
    make_order_ready.short_description = u"准备发货"

    def export_order(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="orders.csv"'
        writer = csv.writer(response)
        writer.writerow(["Id","Status","Ordernum","Email","Amount","Currency",
        "Payment","Note","Active","Shop","Order from","Shipping Country","Create Time","Assigner","Admin","Comment",])
        for query in queryset:
            writer.writerow([
                str(query.id).encode('utf-8'),
                query.get_status_display().encode('utf-8'),
                str(query.ordernum).encode('utf-8'),
                str(query.email).encode('utf-8'),
                str(query.amount).encode('utf-8'),
                str(query.currency).encode('utf-8'),
                str(query.payment).encode('utf-8'),
                query.note.encode('utf-8'),
                '',
                # query.get_active_display().encode('utf-8'),
                str(query.channel).encode('utf-8'),
                str(query.channel_ordernum).encode('utf-8'),
                str(query.shipping_country).encode('utf-8'),
                str(query.create_time).encode('utf-8'),
                str(query.manager).encode('utf-8'),
                str(query.add_user).encode('utf-8'),
                query.comment.encode('utf-8'),
            ])
        return response
    export_order.short_description = u"CSV导出订单"

    export_order_invoice.short_description = u"导出订单发票信息"

    ordering = ['-id']
    #actions = [purchase_products, purchase_orders]

    class Media:
        js = ("admin/js/order.js",)

    def status_view(self, obj):
        colors = {0:'white', 1:'yellow', 2:'purple', 3:'red', 4:'green', 5:'blue', 6:'black', 7:'pink', 8:'orange'}
        color = colors.get(obj.status,'white')
        output =u'<span style="background-color:%s">%s</span>' % (color, obj.id)
        return output
        #return u'%s%s' % (color, obj.site, obj.id)
    status_view.allow_tags = True
    status_view.short_description = "status"

    list_filter = ('status', 'channel__name')
    date_hierarchy = 'created'
    save_as = True
    save_on_top = True
    search_fields = ['id', 'ordernum', 'email', 'shipping_firstname', 'shipping_lastname', 'note',]
    list_display = ('id','channel','email','ordernum', 'status', 'import_note', 'note', 'amount', 'currency','rate','payment','amount_shipping','shipping_type','payment','shipping_firstname','shipping_lastname','shipping_country', 'created','create_time','add_user','comment','is_fba' )
    inlines = [OrderItemInline, PackageInline]
    actions = [update_status_to_3,export_order,export_order_invoice]
admin.site.register(Order, OrderAdmin)


class OrderItemAdmin(admin.ModelAdmin):

    ordering = ['-id']
    search_fields = ['channel_oi_id', 'item__sku', 'sku', ]
    list_display = ('id', 'show_order', 'qty', 'item', 'sku', 'price', 'channel_oi_id', 'created', 'updated', 'deleted')
    list_filter=('order__status','order__channel')
    readonly_fields = ('order', 'item', 'created', 'updated', 'price', 'sku', 'qty')

    def show_order(self, obj):
        url = obj.order.get_admin_url()
        return '<a href="%s">%s</a>' % (url, obj.order)

    show_order.allow_tags = True
    show_order.short_description = '订单号'
    show_order.admin_order_field = 'order'
    save_as = True
    save_on_top = True

admin.site.register(OrderItem, OrderItemAdmin)

class SupplierProductInline(admin.TabularInline):

    form = DepotAdminForm

    def depot_code_field(self, obj):
        depot_one= _depot.models.Depot.objects.get(id=obj.depot.id)
        output = u'%s' % depot_one.get_code_display()
        return output

    depot_code_field.allow_tags = True
    depot_code_field.short_description = "实际发货的物理仓库"

    ordering = ['order']
    model = ChannelDepot
    fields = ['depot', 'order','depot_code_field', 'deleted', 'created', 'updated']
    readonly_fields = ('created', 'depot_code_field', 'updated')
    extra = 0
    #max_num = 0
    can_delete = False


class ChannelAdmin(NoDeleteActionModelAdmin):

    form = ChannelUserAdminForm

    def depots_view(self, obj):
        output = " / ".join([depot.name for depot in obj.depots.order_by('id').all()])
        return output
        #return u'%s%s' % (color, obj.site, obj.id)
    depots_view.allow_tags = True
    depots_view.short_description = "仓库"

    list_display = ('id', 'name', 'manager', 'channel_group', 'depots_view', 'default_depot', 'note',)
    list_filter = ('channel_group', OrderManagerFilter)
    save_as = True
    save_on_top = True
    inlines = [SupplierProductInline, ]
    search_fields = ['name']

admin.site.register(Channel, ChannelAdmin)

class ChannelGroupAdmin(admin.ModelAdmin):

    form = ChannelUserAdminForm
    list_display = ('id', 'name', 'note', 'manager')
    save_as = True
    save_on_top = True
admin.site.register(ChannelGroup, ChannelGroupAdmin)


class AliasAdmin(NoDeleteActionModelAdmin):

    form = ItemAdminForm
    #inlines = [ProductRequestProductInline, ProductRequestImageInline, ]
    #date_hierarchy = 'created'
    save_as = True
    save_on_top = True
    search_fields = ['channel__name','sku','item__sku']
    #readonly_fields = ('add_user', 'deleted', 'products')
    list_display = ('id','channel','item', 'sku', 'created',)
    list_filter = ['channel__type','channel__channel_group','channel__manager',]

    def get_urls(self):
        urls = super(AliasAdmin, self).get_urls()
        my_urls = [
            url(r'^import_channel_sku/$', self.import_channel_sku),
        ]
        return my_urls + urls

    def import_channel_sku(self, request):

        if not request.user.has_perm('lib.import_channel_sku'):
            raise Http404(
                    '您没有渠道别名sku导入界面的权限！')

        channels = Channel.objects.filter(deleted=False)
        if request.POST:
            data_error = ''
            msg=''
            data_success = 0
            channel_id = request.POST['channel']
            if not request.FILES:
                data_error = '请选择文件后再提交'
            else:
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                c = Channel.objects.filter(deleted=False,id=channel_id).first()
                if c:
                    if c.name == 'choies.com':
                        c.name = 'choies'
                    if c.name!=filename:
                       data_error = '选择的渠道名称要和上传的文件名称一致'
                else:
                    data_error = '请选择正确的渠道'

            if not data_error:

                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)
                tag = True

                for row in reader:
                    if tag:
                        tag = False
                        continue
                    # print row[0].strip().upper(),row[1].strip().upper()
                    # break
                    # exit()
                    channel_sku = row[0].strip().upper()
                    sku = row[1].strip().upper()    # ws or erp


                    channel_alias = Alias.objects.filter(sku=channel_sku).first()
                    sku_alias = Alias.objects.filter(sku=sku, channel_id=1).first()
                    sku_item = _product.models.Item.objects.filter(sku=sku,deleted=False).first()


                    if channel_alias:
                        msg += "Already,%s,alias already exist |" % channel_sku
                    elif sku_alias:
                        alians, is_created = Alias.objects.get_or_create(channel_id=channel_id,sku = channel_sku,item_id=sku_alias.item_id)
                        msg += "Success,%s,%s|" %(channel_sku, sku_alias.item.sku)
                    elif sku_item:
                        alians, is_created = Alias.objects.get_or_create(channel_id=channel_id,sku = channel_sku,item_id=sku_item.id)
                        msg += "Success,%s,%s|" %(channel_sku, sku_item.sku)
                    else:
                        msg += "Error,%s#%s, not exist|" % (channel_sku, sku)

                # return_tag = import_channel_sku(request.POST.get('sku'),request.POST.get('itemin_number'),3,request.user.id)
                if msg:
                    #下载表格
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="import_alias_sku_errors.csv"'

                    writer = csv.writer(response)
                    writer.writerow(['product_sku'])
                    datas = msg.split('|')
                    for pd in datas:
                        writer.writerow([pd])
                    return response
                # else:
                #     messages.add_message(request, messages.SUCCESS, u'%s表格中的别名已全部验证,成功上传的别名条数是：%d'% (filename,data_success))
            else:
                messages.add_message(request, messages.ERROR, u'%s表格存在问题：%s'% (filename,data_error))

        return TemplateResponse(request, "import_channel_sku.html",{'opts': self.model._meta,'root_path': self.get_urls(),'channels':channels})
admin.site.register(Alias, AliasAdmin)


class ProductSaleAdmin(NoDeleteActionModelAdmin):

    form = ProductSaleAdminForm

    def p_link(self,obj):
        p=obj.product
        link= p.get_admin_url()
        str=u'<a href="%s">产品详情</a>' %(link)

        return str
    p_link.allow_tags = True
    p_link.short_description = "Link"

    #form = ProductAdminForm
    ordering = ['status','-id']
    list_filter = ('status','channel')
    #filter_horizontal = ['categories',]
    save_as = True
    save_on_top = True
    search_fields = ['product__sku', 'product__name',]
    list_display = ('id', 'product', 'channel', 'status', 'note', 'created','p_link')
    #list_editable = ('status', 'cost', 'weight')
    #readonly_fields =  ('categories', 'related_products')
    #formfield_overrides = {models.TextField: {'widget': RichTextEditorWidget},}

    def set_status_0(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=0
            pd.save()

    set_status_0.short_description = u'设置准备上架'

    def set_status_1_1(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=1
            pd.save()

    set_status_1_1.short_description = u'设置正在上架'

    def set_status_1(modeladmin, request, queryset):
        if 'do_action' in request.POST:
            form = ProductsaleActionForm(request.POST)
            if form.is_valid():
                productaction = form.cleaned_data['productaction']
                for paction in productaction:
                    if paction == 'change':
                        for pd in queryset:
                            pd.status = 1
                            pd.save()
                        pass
                    if paction == 'outcsv':

                        response = HttpResponse(content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename="filename.csv"'

                        writer = csv.writer(response)
                        writer.writerow(['product_id', 'product_sku'])
                        for pd in queryset:
                            writer.writerow([pd.product_id,pd.product])

                        return response
                        pass

                messages.success(request, '选择的操作动作执行成功')
                return
        else:
            form = ProductsaleActionForm()

        return TemplateResponse(request, 'action_is_out_tag.html',
            {'title': u'选择需要操作的动作',
             'objects': queryset,
             'form':form,
             'action':'set_status_1'})

    set_status_1.short_description = u'设置正在上架并下载产品表格'

    def set_status_2(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=2
            pd.save()

    set_status_2.short_description = u'设置上架成功'

    def set_status_3(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=3
            pd.save()

    set_status_3.short_description = u'设置上架失败'

    def set_status_4(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=4
            pd.save()

    set_status_4.short_description = u'设置暂不上架'

    def set_status_5(modeladmin, request, queryset):
        for pd in queryset:
            pd.status=5
            pd.save()

    set_status_5.short_description = u'设置待更新'

    def set_status_6(modeladmin, request, queryset):
            response = HttpResponse(content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="filename.csv"'

            writer = csv.writer(response)
            writer.writerow(['product_id', 'product_sku'])
            for pd in queryset:
                writer.writerow([pd.product_id,pd.product])

            return response

    set_status_6.short_description = u'下载选中产品'

    actions = [set_status_0,set_status_1_1,set_status_1,set_status_2,set_status_3,set_status_4,set_status_5,set_status_6]

    # class Media:
    #     js = ("admin/js/tiny_mce/tiny_mce.js", "admin/js/textareas.js",)

    # inlines = [ItemInline, ProductImageInline, SupplierProductInline, ]
    #actions = [make_products_visiable, update_related_products, make_products_invisiable]
admin.site.register(ProductSale, ProductSaleAdmin)
