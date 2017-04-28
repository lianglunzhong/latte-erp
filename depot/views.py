# -*- coding: utf-8 -*-
import csv
import json
import datetime
import time
import re
import StringIO

from django.http import HttpResponse,HttpResponseRedirect
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from lib.utils import pp, get_now, eu, write_csv, eparse, add8
from lib.models import Shipping, Country
from product.models import Product,Item
from shipping.models import Package, PackageItem, NxbCode, ItemLocked, PackagePickError
from order.models import Channel, Alias, OrderItem
from depot.models import Depot, Pick, PickItem, DepotOutLog, DepotItem
from supply.models import SupplierProduct
from tongguan.models import Package3bao, Product3bao
from django.template.response import TemplateResponse,HttpResponse
from django.contrib.auth.decorators import login_required, permission_required

def index(request):
    data= {}
    if request.POST:
        pass

    return TemplateResponse(request,'bulk_print_barcode.html',{'data':data})

@login_required
@permission_required('lib.export_depotitem_cost_inventory')
def export_depotitem_cost_inventory(request):
    data= {}
    if request.POST:
        msg1 = msg2 =''
        if request.POST.get("type") == 'export_depotitem_cost_inventory':
            item_str = request.POST.get("item")
            if not item_str:
                msg1 += u"请输入货品sku"
                messages.add_message(request, messages.ERROR,u'查询失败：%s'%msg1)
            else:
                item_array = item_str.strip().split('\r\n')

                i =0
                data ={}
                for item_sku in item_array:
                    i +=1
                    item_sku = item_sku.strip()
                    item = Item.objects.filter(deleted=False,sku=item_sku).first()

                    if not item:
                        item_alias = Alias.objects.filter(deleted=False,sku=item_sku,channel=1).first()
                        if not item_alias:
                            msg2 += u"%s货品sku和choies别名sku在系统里不存在 |"% item_sku
                        else:
                            item = Item.objects.filter(deleted=False,id=item_alias.item_id).first()
                            data[i] = item
                    else:
                        data[i] = item

                if not msg1 and not msg2:
                    #下载产品相关的成本库存数据
                    response, writer = write_csv("export_depotitem_cost_inventory")
                    writer.writerow([
                        'Item_sku', 'chioes_model','chioes_sku', 'model', 'supplier_name','南京仓实际库存',
                        '南京仓已锁库存', '产品参考成本','货品参考成本', 'item实际成本=仓库货品总成本/数量',
                    ])

                    for j in data:
                        depotitem = DepotItem.objects.filter(deleted=False,item_id=data[j].id,depot__code=1).first()
                        supplier = SupplierProduct.objects.filter(deleted=False,product_id=data[j].product.id).order_by('order').values_list('supplier__name', flat=True)
                        supplier_str = ','.join(supplier)
                        alias = Alias.objects.filter(deleted=False,item_id=data[j].id,channel=1).values_list('sku', flat=True)
                        sku_str = ','.join(alias)
                        if depotitem:
                            if depotitem.qty:
                                real_cost = depotitem.total/depotitem.qty
                            else:
                                real_cost=0
                            row = [
                                data[j].sku,
                                data[j].product.choies_sku,
                                sku_str,
                                data[j].product.sku,
                                eu(supplier_str),
                                depotitem.qty,
                                depotitem.qty_locked,
                                data[j].product.cost,
                                data[j].cost,
                                real_cost,
                            ]
                        else:
                            row = [
                                data[j].sku,
                                data[j].product.choies_sku,
                                sku_str,
                                data[j].product.sku,
                                eu(supplier_str),
                            ]
                        writer.writerow(row)
                    return response

                elif msg2:
                    #下载表格,错误提示
                    response, writer = write_csv("export_depotitem_cost_inventory_error")
                    writer.writerow(['error item_sku'])
                    data_array = msg2.split('|')
                    for p in data_array:
                        writer.writerow([p])
                    return response
    return TemplateResponse(request,'export_depotitem_cost_inventory.html',{'data':data})

@login_required
@permission_required('lib.import_depotitem_location')
def import_depotitem_location(request):
    data= {}
    if request.POST:
        mag1=''
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
                alias = Alias.objects.filter(deleted=False,sku=row[1]).first()
                #先查询销售别名sku，别名sku不存在则查询货品sku
                if not alias:

                    item = Item.objects.filter(deleted=False,sku=row[1]).first()
                    if item:
                        alias = Alias()
                        alias.item_id = item.id
                if alias:
                    depotitem = DepotItem.objects.filter(item_id=alias.item_id,depot_id=depot).first()
                    if depotitem:
                        if depotitem.position:
                            old_list =depotitem.position.split(',')
                            if row[2] not in old_list:
                                depotitem.position += ','+row[2]
                        else:
                            depotitem.position = row[2]
                        depotitem.save()
                        mag1 += u'SUCCESS,%s,%s |'%(row[1],depotitem.position)
                    else:
                        depotitem = DepotItem.objects.create(item_id=alias.item_id,depot_id=depot,position=row[2])
                        mag1 += u'SUCCESS,%s,%s |'%(row[1],depotitem.position)

                else:

                    mag1 += u'ERROR,%s,%s,alias not exist |'%(row[1],row[2])

            if mag1:
                #下载表格,错误提示
                response, writer = write_csv("import_depotitem_location_errors")
                writer.writerow(['库位导入信息反馈'])
                datas = mag1.split('|')
                for pd in datas:
                    writer.writerow([pd])
                return response

    return TemplateResponse(request,'import_depotitem_location.html',{'data':data})

@login_required
@permission_required('lib.bulk_print_barcode')
def bulk_print_barcode(request):
    data= {}
    if request.POST:
        if request.POST.get('type') == "bulk_print_barcode":
            reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
            head = next(reader)
            depotitem_id_list = []
            qty_list = []

            depot_id = request.POST.get('depot')
            wash_mark = request.POST.get('wash_mark', '0') or '0'
            e=''
            for sku, qty in reader:
                # print sku, qty
                try:
                    depotitem = DepotItem.objects.get(item__sku=sku.strip(), depot_id=depot_id)
                    qty = int(qty)
                    depotitem_id_list.append(str(depotitem.id))
                    qty_list.append(str(qty))
                except Exception, e:
                    print str(e)
            if e:
                messages.error(request, u'表格内容错误：%s'% e)
            else:
                path = "/tongguan/print_barcode/?depotitem_id=%s&qty=%s&wash_mark=%s" %(','.join(depotitem_id_list), ','.join(qty_list), wash_mark)
                return HttpResponseRedirect(path)

    return TemplateResponse(request,'bulk_print_barcode.html',{'data':data})

@login_required
@permission_required('lib.import_depotinlog')
def import_depotinlog(request):
    data= {}
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

    return TemplateResponse(request,'import_depotinlog.html',{'data':data})

@login_required
@permission_required('lib.import_depotoutlog')
def import_depotoutlog(request):
    data= {}
    if request.POST:
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

    return TemplateResponse(request,'import_depotoutlog.html',{'data':data})