# -*- coding: utf-8 -*-
from django.shortcuts import render,get_object_or_404,redirect
from django.template.response import TemplateResponse,HttpResponse
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
# Create your views here.

from project import settings as p_settings
from supply.models import Supplier,SupplierProduct,PurchaseOrderItem,PurchaseOrder
from django.views.generic import View
from django.http import JsonResponse
import json
import StringIO,csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from supply.forms import SupplyAddForm
from lib.utils import get_now
from depot.models import DepotInLog
from order.models import Channel, Order, OrderItem
from product.models import Item, Product, ProductImage
from fba.models import FbaSku, FbaStock, FbaForecast
from lib.utils import eparse, get_now

import datetime
import time
from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

def index(request):
    context = {}
    fba_channels = Channel.objects.filter(is_fba=True)
    context['fba_channels'] = fba_channels
    return TemplateResponse(request, 'fba_index.html', context)

def import_data(request):
    data = {}
    # 导入fba sku对照表
    if 'type' in request.POST and request.POST['type'] == 'fba_sku':
        datas = request.FILES['csvFile']
        csvdata = StringIO.StringIO(datas.read())
        reader = csv.reader(csvdata)
        next(reader)
        msg = ''
        for row in reader:
            fba_sku = row[0].strip()
            fn_sku = row[1].strip()
            sku = row[2].strip()
            title = row[3].strip()
            if not fn_sku or not sku:
                continue
            try:
                item = Item.objects.get(sku=sku)
                FbaSku.objects.create(fba_sku=fba_sku, fn_sku=fn_sku, sku=sku, item=item, title=title)
            except Item.DoesNotExist:
                msg += 'sku:%s不存在\n' % sku
        if msg:
            msg = '上传成功\n报错:\n' + msg
        else:
            msg = '上传成功'
        return HttpResponse(msg)
    #导入fba库存
    elif 'type' in request.POST and request.POST['type'] == 'fba_stock':
        datas = request.FILES['csvFile']
        csvdata = StringIO.StringIO(datas.read())
        reader = csv.reader(csvdata)
        next(reader)
        msg = ''
        successed = 0
        errored = 0
        for row in reader:
            channel_name = row[0].strip()
            try:
               channel_obj = Channel.objects.get(name=channel_name)
            except Channel.DoesNotExist:
                msg += '渠道"%s"不存在\n' % channel_name
                errored += 1
                continue
            sku = row[1].strip()
            try:
                item_obj = Item.objects.get(sku=sku)
            except Product.DoesNotExist:
                msg += 'SKU"%s"不存在<br>' % sku
                errored += 1
                continue
            warehouse = int(row[2].strip())
            fulfillable = int(row[3].strip())
            unsellable = int(row[4].strip())
            reserved = int(row[5].strip())
            inboud = int(row[6].strip())
            total = int(row[6].strip())
            FbaStock.objects.create(
                channel=channel_obj, item=item_obj, warehouse=warehouse, fulfillable=fulfillable,
                unsellable=unsellable, reserved=reserved, inboud=inboud, total=total
            )
            successed += 1
        response = '%d条数据上传成功<br>%d条数据报错:<br>%s' % (successed, errored, msg)
        return HttpResponse(response)

