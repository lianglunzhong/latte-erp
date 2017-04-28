# -*- coding: utf-8 -*-
from django.contrib import admin
from shipping.models import *
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
# from workstation.our_utils import gmt_add8
import lib
import csv
import product
from lib.utils import pp, get_now, eu, write_csv, eparse, add8
from product.forms import *
from lib.admin import NoDeleteActionModelAdmin, NoDeleteActionMPTTModelAdmin

class PackageItemInline(admin.TabularInline):
    form = ItemAdminForm

    def thumb(self, obj):
        p_id = product.models.Item.objects.filter(id=obj.item.id).values_list('product', flat=True)
        images = product.models.ProductImage.objects.filter(product_id=p_id).order_by('-id').all()
        url = ""
        output = ""
        if images:
            for image in images:
                url = '/media/' + str(image.image)
                output = output + u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.item.get_admin_url(),url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.item.get_admin_url(),url)
        output+=u'</a>'
        return output

    # def item_link_field(self, obj):
    #     if obj:
    #         output = u' <a href="%s" target="_blank">%s</a>' % (obj.item.get_admin_url(), obj.item)
    #     else:
    #         output = u''
    #     return output

    def itemwanted_num_field(self, obj):
        itemwanted_qty = ItemWanted.objects.filter(package_item_id=obj.id, deleted=False).aggregate(Sum('qty'))['qty__sum'] or 0
        output1 = u' <a href="/admin/shipping/itemwanted/?q=%s" target="_blank">%s</a><br>' % (obj.id, itemwanted_qty)

        itemlocked_qty = ItemLocked.objects.filter(package_item_id=obj.id, deleted=False).aggregate(Sum('qty'))['qty__sum'] or 0
        output2 = u' <a href="/admin/shipping/itemlocked/?q=%s" target="_blank">%s</a>' % (obj.id, itemlocked_qty)

        return str(output1)+'/'+str(output2)

    # item_link_field.allow_tags = True
    # item_link_field.short_description = u"属性产品+link"

    itemwanted_num_field.allow_tags = True
    itemwanted_num_field.short_description = u"采购需求/占用库存"
    # itemlocked_num_field.allow_tags = True
    # itemlocked_num_field.short_description = u"占用库存量"
    # pick_num_field.allow_tags = True
    # pick_num_field.short_description = u"已拣货量"

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    model = PackageItem
    extra = 0
    fields = ['item',  'thumb', 'qty', 'note', 'deleted', 'itemwanted_num_field', ]
    readonly_fields = ( 'thumb', 'itemwanted_num_field', )
    can_delete = False

class PackageShippingFilter(SimpleListFilter):
    title = u'shipping'
    parameter_name = 'shipping'

    def lookups(self, request, model_admin):
        shipping_list = []
        shipping_list.append(['No_shipping', '(None)'])
        distinct_shippings = Package.objects.filter().values_list("shipping_id").distinct()
        all_shipping = lib.models.Shipping.objects.filter(id__in=distinct_shippings)
        for shipping in all_shipping:
            shipping_list.append([shipping.id, shipping.label])
        return shipping_list

    def queryset(self, request, queryset):
        if self.value() and self.value() != 'No_shipping':
            return queryset.filter(shipping_id=self.value())
        elif self.value() == 'No_shipping':
            return queryset.filter(shipping_id__isnull=True)
        else:
            return queryset.all()

