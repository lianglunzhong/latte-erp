# -*- coding: utf-8 -*-
from django.contrib import admin
from depot.models import *
from lib.admin import NoDeleteActionModelAdmin, NoDeleteActionMPTTModelAdmin
from dal import autocomplete
from product.forms import *
from depot.forms import *
import order
from django.shortcuts import redirect
from lib.utils import pp, get_now, eu, write_csv, eparse, add8
from django.db.models import Sum
from django.conf.urls import url, include
from django.contrib import messages
from django.template.response import TemplateResponse,HttpResponse
import csv,StringIO
from django.contrib.admin import SimpleListFilter
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404

class DepotManagerFilter(SimpleListFilter):
    title = u'负责人'
    parameter_name = 'manager'
    # for user in users:

    def lookups(self, request, model_admin):
        user_list = []
        user_list.append(['No_assigner', '(None)'])
        # assigner_ids = ProductAction.objects.values_list("manager_id").distinct()
        # users = User.objects.filter(id__in=assigner_ids).order_by('username')
        users = User.objects.filter(groups__name='[仓库组]').filter(is_staff=1).order_by('username')
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



class DepotItemAdmin(NoDeleteActionModelAdmin):

    def thumb(self, obj):
        p_id = Item.objects.filter(id=obj.item.id).values_list('product', flat=True)
        images = ProductImage.objects.filter(product_id=p_id).order_by('-id').all()
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

    def item_link_field(self, obj):
        order_alias = order.models.Alias.objects.filter(channel_id=1,item=obj.item,deleted=False).first()
        sku_alias =u""
        if order_alias:
            sku_alias=order_alias.sku
        if obj:
            output = u' <a href="%s" target="_blank">%s</a><br/><br/><a href="%s" target="_blank">%s</a><br/><br/>%s' % (obj.item.get_admin_url(), obj.item,obj.depot.get_admin_url(), obj.depot,sku_alias)
        else:
            output = u''
        return output

    item_link_field.allow_tags = True
    item_link_field.short_description = u"仓库名称+货品"

    # def depot_link_field(self, obj):
    #     if obj:
    #         output = u' <a href="%s" target="_blank">%s</a>' % (obj.depot.get_admin_url(), obj.depot)
    #     else:
    #         output = u''
    #     return output
    #
    # depot_link_field.allow_tags = True
    # depot_link_field.short_description = u"仓库名称"
    def get_search_results(self, request, queryset, search_term):
        queryset, use_distinct = super(DepotItemAdmin, self).get_search_results(request, queryset, search_term)
        q = request.GET.get('q', '')
        if search_term:
            alias_sku = order.models.Alias.objects.filter(sku=q,deleted=False,channel_id=1).first()
            if alias_sku:
                queryset = DepotItem.objects.filter(item=alias_sku.item)
        return queryset, use_distinct
        

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"
    save_as = True
    save_on_top = True
    search_fields = ['item__key','item__sku', 'position']
    list_filter = ('depot', 'deleted')
    list_display = ('id', 'item_link_field', 'thumb', 'total', 'qty', 'qty_locked', 'position', 'deleted',  'created', 'updated',)
    readonly_fields = ('item', 'depot', 'qty', 'total', 'qty_locked', 'deleted', 'created', 'updated',)

    def get_urls(self):
        urls = super(DepotItemAdmin, self).get_urls()
        my_urls = [
            url(r'^import_depotitem_location/$', self.import_depotitem_location),
            url(r'^import_depotinlog/$', self.import_depotinlog),
            url(r'^import_depotoutlog/$', self.import_depotoutlog),
            url(r'^bulk_print_barcode/$', self.bulk_print_barcode),
            # url(r'^update_depotoutlog_cost/$', self.update_depotoutlog_cost),

        ]
        return my_urls + urls

    def import_depotitem_location(self, request):
        if not request.user.has_perm('lib.import_depotitem_location'):
            raise Http404(
                    '您没有南京仓批量更新货品库位界面的权限！')
        if request.POST:

            data_error1=''
            if not request.FILES:
                data_error = u'请选择文件后再提交'
                messages.add_message(request, messages.ERROR,u'上传失败：%s'%data_error)
            else:
                depot = request.POST['depot_id']
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)

                headers = next(reader)#去掉首行
                for row in reader:
                    row = [i.strip() for i in row]
                    alias = order.models.Alias.objects.filter(deleted=False,sku=row[1]).first()
                    if alias:
                        depotitem = DepotItem.objects.filter(item=alias.item,depot_id=depot).first()
                        if depotitem:
                            if depotitem.position:
                                old_list =depotitem.position.split(',')
                                if row[2] not in old_list:
                                    depotitem.position += ','+row[2]
                            else:
                                depotitem.position = row[2]
                            depotitem.save()
                            data_error1 += u'SUCCESS,%s,%s |'%(row[1],depotitem.position)
                        else:
                            depotitem = DepotItem.objects.create(item=alias.item,depot_id=depot,position=row[2])

                    else:

                        data_error1 += u'ERROR,%s,%s,alias not exist |'%(row[1],row[2])

                if data_error1:
                    #下载表格
                    response = HttpResponse(content_type='text/csv')
                    response['Content-Disposition'] = 'attachment; filename="import_depotitem_location_errors.csv"'

                    writer = csv.writer(response)
                    writer.writerow(['product_sku'])
                    datas = data_error1.split('|')
                    for pd in datas:
                        writer.writerow([pd])

                    return response

        return TemplateResponse(request, "import_depotitem_location.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

# <QueryDict: {u'item_sku': [u'dfsddfsg'], u'qty': [u'4'], u'note': [u'gfsd'], u'c
# ost': [u'6'], u'csrfmiddlewaretoken': [u'2Cn4z9Vzmatuv80F3BpGEI6SxuiYT12O'], u't
# ype': [u'3']}>
    def import_depotinlog(self, request):
        if not request.user.has_perm('lib.import_depotinlog'):
            raise Http404(
                    '您没有手动杂入界面的权限！')
        context = {}
        msg=''
        if request.POST:
            if request.POST.get("type") == 'import_depotinlog_single':
                post_arr = request.POST
                try:
                    qty = int(post_arr['qty'])
                except Exception,e:
                    qty = 0
                try:
                    cost = float(post_arr['cost'])
                except Exception,e:
                    cost = 0

                note = post_arr['note'].strip()

                item = Item.objects.filter(deleted=False,sku=post_arr['item_sku']).first()
                if item and qty > 0:
                    depotitem,flag = DepotItem.objects.get_or_create(depot_id=post_arr['depot_id'],item_id=item.id)
                    print 'depotitem',depotitem
                    obj=None
                    re = depotitem.item_in(qty,cost,note,obj,post_arr['depotinlog_type'],request.user)
                    if not re:
                        msg +=u"%s入库失败 | "% post_arr['item_sku']
                else:
                    if not item:
                        msg +=u"%s货品sku系统中不存在 | "% post_arr['item_sku']
                    if qty<=0:
                        msg +=u"入库数量必须大于0 | "


                if msg:
                    messages.add_message(request, messages.ERROR,msg)
                else:
                    messages.add_message(request, messages.SUCCESS,u"%s货品杂入成功"% post_arr['item_sku'])

            elif request.POST.get("type") == 'import_depotinlog_batch':
                if not request.FILES:
                    data_error = u'请选择文件后再提交'
                    messages.add_message(request, messages.ERROR, data_error)
                else:
                    datas = request.FILES['csvFile']
                    filename = datas.name.split('.')[0]
                    reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
                    header = next(reader)
                    i=0
                    msg=''
                    data ={}
                    for row in reader:
                        i +=1
                        for j in range(0,4):
                            row[j] = row[j].strip()
                            if j ==1:
                                try:
                                   row[j]=int(row[j])
                                except Exception,e:
                                    row[j] = 0
                            if j==2:
                                try:
                                   row[j]=float(row[j])
                                except Exception,e:
                                    row[j] = 0

                        item = Item.objects.filter(deleted=False,sku=row[0]).first()
                        if not item:
                            msg +=u'ERROR,第%s行的%s货品sku系统不存在 |'%(i,row[0])
                        if row[1]<=0:
                            msg +=u'ERROR,第%s行的货品%s入库数量必须大于0 |'%(i,row[0])
                        if row[3] not in ['移库入库','杂入-made系统']:
                            msg +=u'ERROR,第%s行的货品是%s入库类型只能是移库入库 / 杂入-made系统 |'%(i,row[0])

                        data[i] = row
                    if msg:
                        #下载表格
                        response = HttpResponse(content_type='text/csv')
                        response['Content-Disposition'] = 'attachment; filename="import_alias_sku_errors.csv"'

                        writer = csv.writer(response)
                        writer.writerow(['表格问题反馈'])
                        datas = msg.split('|')
                        for pd in datas:
                            writer.writerow([pd])
                        return response
                    else:
                        for i in data:
                            item = Item.objects.filter(deleted=False,sku=data[i][0]).first()
                            if item and data[i][1] > 0:
                                depotitem,flag = DepotItem.objects.get_or_create(depot_id=request.POST.get("depot_id"),item_id=item.id)
                                obj=None
                                if data[i][3]=='移库入库':
                                    data[i][3]=4
                                elif data[i][3]=='杂入-made系统':
                                    data[i][3]=5
                                re = depotitem.item_in(data[i][1],data[i][2],data[i][4],obj,data[i][3],request.user)
                                if not re:
                                    messages.add_message(request, messages.ERROR,u'%s'% data[i][0])
                        messages.add_message(request, messages.SUCCESS,u"%s表格上传成功，请去入库记录检查明细"% filename)

        return TemplateResponse(request,"import_depotinlog.html",context)


    def import_depotoutlog(self, request):
        if not request.user.has_perm('lib.import_depotoutlog'):
            raise Http404(
                    '您没有手动杂出界面的权限！')
        context = {}
        msg=''
        if request.POST:
            post_arr = request.POST

            try:
                qty = int(post_arr['qty'])

            except Exception,e:
                qty = 0

            note = post_arr['note'].strip()
            # post_arr['item_sku'] = post_arr['item_sku'].strip()
            item = Item.objects.filter(deleted=False,sku=post_arr['item_sku']).first()
            print qty
            if item and qty > 0:
                depotitem,flag = DepotItem.objects.get_or_create(depot_id=post_arr['depot_id'],item=item.id)
                print 'depotitem',depotitem
                obj=None
                re = depotitem.item_out(qty,note,obj,post_arr['type'],request.user)
                if not re:
                    msg +=u"%s货品sku库存不足，出库失败 | "% post_arr['item_sku']
            else:
                if not item:
                    msg +=u"%s货品sku系统中不存在 | "% post_arr['item_sku']
                if qty<=0:
                    msg +=u"出库数量必须大于0 | "


            if msg:
                messages.add_message(request, messages.ERROR,msg)
            else:
                messages.add_message(request, messages.SUCCESS,u"%s货品杂出成功"% post_arr['item_sku'])

        return TemplateResponse(request, "import_depotoutlog.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    def bulk_print_barcode(self, request):
        if request.POST.get('type') == "bulk_print_barcode":
            reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
            head = next(reader)
            depotitem_id_list = []
            qty_list = []

            depot_id = request.POST.get('depot')
            wash_mark = request.POST.get('wash_mark', '0') or '0'
            for sku, qty in reader:
                print sku, qty
                try:
                    depotitem = DepotItem.objects.get(item__sku=sku, depot_id=depot_id)
                    qty = int(qty)
                    depotitem_id_list.append(str(depotitem.id))
                    qty_list.append(str(qty))
                except Exception, e:
                    print str(e)
            path = "/tongguan/print_barcode/?depotitem_id=%s&qty=%s&wash_mark=%s" %(','.join(depotitem_id_list), ','.join(qty_list), wash_mark)
            return HttpResponseRedirect(path)
        return TemplateResponse(request, "bulk_print_barcode.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    # def update_depotoutlog_cost(self, request):
    #     msg=u'修改订单销售出库的出库单成本，只执行一次，因为第一天库存表中没有成本'
    #     depotoutlogs = DepotOutLog.objects.filter(type=0,deleted=False,cost=0)
    #     i=0
    #     for depotoutlog in depotoutlogs:
    #         depotinlog = DepotInLog.objects.filter(type=4,deleted=False,item=depotoutlog.item,depot=depotoutlog.depot).first()
    #         if depotinlog:
    #             i +=1
    #             depotoutlog.cost = depotinlog.cost
    #             depotoutlog.save()
    #     msg +=u', 更新成功的库存数是%d'% i
    #     messages.add_message(request, messages.ERROR,msg)
    #     return TemplateResponse(request, "import_depotoutlog.html",{'opts': self.model._meta,'root_path': self.get_urls(),})

    def export_depotitem(modeladmin, request, queryset):
        # Create the HttpResponse object with the appropriate CSV header.
        # response = HttpResponse(content_type='text/csv')
        # response.write('\xEF\xBB\xBF')
        # response['Content-Disposition'] = 'attachment; filename="DepotItem.csv"'
        response, writer = write_csv("DepotItem")
        writer.writerow(["ID","sku","渠道别名sku","实际库存量","已锁库存量","可用库存量","库位","成本","单位成本"])
        for query in queryset:
            order_alias = order.models.Alias.objects.filter(channel_id=1,item_id=query.item.id,deleted=False).first()
            sku_alias =u""
            if order_alias:
                sku_alias=order_alias.sku

            canuse_qty = query.qty - query.qty_locked
            if query.qty:
                row = [
                    str(query.id),
                    eu(query.item.sku),
                    str(sku_alias),
                    str(query.qty),
                    str(query.qty_locked),
                    str(canuse_qty),
                    eu(query.position),
                    str(query.total),
                    str(round(query.total/query.qty,2))
                ]
            else:
                row = [
                    str(query.id),
                    eu(query.item.sku),
                    str(sku_alias),
                    str(query.qty),
                    str(query.qty_locked),
                    str(canuse_qty),
                    eu(query.position),
                    str(query.total),
                    0
                ]
            writer.writerow(row)
        return response
    export_depotitem.short_description = u" CSV导出货品库存"

    def export_depotitem_inventory(modeladmin, request, queryset):
        response, writer = write_csv("DepotItems")
        writer.writerow(["ID", "sku", "渠道别名sku", "实际库存量", "已锁库存量", "可用库存量", "库位","成本","单位成本"])
        queryset=queryset.filter(qty__gt=0)
        for query in queryset:
            order_alias_list = order.models.Alias.objects.filter(channel_id=1, item_id=query.item.id, deleted=False).first()
            sku_alias = u""
            if order_alias_list:
                sku_alias = order_alias_list.sku

            canuse_qty = query.qty - query.qty_locked
            row = [
                str(query.id),
                eu(query.item.sku),
                str(sku_alias),
                str(query.qty),
                str(query.qty_locked),
                str(canuse_qty),
                eu(query.position),
                str(query.total),
                str(round(query.total/query.qty,2))
            ]
            writer.writerow(row)
        return response

    export_depotitem_inventory.short_description=u" csv导出有库存的产品"
    actions = [export_depotitem,export_depotitem_inventory]
admin.site.register(DepotItem, DepotItemAdmin)

class ChannelDepotInline(admin.TabularInline):

    def channel_link_field(self, obj):
        if obj:
            output = u' <a href="%s" target="_blank">%s</a>' % (obj.channel.get_admin_url(), obj.channel)
        else:
            output = u''
        return output

    channel_link_field.allow_tags = True
    channel_link_field.short_description = u"渠道名称"

    model = order.models.ChannelDepot
    extra = False
    fields = ['channel_link_field', 'order', 'created', 'updated', 'deleted']
    readonly_fields = ('channel_link_field', 'channel', 'order', 'created', 'updated', 'deleted',)
    max_num = 0
    can_delete = False


class DepotAdmin(NoDeleteActionModelAdmin):
    form = DepotManagerAdminForm

    def depot_item_num_field(self, obj):
        if obj:
            depot_item_count = DepotItem.objects.filter(depot=obj.id, deleted=False).count()
            depot_item = DepotItem.objects.filter(depot=obj.id, deleted=False)
            depot_item_qty = depot_item.aggregate(qty=Sum('qty'))
            depot_item_qty_locked = depot_item.aggregate(qty_locked=Sum('qty_locked'))
            if not depot_item_qty['qty']:
                depot_item_qty['qty'] = 0
            if not depot_item_qty_locked['qty_locked']:
                depot_item_qty_locked['qty_locked'] = 0
            output = u'%s # %s # %s'% (depot_item_count,depot_item_qty['qty'],depot_item_qty_locked['qty_locked'])
        else:
            output = u''
        return output

    depot_item_num_field.allow_tags = True
    depot_item_num_field.short_description = u"仓库货品种数 # 实际库存量 # 已锁库存量"

    save_as = True
    save_on_top = True
    list_filter = ('name', 'code',DepotManagerFilter)
    list_display = ('id', 'name',  'manager', 'code', 'depot_item_num_field', 'note', 'created', 'updated', 'deleted',)
    inlines = [ChannelDepotInline, ]
admin.site.register(Depot, DepotAdmin)


class DepotInLogAdmin(NoDeleteActionModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.operator_id:
            obj.operator_id = request.user.id
        super(DepotInLogAdmin, self).save_model(request, obj, form, change)

 # editing an existing object 区分add和change界面，change设置只读
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('depot', 'item', 'qty', 'cost', 'type',)
        return self.readonly_fields

    form = DepotInLogAdminForm

    save_as = True
    save_on_top = True
    search_fields = ['item__key', 'item__sku']
    fields = ('depot', 'item', 'qty', 'cost', 'type', 'content_type', 'object_id', 'note', 'operator')
    readonly_fields = ('operator', 'content_type', 'object_id',)
    list_display = ('id', 'item', 'depot', 'qty', 'type', 'content_type', 'object_id', 'operator', 'cost', 'created')
    list_filter = ('depot', 'type')

admin.site.register(DepotInLog, DepotInLogAdmin)


class DepotOutLogAdmin(NoDeleteActionModelAdmin):

    def save_model(self, request, obj, form, change):
        if not obj.operator_id:
            obj.operator_id = request.user.id
        super(DepotOutLogAdmin, self).save_model(request, obj, form, change)

 # editing an existing object 区分add和change界面，change设置只读
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return self.readonly_fields + ('depot', 'item', 'qty', 'cost', 'type',)
        return self.readonly_fields

    form = DepotOutLogAdminForm

    save_as = True
    save_on_top = True
    search_fields = ['item__key','item__sku']
    fields = ('depot', 'item', 'qty', 'cost', 'type', 'content_type', 'object_id', 'note', 'operator')
    readonly_fields = ('operator', 'content_type', 'object_id',)
    list_display = ('id', 'item', 'depot', 'qty', 'type', 'content_type', 'object_id', 'operator', 'cost', 'created')
    list_filter = ('depot', 'type')
admin.site.register(DepotOutLog, DepotOutLogAdmin)


class PickItemInline(admin.TabularInline):

    def thumb(self, obj):

        p_id = product.models.Item.objects.filter(id=obj.depot_item.item.id).values_list('product', flat=True)
        images = product.models.ProductImage.objects.filter(product_id=p_id).order_by('-id').all()
        url = ""
        output = ''
        if images:
            for image in images:
                url = '/media/' + str(image.image)
                output = output + u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.depot_item.item.get_admin_url(),url)
                break
        else:
            url = "http://placehold.it/100x100"
            output =u'<a href="%s" target="_blank"><img src="%s" width="100px"/>' % (obj.depot_item.item.get_admin_url(),url)
        output+=u'</a>'
        return output

    thumb.allow_tags = True
    thumb.short_description = u"缩略图"

    model = PickItem
    extra = False
    fields = ['depot_item', 'thumb', 'qty', 'created', 'updated', ]
    readonly_fields = ('depot_item', 'thumb', 'qty', 'created', 'updated', )
    max_num = 0
    can_delete = False


class PickAdmin(NoDeleteActionModelAdmin):

    save_as = True
    save_on_top = True
    list_display = ('id', 'status','type','pick_type','user_adder', 'print_time', 'assign_time', 'pick_start', 'pick_end','is_error','created',)
    list_filter = ('status','type','pick_type','user_adder','is_error')
    readonly_fields = ('id', 'status', 'created', 'type', 'print_time',)
    inlines = [PickItemInline, ]
    # form = OutPackageAdminForm

    # inlines = [PickPackageInline,]
    # Set all fields readonly
   #def get_readonly_fields(self, request, obj=None):
   #    if not request.user.is_superuser:

   #        return list(set(
   #            [field.name for field in self.opts.local_fields] +
   #            [field.name for field in self.opts.local_many_to_many]
   #        ))
   #    else:
   #        return ['pick_num', 'pick_type', 'ship_type', 'created', 'creater']

admin.site.register(Pick, PickAdmin)

class PickItemAdmin(NoDeleteActionModelAdmin):
   save_as = True
   save_on_top = True
   search_fields = ['depot_item__item__key', 'depot_item__depot__name']
   list_display = ('pick', 'depot_item', 'qty', 'created', 'updated', )
   readonly_fields = ('pick', 'depot_item', 'qty', 'created', 'updated', )
   can_delete = False

admin.site.register(PickItem, PickItemAdmin)