# FBA预测囤货
def forecast(request):
    if request.method == 'POST':
        data = {}
        data['msg'] = ''
        order_status = [1,3,4,5,6]
        if 'channel' in request.POST and request.POST['channel']:
            channels = request.POST.getlist('channel')
            now = get_now()
            last_order = Order.objects.filter(deleted=False)\
                .filter(channel_id__in=channels).filter(status__in=order_status)\
                .filter(is_fba=True).order_by('-create_time')[:1].values('create_time')
            for l_o in last_order:
                now = l_o['create_time']
            date7 = 7
            sale_date7 = now - datetime.timedelta(days=date7)
            # 根据传递的渠道进行分别的生成
            for channel in channels:
                #先删除该channel下旧的数据
                channel = int(channel)
                FbaForecast.objects.filter(deleted=False).filter(channel_id=channel).filter(is_purchase=False).delete()

                # 选出某个商店最近7天的所有orderitem
                orderitems = OrderItem.objects.filter(deleted=False)\
                    .filter(order__status__in=order_status)\
                    .filter(order__channel_id=channel)\
                    .filter(order__create_time__gte=sale_date7)\
                    .filter(order__is_fba=True)\
                    .values('qty', 'sku', 'item_id')
                fore_dic = {}
                # 这个循环计算出这个channel不同时间段的销售量: 7天
                for orderitem in orderitems:
                    sku = orderitem['sku']
                    try:
                        if orderitem['item_id'] not in fore_dic:
                            fore_dic[orderitem['item_id']] = {'sales7': 0}
                        fore_dic[orderitem['item_id']]['sales7'] += orderitem['qty']
                    except:
                        data['msg'] += 'Item:%s Not Found | ' % sku

                # 这个循环生成新的预测囤货信息
                itemids = fore_dic.keys()
                itemobjs = Item.objects.filter(id__in=itemids).values('id', 'sku', 'product_id')
                for itemobj in itemobjs:
                    foredata = fore_dic[itemobj['id']]
                    # try:
                        # 可用库存,当前库存
                    try:
                        fba_stock = FbaSku.objects.get(item_id=itemobj['id'])
                        can_stock = fba_stock.fulfillable #可用库存
                        now_stock = fba_stock.total - fba_stock.unsellable #当前库存
                    except FbaSku.DoesNotExist:
                        can_stock = 0
                        now_stock = 0

                    # 区分“做货产品”和“采购产品”
                    supplier_product = SupplierProduct.objects.filter(product_id=itemobj['product_id']).order_by('order')[:1].values('id', 'supplier__type')
                    supplier_type = 0
                    for s_product in supplier_product:
                        supplier_type = s_product['supplier__type']
                    if supplier_type == 2:
                        forecast_type = '做货产品'
                        is_made = True
                    else:
                        forecast_type = '采购产品'
                        is_made = False

                    # 囤货产品类型
                    if can_stock == 0:
                        has_stock = False
                        forecast_type = '断货' + forecast_type
                    else:
                        has_stock = True
                        forecast_type = '有货' + forecast_type

                    # 7天销量
                    sales_7 = foredata['sales7']

                    # 安全库存
                    if is_made:
                        safe_stock = sales_7 * 6
                    else:
                        safe_stock = sales_7 * 4

                    # 采购中的数量
                    purchase_item_qty = 0
                    qty = PurchaseOrderItem.objects.filter(status__in=[0, 3]).filter(item_id=itemobj['id']).filter(purchaseorder__status__in=[0,1]).aggregate(Sum('qty'))
                    real_qty = PurchaseOrderItem.objects.filter(status=3).filter(item_id=itemobj['id']).filter(purchaseorder__status__in=[0,1]).aggregate(Sum('real_qty'))
                    if real_qty['real_qty__sum']:
                        partial_real_qty = real_qty['real_qty__sum']
                    else:
                        partial_real_qty = 0

                    if qty['qty__sum']:
                        purchase_item_qty = qty['qty__sum'] - partial_real_qty
                    else:
                        purchase_item_qty = 0 - partial_real_qty
                    
                    #预测囤货数量(建议采购数量)
                    if not has_stock and not is_made: # 断货采购产品
                        fore_qty = sales_7 * 4 - purchase_item_qty
                    elif not has_stock and is_made: # 断货做货产品
                        fore_qty = sales_7 * 6 - purchase_item_qty
                    elif has_stock and not is_made: # 有货采购产品
                        fore_qty = sales_7 * 4 - purchase_item_qty
                    elif has_stock and not is_made: # 有货做货产品
                        fore_qty = sales_7 * 6 - purchase_item_qty

                    # 创建预测囤货数据
                    forecast = FbaForecast()
                    forecast.channel_id = channel
                    forecast.item_id = itemobj['id']
                    forecast.forecast_type = forecast_type
                    forecast.sales_7 = sales_7
                    forecast.can_stock = can_stock
                    forecast.now_stock = now_stock
                    forecast.safe_stock = safe_stock
                    forecast.purchase_item_qty = purchase_item_qty
                    forecast.fore_qty = fore_qty
                    forecast.assigner_id = request.user.id
                    forecast.save()

                    # except Exception, e:
                    #     data['msg'] += str(e) + ' | '
            # 新增产品
            if 'skus' in request.POST and request.POST['skus']:
                skus = request.POST['skus'].strip().split('\r\n')
                do_skus = []
                for sku in skus:
                    try:
                        fba_sku = FbaSku.objects.get(sku=sku)
                        data['msg'] += '%s在对照表中已存在' % sku
                    except FbaSku.DoesNotExist:
                        do_skus.append(sku)
                if len(do_skus) > 0:
                    last_order = OrderItem.objects.filter(sku__in=do_skus).filter(order__channel_id__in=channels).filter(order__is_fba=False).order_by('-create_time')[:1].get()
                    now = last_order.order.create_time
                    date7 = 7
                    sale_date7 = now - datetime.timedelta(days=date7)
                    # 根据传递的渠道进行分别的生成
                    for channel in channels:
                        channel = int(channel)
                        # 选出某个商店最近7天的所有orderitem
                        orderitems = OrderItem.objects.filter(status=True)\
                            .exclude(order__status=6)\
                            .filter(sku__in=do_skus)\
                            .filter(order__channel_id=channel)\
                            .filter(order__created__gte=sale_date7)\
                            .filter(order__is_fba=False)\
                            .values('order__created', 'qty', 'sku')
                        fore_dic = {}
                        # 这个循环计算出这个channel不同时间段的销售量: 7天
                        sku_lists = tuple(orderitems.values_list('sku', flat=True))
                        sku_id_dict = dict(Item.objects.filter(sku__in=sku_lists).values_list('sku', 'id'))
                        for orderitem in orderitems:
                            sku = orderitem['sku']
                            try:
                                item_id = sku_id_dict[sku]
                                if item_id not in fore_dic:
                                    fore_dic[item_id] = {'sales7': 0}
                                fore_dic[item_id]['sales7'] += orderitem['qty']
                            except:
                                data['msg'] += 'Item:%s Not Found | ' % sku

                        # 这个循环生成新的预测囤货信息
                        itemids = fore_dic.keys()
                        itemobjs = Item.objects.filter(id__in=itemids).values('id', 'sku', 'product_id')
                        for itemobj in itemobjs:
                            foredata = fore_dic[itemobj['id']]
                            try:
                                # 可用库存,当前库存
                                try:
                                    fba_stock = FbaSku.objects.get(item_id=itemobj['id'])
                                    can_stock = fba_stock.fulfillable #可用库存
                                    now_stock = fba_stock.total - fba_stock.unsellable #当前库存
                                except FbaSku.DoesNotExist:
                                    can_stock = 0
                                    now_stock = 0

                                # 区分“做货产品”和“采购产品”
                                supplier_product = SupplierProduct.objects.filter(product_id=itemobj['product_id']).order_by('order').values['supplier__type'][:1].get()
                                if supplier_product['supplier__type'] == 2:
                                    forecast_title = '新增做货产品'
                                    is_made = True
                                else:
                                    forecast_title = '新增采购产品'
                                    is_made = False

                                # 7天销量
                                sales_7 = foredata['sales7']

                                # 安全库存
                                if is_made:
                                    safe_stock = sales_7 * 7
                                else:
                                    safe_stock = sales_7 * 5

                                # 采购中的数量
                                purchase_item_qty = Item.objects.get(id=itemobj['id']).get_purchasing_qty()
                                
                                #预测囤货数量(建议采购数量)
                                if not is_made: # 断货采购产品
                                    fore_qty = sales_7 * 5
                                else: # 断货做货产品
                                    fore_qty = sales_7 * 7
                                # 创建预测囤货数据
                                forecast = FbaForecast()
                                forecast.channel_id = channel
                                forecast.item_id = itemobj['id']
                                forecast.forecast_type = forecast_type
                                forecast.sales_7 = sales_7
                                forecast.can_stock = can_stock
                                forecast.now_stock = now_stock
                                forecast.safe_stock = safe_stock
                                forecast.purchase_item_qty = purchase_item_qty
                                forecast.fore_qty = fore_qty
                                forecast.assigner_id = request.user.id
                                forecast.save()

                            except Exception, e:
                                data['msg'] += str(e) + ' | '
            response = 'SUCCESS! <a href="/fba/forecast">进入预测囤货列表页面</a><br>'
            if data['msg'] != '':
                response = '报错信息:<br>%s' % (data['msg'])
            return HttpResponse(response)

    #囤货界面
    context = {}
    search = request.GET.get('search')
    if not search:
        search = ''
    context['search'] = search
    
    if 'type' in request.GET and request.GET['type'] and request.GET['type']=='do_search':#search
        obj_list = FbaForecast.objects
        if request.GET['channel'] or request.GET['sku'] or request.GET['created_from'] or request.GET['is_real_qty'] or request.GET['is_purchase']:
            if request.GET['channel']:
                channel = request.GET['channel'].strip()
                obj_list = obj_list.filter(channel_id=channel)
            if request.GET['sku']:
                sku = request.GET['sku'].strip()
                obj_list = obj_list.filter(item__sku__contains=sku)
            if request.GET['is_real_qty']:
                is_real_qty = int(request.GET['is_real_qty'].strip())
                if is_real_qty == 0:
                    obj_list = obj_list.filter(real_qty=0)
                else:
                    obj_list = obj_list.filter(real_qty__gt=0)
            if request.GET['is_purchase']:
                is_purchase = int(request.GET['is_purchase'].strip())
                obj_list = obj_list.filter(is_purchase=is_purchase)
            if request.GET['created_from'] and request.GET['created_to']:
                try:
                    time.strptime(request.GET['created_from'],"%Y-%m-%d")
                    time.strptime(request.GET['created_to'],"%Y-%m-%d")
                except Exception, e:
                    return HttpResponse('请检查时间格式!')

                date_from = request.GET['created_from']
                date_to = request.GET['created_to']
                obj_list = obj_list.filter(created__gte=date_from).filter(created__lte=date_to)
            elif request.GET['created_from']:
                try:
                    time.strptime(request.POST['created_from'],"%Y-%m-%d")
                except Exception, e:
                    return HttpResponse('请检查时间格式!')
                date_from = request.GET['created_from']
                date_to = datetime.datetime.strptime(date_from, "%Y-%m-%d") + datetime.timedelta(days=1)
                date_to = str(date_to)
                obj_list = obj_list.filter(created__gte=date_from).filter(created__lte=date_to)

        if request.GET['per_num']:
            per_num = request.GET['per_num']
        obj_list = obj_list.all().order_by('-sales_7')
    elif 'type' in request.GET and request.GET['type'] and request.GET['type']=='forecastviews_export':
        return forecastviewsExport(request)
    else:
        obj_list = FbaForecast.objects.filter(deleted=0,assigner_id=request.user.id).order_by('-sales_7')
    
    paginator = Paginator(obj_list, 10)
    page_want = request.GET.get('p')
    try:
        page_info = paginator.page(page_want)
    except PageNotAnInteger:
        page_info = paginator.page(1)
    except EmptyPage:
        page_info = paginator.page(paginator.num_pages)

    for p in page_info:
        try:
            fba_sku = FbaSku.objects.get(item=p.item)
            p.fn_sku = fba_sku.fn_sku
        except FbaSku.DoesNotExist:
            p.fn_sku = ''
        product_image = ProductImage.objects.filter(product=p.item.product)[:1].values('image')
        if len(product_image) > 0:
            for p_image in product_image:
                p.product_image = p_image['image']
        else:
            p.product_image = ''
    context['gets'] = request.GET
    context['info'] = page_info
    fba_channels = Channel.objects.filter(is_fba=True)
    context['fba_channels'] = fba_channels

    return TemplateResponse(request,'fba_forecast.html',context)