class PackageAdmin(NoDeleteActionModelAdmin):

   #def get_queryset(self, request):
   #    query_set = Package.objects.filter(deleted=False)
   #    return query_set

    # hide Delete Action
    # def get_actions(self, request):
    #     actions = super(PackageAdmin, self).get_actions(request)
    #     if not request.user.is_superuser:
    #         del actions['delete_selected']
    #     return actions
    #
    # def has_delete_permission(self, request, obj=None):
    #     if request.user.is_superuser:
    #         return True
    #     else:
    #         return False

    def export_package(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="pacakge.csv"'
        writer = csv.writer(response)
        writer.writerow(['id','order','ordernum','email','shipping','shipping_country',
        'note', 'status', 'tracking_no', 'created','print_time','ship_time','shop','item',"delivered time", "delivered age","delivery_search_time","17track_status"])

        for query in queryset:
            str_item = ''
            package_items = PackageItem.objects.filter(package_id=query.id)
            for p_item in package_items:
                str_item += "%s:%s; " % (p_item.item.sku, p_item.qty)
            # if not query.tracking_link:
            #     try:
            #         tracking_link = query.shipping.link
            #     except:
            #         tracking_link = ''
            # else:
            #     tracking_link = query.tracking_link
            writer.writerow([
                str(query.id).encode('utf-8'),
                str(query.order).encode('utf-8'),
                str(query.order.ordernum).encode('utf-8'),
                str(query.email).encode('utf-8'),
                str(query.shipping).encode('utf-8'),
                str(query.shipping_country).encode('utf-8'),
                query.note.encode('utf-8'),
                query.get_status_display().encode('utf-8'),
                str(query.tracking_no).encode('utf-8'),
                # str(tracking_link).encode('utf-8'),
                # str(query.cost).encode('utf-8'),
                # str(query.cost1).encode('utf-8'),
                # gmt_add8(query.created),
                # gmt_add8(query.print_time),
                # gmt_add8(query.ship_time),
                # str(query.order.shop).encode('utf-8'),
                str(str_item).encode('utf-8'),
                # gmt_add8(query.delivery_time),
                # str(query.delivery_age).encode('utf-8'),
                # gmt_add8(query.delivery_search_time),
                # query.get_track17_status_display().encode('utf-8'),
            ])
        return response

    def export_package_overweight(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        response = HttpResponse(content_type='text/csv')
        response.write('\xEF\xBB\xBF')
        response['Content-Disposition'] = 'attachment; filename="overweight_pacakge.csv"'
        writer = csv.writer(response)
        writer.writerow(['package_id','total_weight', 'status'])
        queryset = queryset.filter(status=1)
        for query in queryset:
            weight = PackageItem.objects.filter(package=query).aggregate(Sum('item__weight')).get('item__weight__sum', 0)
            if weight >= 1.8:
                writer.writerow([
                str(query.id),
                str(weight).encode('utf-8'),
                '1',
            ])
        return response

    export_package_overweight.short_description = 'csv导出超重package'

    def update_status_to_1(modeladmin, request, queryset):
        for query in queryset:
            if query.status==0:
                query.status = 1
                query.save()

    update_status_to_1.short_description = '包裹单人工审核通过，状态修改成开始处理'

    def show_tracking_link(self, obj):
        try:
            url = obj.shipping.link
        except:
            url = ''
        #如果没有cn_name则显示sku(给一个超链接的入口)
        return '<a href="%s">%s</a>' % (url, url)
    show_tracking_link.allow_tags = True
    show_tracking_link.short_description = 'tracking_link'
    show_tracking_link.admin_order_field = 'tracking_link'

    export_package.short_description = u"CSV导出Package"

    # def get_queryset(self, request):
    #     query_set = Package.objects.exclude(status = 0)
    #     return query_set

    def order_note(self, obj):
        return obj.order.note
    order_note.short_description = u"订单备注"

    def order_active(self, obj):
        return obj.order.get_active_display()

    def shop(self, obj):
        return obj.order.shop

    # def pick_num(self, obj):
    #     try:
    #         pickpackage = PickPackage.objects.filter(package_id = obj.id).order_by("-id")[0]
    #     except:
    #         return ""
    #
    #     picknum = pickpackage.pick.pick_num
    #     return picknum


    # def get_search_results(self, request, queryset, search_term):
    #     #queryset会包含filter过滤的条件, search_term是一个unicode字符串
    #     if search_term and search_term.strip():
    #         id_list = search_fun(self.__class__.search_fields, search_term, queryset)
    #         queryset = self.model.objects.filter(id__in=id_list).order_by('order__ordernum')
    #     else:
    #         queryset, use_distinct = super(self.__class__, self).get_search_results(request, queryset, search_term)
    #     return queryset, False

    date_hierarchy = 'created'
    search_fields = ('id', 'tracking_no','order__ordernum', 'email')
    list_display = ('id', 'shipping', 'shipping_country', 'show_order','order_note', 'weight', 'qty', 'sku_qty', 'pick_type', 'pick', 'status', 'tracking_no', 'show_tracking_link','created', )
    # inlines = [PackageItemInline, ]
    list_filter = ('status', PackageShippingFilter, 'pick_type','order__channel','order__status')
    # exclude = ("tracking_link", )   #过滤这个字段不显示在编辑页面, list展示的是外键shipping的link
    actions = (export_package, export_package_overweight, update_status_to_1)
    readonly_fields = ('order',)

    def get_readonly_fields(self, request, obj=None):
        this_readonly_fields = list(self.readonly_fields)
        if obj and obj.cost == 0:
            this_readonly_fields.append('cost1')
        if obj and obj.status == 4:
            this_readonly_fields.append('status')
        if not request.user.is_superuser:
            this_readonly_fields.extend(['tracking_no', 'pick_type'])
        return this_readonly_fields

    def show_order(self, obj):
       #url = reverse('admin:workstation_order_change', args=(obj.order.id,))
        url = obj.order.get_admin_url()
        return '<a href="%s">%s</a>' % (url, obj.order.ordernum)
    show_order.allow_tags = True
    show_order.short_description = 'order'
    show_order.admin_order_field = 'order'

    save_as = True
    save_on_top = True
    inlines = [PackageItemInline, ]
admin.site.register(Package, PackageAdmin)

class PackageItemAdmin(NoDeleteActionModelAdmin):

    def get_queryset(self, request):
        query_set = PackageItem.objects.filter(deleted=False)
        return query_set

    list_display = ('id', 'item', 'qty', 'note',)
    readonly_fields = ('item', 'qty', 'package', 'deleted')
    search_fields = ['id', 'package__id', 'item__sku', ]

    save_as = True
    save_on_top = True
admin.site.register(PackageItem, PackageItemAdmin)

class SuppliertypeFilter(SimpleListFilter):
    title = u'供应商类型'
    parameter_name = 'type'
    # for user in users:

    def lookups(self, request, model_admin):
        supplier_type = []
        supplier_type.append([0, '线下'])
        supplier_type.append([1, '线上'])
        supplier_type.append([2, '工厂'])
        return supplier_type
    def queryset(self, request, queryset):
        #supplier_type = obj.purchaseorderitem.purchaseorder.supplier.get_type_display()
        if self.value() and self.value()!='No_assigner':
            return queryset.filter(purchaseorderitem__purchaseorder__supplier__type=self.value())
        elif self.value() == 'No_assigner':
            return queryset.filter(add_user_id__isnull=True)
        else:
            return queryset.all()

# class ItemWantedAdmin(admin.ModelAdmin):
class ItemWantedAdmin(NoDeleteActionModelAdmin):
    # list_display = ('id', 'name', 'note', 'manager')
    # def get_queryset(self, request):
    #     query_set = ItemWanted.objects.filter(deleted=False)
    #     return query_set

    # def item_link(self,obj):
    #     link=obj.item.get_admin_url()
    #     obj_item='<a href="%s">' %(link)
    #     obj_item+=obj.item.__unicode__()
    #     obj_item+='</a>'
    #     return obj_item
    #
    # item_link.allow_tags = True
    # item_link.short_description = "包裹单货品sku"

    def pkg_link(self,obj):
        link=obj.package_item.package.get_admin_url()
        obj_item='<a href="%s">' %(link)
        obj_item+=str(obj.package_item.package.id)
        obj_item+='</a>'
        return obj_item

    pkg_link.allow_tags = True
    pkg_link.short_description = "包裹单"

    def pitem_link(self,obj):
        link=obj.package_item.get_admin_url()
        str_pitem_link='<a href="%s">' %(link)
        str_pitem_link+=str(obj.package_item.id)
        str_pitem_link+='</a>'
        return str_pitem_link

    pitem_link.allow_tags = True
    pitem_link.short_description = "包裹单货品"

    def oitem_link(self,obj):
        link=obj.package_item.package.order.get_admin_url()
        str_oitem_link='<a href="%s">' %(link)
        str_oitem_link+=str(obj.package_item.package.order.id)
        str_oitem_link+='</a>'
        return str_oitem_link

    oitem_link.allow_tags = True
    oitem_link.short_description = "订单"

    def poitem_link(self,obj):
        # a = obj.purchaseorderitem.id
        # print a
        link = u''
        poid = u''
        str_purchaseorderitem_link = u''
        if obj.purchaseorderitem:
            link = obj.purchaseorderitem.purchaseorder.get_admin_url()
            poid = obj.purchaseorderitem.purchaseorder.id
            str_purchaseorderitem_link='<a href="%s">' %(link)
            str_purchaseorderitem_link+=str(obj.purchaseorderitem.purchaseorder.id)
            str_purchaseorderitem_link+='</a>'
        return str_purchaseorderitem_link

    poitem_link.allow_tags = True
    poitem_link.short_description = "采购单号"

    def depot_link(self,obj):
        link=obj.depot.get_admin_url()
        str='<a href="%s">' %(link)
        str+=obj.depot.name
        str+='</a>'
        return str

    depot_link.allow_tags = True
    depot_link.short_description = "仓库"

    def item_sku(self,obj):
        link=obj.item.get_admin_url()
        str='<a href="%s">' %(link)
        str+=obj.item.sku
        str+='</a>'
        return str

    item_sku.allow_tags = True
    item_sku.short_description = "sku"

    def order_alias_sku(self,obj):
        alias_sku = order.models.Alias.objects.filter(item_id=obj.item.id,deleted=False,channel_id=1).first()
        if not alias_sku:
            str='%s' %('')
        else:
            str='%s' %(alias_sku.sku)
            return str

    order_alias_sku.allow_tags = True
    order_alias_sku.short_description = "渠道sku销售别名"

    def item_size(self,obj):
        size_id = obj.item.key.split("-")[2]
        product_option = Option.objects.filter(id =size_id,deleted=False).first()
        if product_option:
            size = product_option.name
        else:
            size=''
        return size

    def item_supplier(self,obj):
        if not obj.purchaseorderitem:
            supplier_name = ""
        else:
            supplier_name = obj.purchaseorderitem.purchaseorder.supplier.name
        return supplier_name

    item_supplier.allow_tags = True
    item_supplier.short_description = "供应商"

    def item_supplier_type(self,obj):
        if not obj.purchaseorderitem:
            supplier_type = ""
        else:
            supplier_type = obj.purchaseorderitem.purchaseorder.supplier.get_type_display()
        return supplier_type

    item_supplier_type.allow_tags = True
    item_supplier_type.short_description = "供应商类型"

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.item.product.get_images()
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
    thumb.short_description = "Image"

    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(ItemWantedAdmin, self).get_search_results(request, queryset, search_term)
        q = request.GET.get('q', '')
        if search_term:
            alias_sku = order.models.Alias.objects.filter(sku=q,deleted=False,channel_id=1).first()
            if alias_sku:
                queryset = ItemWanted.objects.filter(item=alias_sku.item)
        return queryset, use_distinct

    def export_itemwanted(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        # response = HttpResponse(content_type='text/csv')
        # response.write('\xEF\xBB\xBF')
        # response['Content-Disposition'] = 'attachment; filename="DepotItem.csv"'
        response, writer = write_csv("itemwanted")
        writer.writerow(["ID","包裹单","包裹单货品","订单","采购单号","仓库","SKU","渠道sku销售别名","Item size","供应商","供应商类型","采购需求数量","新增时间","修改时间","是否已删除"])
        for query in queryset:
            order_alias = order.models.Alias.objects.filter(channel_id=1,item_id=query.item.id,deleted=False).first()
            sku_alias =u""
            if order_alias:
                sku_alias=order_alias.sku

            size_id = query.item.key.split("-")[2]
            product_option = Option.objects.filter(id =size_id,deleted=False).first()
            if product_option:
                size = product_option.name
            else:
                size=u''

            if not query.purchaseorderitem:
                supplier_name = ""
                supplier_type = ""
                purchaseorder_id = ""
            else:
                supplier_name = query.purchaseorderitem.purchaseorder.supplier.name
                supplier_type = query.purchaseorderitem.purchaseorder.supplier.get_type_display()
                purchaseorder_id = query.purchaseorderitem.purchaseorder_id

            row = [
                str(query.id),
                str(query.package_item.package.id),
                str(query.package_item.id),
                str(query.package_item.package.order.id),
                str(purchaseorder_id),
                str(query.depot.name),
                str(query.item.sku),
                str(sku_alias),
                str(size),
                str(supplier_name),
                str(supplier_type),
                str(query.qty),
                str(query.created),
                str(query.updated),
                str(query.deleted)
            ]
            writer.writerow(row)
        return response
    export_itemwanted.short_description = u"CSV导出采购需求"

    actions = [export_itemwanted,]

    save_as = True
    save_on_top = True
    search_fields = ['id','item__sku','package_item__id','item__product__sku']
    list_filter = (SuppliertypeFilter,'deleted',)
    list_display = ('id', 'pkg_link', 'pitem_link','oitem_link','poitem_link','depot_link','item_sku','order_alias_sku','item_size','item_supplier','item_supplier_type','qty', 'thumb', 'created', 'updated', 'deleted')
    readonly_fields = ['item', 'depot', 'package_item', 'purchaseorderitem','qty']
admin.site.register(ItemWanted, ItemWantedAdmin)


class ItemLockedAdmin(NoDeleteActionModelAdmin):
#class ItemLockedAdmin(admin.ModelAdmin):

   # def get_queryset(self, request):
   #    query_set = ItemLocked.objects.filter(deleted=False)
   #    return query_set

    def pkg_link(self,obj):
        link=obj.package_item.package.get_admin_url()
        str='<a href="%s">' %(link)
        str+=obj.package_item.package.__unicode__()
        str+='</a>'
        return str

    pkg_link.allow_tags = True
    pkg_link.short_description = "包裹单"

    def pitem_link(self,obj):
        link=obj.package_item.get_admin_url()
        str='<a href="%s">' %(link)
        str+=obj.package_item.__unicode__()
        str+='</a>'
        return str

    pitem_link.allow_tags = True
    pitem_link.short_description = "包裹单货品"

    def item_depot(self,obj):
        link=obj.depot_item.depot.get_admin_url()
        str='<a href="%s">' %(link)
        str+=obj.depot_item.depot.name
        str+='</a>'
        return str

    item_depot.allow_tags = True
    item_depot.short_description = "仓库"

    def thumb(self, obj):
        #output =u'<img src="%s"/>' % (obj.get_simage())
        images = obj.package_item.item.product.get_images()
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
    thumb.short_description = "Image"

    save_as = False
    save_on_top = True
    search_fields = ('id','depot_item__item__sku','package_item__package__id','package_item__id')
    list_display = ('id', 'pkg_link', 'pitem_link', 'item_depot', 'depot_item', 'qty', 'thumb', 'created', 'updated', 'deleted')
    readonly_fields = ['depot_item', 'package_item', 'qty', ]
    list_filter = ('depot_item__depot',)


admin.site.register(ItemLocked, ItemLockedAdmin)

class NxbCodeAdmin(admin.ModelAdmin):
    save_as = True
    save_on_top = True
    list_display = ('code', 'is_used', 'used_time', 'package_id', 'note')
admin.site.register(NxbCode, NxbCodeAdmin)