@csrf_exempt
def ajax_process(request):
    data = {}
    if 'type' in request.POST and request.POST['type'] == 'forecast_enter_qty':
        if 'id' in request.POST and request.POST['id'] and 'qty' in request.POST and request.POST['qty']:
            forecast_id = int(request.POST['id'])
            enter_qty = int(request.POST['qty'])
            try:
                forecast = FbaForecast.objects.get(id=forecast_id)
                if enter_qty > 0:
                    forecast.real_qty = enter_qty
                    forecast.assigner = request.user
                    forecast.save()
                    data['success'] = 1
                    data['assigner'] = request.user.username
                else:
                    data['success'] = 0
                    data['msg'] = '囤货数量必须大于零!'
            except Forecast.DoesNotExist:
                data['success'] = 0
                data['msg'] = 'Forecast ID: %s Not Found!' % str(forecast_id)
        else:
            data['success'] = 0
            data['msg'] = '数量必填!'
    elif 'type' in request.POST and request.POST['type'] == 'delete':
        if 'fore_ids' in request.POST and request.POST['fore_ids']:
            data['ids'] = []
            data['msg'] = ''
            fore_ids = request.POST['fore_ids'].strip().split(',')
            for fore_id in fore_ids:
                if len(fore_id) == 0:
                    continue
                fore_id = int(fore_id)
                try:
                    forecast = Forecast.objects.get(id=fore_id)
                    if not forecast.is_purchase:
                        data['ids'].append(fore_id)
                        forecast.delete()
                    else:
                        data['msg'] += u'Forecast ID: %d 已经生成采购单,不哪能删除! | ' % fore_id
                except Forecast.DoesNotExist:
                    data['msg'] += 'Forecast ID: %s Not Found!' % str(fore_id)

            if data['msg'] == '':
                data['success'] = 1
            else:
                data['success'] = 0
        else:
            data['success'] = 0
            data['msg'] = 'ID必填!'
    elif 'type' in request.POST and request.POST['type'] == 'ajax_item':
        if 'model' in request.POST and request.POST['model']:
            model = request.POST['model']
            try:
                skus = []
                items = Item.objects.filter(model=model)
                for item in items:
                    skus.append(item.sku)
                if len(skus) == 0:
                    data['success'] = 0
                    data['msg'] = 'model不存在'
                else:
                    data['success'] = 1
                    data['skus'] = skus
            except:
                data['success'] = 0
                data['msg'] = 'model不存在'
        else:
            data['success'] = 0
            data['msg'] = 'model必填!'

    return HttpResponse(json.dumps(data), content_type='application/json')

@login_required
def forecastviewsExport(request):

    oneMothAgo = datetime.datetime.now() - datetime.timedelta(days=30)
    nowTime = datetime.datetime.now()

    try:
        time.strptime(request.GET.get("from"), "%Y-%m-%d")
        fromTime = request.GET.get("from")
    except:
        fromTime = oneMothAgo

    try:
        time.strptime(request.GET.get("to"), "%Y-%m-%d")
        toTime = request.GET.get("to")
    except:
        toTime = nowTime
    forecasts = FbaForecast.objects.filter(created__gte=fromTime).filter(created__lte=toTime)
    if request.GET.get('channel', ''):
        forecasts = forecasts.filter(channel_id=request.GET['channel'])

    #  response 头
    response = HttpResponse(content_type='text/csv')
    response.write('\xEF\xBB\xBF')
    response['Content-Disposition'] = 'attachment; filename="forecast_export.csv"'
    writer = csv.writer(response)
    writer.writerow(["ID", "Create time", "Sku", "channel", "囤货人", "7天总销量", "7天日均销量", "趋势状态",
                     "库存数量", "库存天数", "采购中数量", "采购前置天数", "安全库存",
                     "预测囤货量(Y天)", "实际囤货量", "是否生成采购单"])

    for forecast in forecasts:
        rowList = []
        try:
            username = forecast.assigner.username.encode("utf-8")
        except:
            username = ""

        # 14天日均销量
        sales_average_7 = round(float(forecast.sales_7)/7, 2)
        # 库存天数
        stock_day = round(float(forecast.item.qty)/sales_average_7, 2) if sales_average_7 else 0.0
        is_purchase = "是" if forecast.is_purchase else ""


        rowList.append(forecast.id)
        rowList.append(forecast.created)
        rowList.append(forecast.item.sku)
        rowList.append(forecast.channel.name)
        rowList.append(username)
        rowList.append(forecast.sales_7)
        rowList.append(sales_average_7)
        rowList.append(forecast.get_sales_trend_display().encode("utf-8"))
        rowList.append(forecast.stock)
        rowList.append(stock_day)
        rowList.append(forecast.purchase_item_qty)
        rowList.append(forecast.item.purchase_period)
        rowList.append(forecast.safe_stock)
        rowList.append(forecast.fore_qty)
        rowList.append(forecast.real_qty)
        rowList.append(is_purchase)
        writer.writerow(rowList)
    return response
