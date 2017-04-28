# -*- coding: utf-8 -*-
import csv
import json
import datetime
import time
import re
import StringIO

from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Sum, Count
from django.contrib import messages

from lib.utils import pp, get_now, eu, write_csv, eparse, add8
from lib.models import Shipping, Country
from product.models import Product
from shipping.models import Package, PackageItem, NxbCode, ItemLocked, PackagePickError
from order.models import Channel, Alias, OrderItem
from depot.models import Depot, Pick, PickItem, DepotOutLog, DepotItem
from tongguan.models import Package3bao, Product3bao
from django.contrib.auth.decorators import login_required, permission_required


@login_required
@permission_required('lib.product_3bao')
def index(request):
    data = {}
    data['tracking_no_nums'] = NxbCode.objects.filter(is_used=0).count()
    return render(request, 'tongguan.html', data)

def product_3bao(request):
    if request.POST.get("type") == 'upload':
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)

        std_header = ["\xEF\xBB\xBFsku","hs_code","unit","f_model","status","cn_name"]
        field_header = ["sku", 'hs_code', 'unit', 'f_model',"status","cn_name"]

        # 由于bom头的问题, 就不比较第一列的header了
        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('tongguan_index')

        msg = ''
        for i, row in enumerate(reader, 2):
            res = dict(zip(field_header, row))

            # 先判断上传的sku的对应的产品
            item = Alias.objects.filter(sku__istartswith=res['sku']).first()
            if item:
                product = item.item.product
            else:
                product = Product.objects.filter(sku=res['sku']).first()

            if not product:
                msg += u"你上传的第%s行的sku: %s 无法找到对应的产品 | " % (i, res['sku'])
                continue

            # 再判断对应产品是否存在
            product_3bao = Product3bao.objects.filter(sku=product.sku).first()

            # 如果已经存在, 但3bao产品的sku来自别名, 那么说明这个sku是ws中的model, 需要将这个model保存
            if product_3bao and item:
                choies_models = product_3bao.choies_models.split(',')
                if res['sku'] not in choies_models:
                    choies_models.append(res['sku'])
                    product_3bao.choies_models = ','.join([i for i in choies_models if i])
                    product_3bao.save()
            else:
                # 3bao产品没有, 但是有product, 那么创建
                product_3bao = Product3bao()
                product_3bao.choies_models = res['sku']

            product_3bao.__dict__.update(res)
            product_3bao.product_id = product.id
            product_3bao.sku = product.sku
            product_3bao.save()
            print i

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'3bao产品操作成功')

    return redirect('tongguan_index')

def package_3bao(request):
    if request.POST.get("type") == 'upload_3bao_tonanjing':
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)

        std_header = ["\xEF\xBB\xBFpackage_id","is_tonanjing"]
        field_header = ["package_id", "is_tonanjing"]

        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('tongguan_index')

        msg = ''
        for i, row in enumerate(reader, 2):
            res = dict(zip(field_header, row))
            try:
                package_id = int(res['package_id'].strip())
                is_tonanjing = int(res['is_tonanjing'].strip())
            except Exception, e:
                msg += u"上传的第%s行的package_id%s和is_tonanjing不是正确的数字格式 |" % (i, res['package_id'])
                continue

            package = Package.objects.filter(id=package_id).first()
            if not package:
                msg += u"上传的第%s行的package_id: %s 对应的包裹不存在 |" % (i, res['package_id'])
                continue

            package3bao, flag = Package3bao.objects.get_or_create(package_id=package.id)
            # 当is_tonanjing发生改变, is_over就变成0
            if package3bao.is_tonanjing != is_tonanjing:
                package3bao.is_over = 0
            package3bao.is_tonanjing = is_tonanjing
            package3bao.save()

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'发往南京状态更新成功')

    elif request.POST.get("type") == 'upload_3bao_over':
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)

        std_header = ["package_id","is_over"]
        field_header = ["package_id", "is_over"]

        if header[1:] != std_header[1:]:
            messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
            return redirect('tongguan_index')

        msg = ''
        for i, row in enumerate(reader, 2):
            res = dict(zip(field_header, row))
            try:
                package_id = int(res['package_id'].strip())
                is_over = int(res['is_over'].strip())
            except Exception, e:
                msg += u"上传的第%s行的package_id%s和is_over不是正确的数字格式 |" % (i, res['package_id'])
                continue

            package = Package.objects.filter(id=package_id).first()
            if not package:
                msg += u"上传的第%s行的package_id: %s 对应的包裹不存在 |" % (i, res['package_id'])
                continue

            package3bao = Package3bao.objects.filter(package_id=package.id).first()
            # 当is_tonanjing为0时, 则不允许进行更新
            if not package3bao:
                msg += u"上传的第%s行的package_id: %s 对应的三宝Package不存在 |" % (i, res['package_id'])
                continue

            if not package3bao.is_tonanjing:
                msg += u"上传的第%s行的package_id: %s 对应的三宝package的发往南京状态为0 |" % (i, res['package_id'])
                continue

            package3bao.is_over = is_over
            package3bao.save()

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'海关审结状态更新成功')
    elif request.POST.get("type") == 'export_package3bao':
        response, writer = write_csv("package3bao")
        writer.writerow([
            'Package_id', 'Ordernum', 'Shipping', 'tracking_no', 'print_time',
            'is_tonanjing', 'is_over', 'remark',
        ])

        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00+08:00")
            to_time = eparse(request.POST.get('to'), offset=" 00:00:00+08:00") or get_now()
        except Exception, e:
            messages.error(request, u"请输入正确的时间格式")
            return redirect('tongguan_index')

        package3baos = Package3bao.objects.filter(package__print_time__gte=from_time)\
                                          .filter(package__print_time__lte=to_time)\
                                          .filter(is_tonanjing=1)
        for p in package3baos:
            row = [
                p.package_id,
                p.package.order.ordernum,
                p.package.shipping.label,
                add8(p.package.print_time),
                p.is_tonanjing,
                p.is_over,
                eu(p.remark),
            ]
            writer.writerow(row)
        return response

    return redirect('tongguan_index')

def k_tongguan(request):
    msg = ''
    if request.POST.get("type") == "tongguan_k_tongguan":
        carrier_style_codes = {
            "NXB": '3201985002',
            "EUB": '3201981289',
            "FEDEX": '3202382511',
        }
        response, writer = write_csv("k_tong_guan_order")
        writer.writerow([
            '原始订单编号', '进出口标志', '物流企业代码', '物流企业运单号', '订单商品货款', '订单商品运费', 
            '订单税款总额', '收货人名称', '收货人地址', '收货人电话', '收货人所在国家', '企业商品货号', 
            '商品数量', '计量单位', '币制代码', '商品总价', '新sku', 'ws_sku',
        ])
        package_ids = request.POST['package_ids'].strip().split('\r\n')
        carrier = request.POST.get('carrier', '').upper()
        for package_id in package_ids:
            package = Package.objects.filter(id=package_id).first()
            print package
            if not package:
                msg += u"Package:%s is not exist.|" %package_id
                continue

            order = package.order

            if package.status == 4:
                msg += u"Package:%s is not canceled.|" %package_id
                continue

            tongguan_info = order.cannot_tongguan()
            if tongguan_info:
                msg += u"Package:%s %s.|" %(package_id, tongguan_info)
                continue

            package_carrier = package.shipping and package.shipping.label.strip().upper()
            if  package_carrier!= carrier:
                msg += u'!!这条单号的物流不是%s,是%s,请注意维护!!|' %(carrier, package_carrier)
                continue

            carrier_code = carrier_style_codes.get(carrier, u"!!物流单号为空, 请注意维护!!")

            #金额分摊
            rate = order.rate if order.rate != 0 else 1
            order_amount = round(order.amount / rate , 2)
            order_amount_shipping = round(order.amount_shipping / rate , 2)

            # 将订单金额和orderitem的产品金额之差进行均摊, 如果产品金额为0, 则改为0.1
            # 表格的最小单位, 是packageitem, 但是相同model的packageitem需要进行合并
            # 解决思路, 制作一个model: price的dict

            order_items = OrderItem.objects.filter(order_id=order.id)\
                                           .exclude(qty=0)\
                                           .filter(deleted=False)\
                                           .values_list('item__product__sku', 'price', 'qty')

            # 因为要根据model进行合并, 因此认为相同model的金额是一样的, 并且取这个order中同model的最大price
            model_price = {}
            for model, price, qty in order_items:
                price = round((price or 0.1) / rate, 2)

                if model not in model_price:
                    model_price[model] = {
                        'price': price,
                        'qty': qty,
                    }
                else:
                    if model_price[model]['price'] < price:
                        model_price[model]['price'] = price
                    model_price[model]['qty'] += qty

            # 计算新的model下, order的产品金额
            order_product_amount = 0
            for model, data in model_price.iteritems():
                order_product_amount += data['price'] * data['qty']

            amount_delta = order_amount - order_product_amount

            # 将差值进行按比例均摊, 得出最终产品应该的价格
            finnal_model_price = {}
            for model, data in model_price.iteritems():
                finnal_model_price[model] = round((data['price'] / order_product_amount) * amount_delta + data['price'], 2)

            package_items = PackageItem.objects.filter(package=package).values_list('item__product__sku', 'qty')
            package_amount = 0
            package_models = {}
            for model, qty in package_items:
                model_amount = finnal_model_price[model] * qty
                if model not in package_models:
                    package_models[model] = {
                        'qty': qty,
                        'amount': model_amount,
                    }
                else:
                    package_models[model]['qty'] += qty
                    package_models[model]['amount'] += model_amount
                package_amount += model_amount

            for p_model, data in package_models.iteritems():
                p_3bao = Product3bao.objects.filter(sku=p_model).first()
                if not p_3bao:
                    unit_str = ''
                    choies_model = ''  # to delete暂时先使用旧的已备案model, 等新的sku备案完成, 再使用新的product的sku

                else:
                    choies_model = p_3bao.get_choies_model() # to delete 

                    unit_str = p_3bao.unit.split('/')
                    if unit_str:
                        unit_str = unit_str[0]
                    else:
                        unit_str = ''

                # 最后两列展示新的sku和旧的sku
                ws_alias = Alias.objects.filter(item__product__sku=p_model).first()
                if not ws_alias:
                    ws_sku = "这个是全新的产品"
                else:
                    ws_sku = ws_alias.sku


                row = [
                    package.id,
                    'E',
                    eu(carrier_code),
                    package.tracking_no,
                    round(package_amount, 2),
                    '0',
                    '0',
                    eu(package.get_name()),
                    eu(package.get_address()),
                    '`' + eu(package.shipping_phone),
                    package.shipping_country.number,
                    choies_model, # todo 新sku备案好后,更新为新的sku
                    data['qty'],
                    '`' + unit_str,
                    '502',
                    round(data['amount'], 2),
                    p_model,
                    ws_sku,
                ]
                writer.writerow(row)

        if msg:
            errors = msg.split('|')
            for err in errors:
                writer.writerow([eu(err)])

        return response
    elif request.POST.get("type") == "tongguan_export_product":
        # 如果产品没有3bao信息, 则在表格最后展示新, 旧sku
        response, writer = write_csv("tongguan_product")
        skus = request.POST['skus'].strip().split('\r\n')
        write_3bao_info(skus, writer)
        return response

    elif request.POST.get("type") == 'export_not_record_skus':
        response, writer = write_csv("not_record_skus")
        used_skus = set(OrderItem.objects.filter(order__channel__type=2).values_list('item__product__sku', flat=True).distinct())
        recorded_skus = set(Product3bao.objects.filter(status=1).values_list('sku', flat=True))
        no_record_skus = list(used_skus - recorded_skus)

        product3bao_no_record = Product3bao.objects.filter(status=0).values_list('sku', flat=True)
        no_record_skus2 = list(set(product3bao_no_record) - set(no_record_skus))[:3000]
        no_record_skus.extend(no_record_skus2)
        write_3bao_info(no_record_skus, writer)

        return response
    else:
        return redirect('tongguan_index')




def write_3bao_info(skus, writer):
    writer.writerow([
        '企业商品货号', 'ws_sku', '商品上架品名', '商品名称', '规格型号', '商品编码(HS编码)选填',
        '第一计量单位', '第二计量单位', '备案价格', '币制', '品牌', '海关行邮税编码', '产品链接'
    ])

    no_product = []
    no_3bao = []
    for sku in skus:
        p = Product.objects.filter(sku=sku).first()
        if not p:
            no_product.append(sku)
            continue

        p_3bao = Product3bao.objects.filter(sku=sku).first()
        if not p_3bao:
            no_3bao.append((sku, p.choies_sku))
            continue

        ws_alias = Alias.objects.filter(item__product_id=p.id).first()
        if not ws_alias:
            ws_sku = '新品, 只在ws中备案'
        else:
            ws_sku = ws_alias.sku

        units  = p_3bao.unit.strip().split('/')
        unit_1 = units[0]
        if len(units) > 1:
            unit_2 = units[1]
        else:
            unit_2 = ''

        if p.choies_site_url:
            item_link = p.choies_site_url
        elif p.get_image_thumb() != 'http://placehold.it/100x100':
            item_link = p.get_image_thumb()
        else:
            item_link =  ''

        row = [
            p_3bao.sku,
            ws_sku,
            eu(p.name),
            eu(p.cn_name),
            eu(p_3bao.f_model),
            p_3bao.hs_code,
            '`' + str(unit_1),
            '`' + str(unit_2),
            p.price,
            '502',
            'choies',
            '',
            item_link,
        ]
        writer.writerow(row)

    for i, k in no_3bao:
        writer.writerow([i, k, '这个sku没有传入3bao信息'])            

    for j in no_product:
        writer.writerow([j, '这个sku没有产品'])


def bulk_action(request):
    """批量操作"""
    msg = ""
    if request.method == "POST" and request.POST.get('type', '') == 'import_nxb_tracking_no':
        try:
            i = 0
            tracking_nos = request.POST.get('tracking_nos').strip().split('\r\n')
            for tracking_no in tracking_nos:
                try:
                    NxbCode.objects.create(code=tracking_no)
                    i += 1
                except Exception, e:
                    msg += u' | %s 已存在' % tracking_no
                    continue
        except Exception, e:
            msg += ' | ' + str(e)
        if not msg:
            messages.success(request, u'成功导入%s个运单号' % i)
        else:
            messages.error(request, (u'成功导入%s个运单号' % i) + msg)
    
    return redirect('tongguan_index')


def shouji(request):
    """收寄导出"""
    msg = ""
    package_ids = request.POST.get('package_id', '').strip().split("\r\n")

    if request.POST.get("type") == "nxb_pickup_export":
        response, writer = write_csv("nxb_pickup_export")
        writer.writerow(["邮件号码", "寄达局名称", "邮件重量", "单件重量", "寄达局邮编", "英文国家名",
                         "英文州名", "英文城市名", "收件人姓名", "收件人地址", "收件人电话", "寄件人姓名（英文）",
                         "寄件人省名（英文）", "寄件人城市名（英文）", "寄件人地址（英文）", "寄件人电话",
                         "内件类型代码", "内件名称", "内件英文名称", "内件数量", "单价", "产地"])

        for package_id in package_ids:
            p_3bao = Package3bao.objects.filter(package__status=5)\
                                        .filter(package__shipping__label='NXB')\
                                        .filter(package_id=package_id)\
                                        .first()
            if not p_3bao:
                msg += u"%s对应的Package或status不是已发货, 或不是NXB, 或不存在\n" % package_id
                continue

            package = p_3bao.package
            p_item = package.set_to_logistics()

            row = [
                eu(package.tracking_no),
                eu(package.shipping_country.cn_name),
                str(package.weight * 1000) + 'g',
                str(round(package.weight/package.qty, 3) * 1000) + 'g',
                '`' + package.shipping_zipcode,
                eu(package.shipping_country.name),
                eu(package.shipping_state),
                eu(package.shipping_city),
                eu(package.name),
                eu(package.address),
                format_shipping_phone(package.shipping_phone),
                "Wang Jian",
                "Nanjing",
                "Nanjing",
                "No.63 Longtan Logistics Park,Qixia District",
                "`442032899993",
                "1",
                eu(p_item.cn_name).replace('&', ' '),
                eu(p_item.name).replace('&', ' '),
                package.qty,
                "10",
                "cn",
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response
    elif request.POST.get("type") == "eub_pickup_export":
        response, writer = write_csv("eub_pickup_export")
        writer.writerow(["运单号", "订单号", "内件数", "客户代码", "客户姓名", "电话", "邮箱"])

        for package_id in package_ids:
            package = Package.objects.filter(id=package_id)\
                                     .filter(shipping__label='EUB')\
                                     .filter(status=5)\
                                     .first()
            if not package:
                msg += u"%s对应的Package或status不是已发货, 或不是EUB, 或不存在\n" % package_id
                continue

            package.set_to_logistics()

            row = [
                eu(package.tracking_no),
                package.id,
                package.qty,
                "C04",
                package.name,
                format_shipping_phone(package.shipping_phone),
                eu(package.email),
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response
    elif request.POST.get("type") == "eub_weight_pickup_export":
        response, writer = write_csv("eub_weight_pickup_export")
        writer.writerow(["邮件号", "收件人国家", "重量"])

        for package_id in package_ids:
            package = Package.objects.filter(id=package_id)\
                                     .filter(shipping__label='EUB')\
                                     .filter(status=5)\
                                     .first()
            if not package:
                msg += u"%s对应的Package或status不是已发货, 或不是EUB, 或不存在\n" % package_id
                continue

            row = [
                eu(package.tracking_no),
                package.shipping_country.code,
                package.get_weight(),
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response

    return redirect('tongguan_index')

def export_upload_format(request):
    """包裹上传格式导出"""
    msg = ""
    # 对输入的package_id 进行去重复
    package_ids_r = request.POST.get('package_id', '').strip().split("\r\n")
    package_ids = list(set(package_ids_r))
    package_ids.sort(key=package_ids_r.index)

    if request.POST.get("type") == "eub_format_export":
        response, writer = write_csv("eub_format_export")
        writer.writerow(["订单号", "商品交易号", "商品SKU", "数量", "收件人姓名（英文）",
                         "收件人地址1（英文）", "收件人地址2（英文）", "收件人地址3（英文）",
                         "收件人城市", "收件人州", "收件人邮编", "收件人国家", "收件人电话", 
                         "收件人电子邮箱"])

        for package_id in package_ids:
            package_items = PackageItem.objects.filter(package__status=3).filter(package_id=package_id)
            if not package_items:
                msg += u"%s对应的Package或status不是打包中, 或不存在或没有package产品\n" % package_id
                continue

            package = Package.objects.get(id=package_id)
            package.set_to_logistics()
            for pi in package_items:
                row = [
                    package.id,
                    '',
                    pi.item.sku,
                    pi.qty,
                    eu(package.name),
                    eu(package.address),
                    "",
                    "",
                    eu(package.shipping_city),
                    eu(package.shipping_state),
                    eu(package.shipping_zipcode),
                    eu(package.shipping_country.name),
                    format_shipping_phone(package.shipping_phone),
                    eu(package.email),
                ]
                writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response
    elif request.POST.get("type") == "sku_list":
        response, writer = write_csv("sku_list")
        writer.writerow(["SKU编号", "商品中文名称", "商品英文名称", "重量（3位小数）", "报关价格(整数)", "原寄地"])

        skus = PackageItem.objects.filter(package__status=3)\
                                  .filter(package_id__in=package_ids)\
                                  .values_list('item__sku', flat=True)\
                                  .distinct()
        for sku in skus:
            item = Item.objects.get(sku=sku)
            row = [
                sku,
                eu(item.category.cn_name),
                eu(item.category.name),
                item.weigth or item.product.weight,
                10,
                'CN',
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response

    elif request.POST.get("type") == "chukouyi_export":
        response, writer = write_csv("chukouyi_export")
        writer.writerow(['库存编码', '客户备注Custom', 'Remark', 'Tracking Number', 'Declared Name',
                         'Declared Value(USD)', 'Quantity', 'Weight', 'Packing', 'Name', 'Address Line1',
                         'Address Line2', 'Town/City', 'State/Province', 'Zip/Postal Code', 'Country',
                         'Phone Number', 'Email'])

        for package_id in package_ids:
            try:
                package = Package.objects.get(id=package_id)
            except Exception, e:
                msg += u"| package_id为 %s 不存在" % package_id
                continue
            packageitem = package.set_to_logistics()
            row = [
                '',
                '`' + str(package.id),
                '',
                '',
                packageitem.item.product.category.name,
                '10.00',
                '1',
                package.weight * 1000,
                '1*1*1',
                eu(package.name),
                eu(package.shipping_address),
                eu(package.shipping_address1),
                eu(package.shipping_city),
                eu(package.shipping_state),
                '`' + eu(package.shipping_zipcode),
                package.shipping_country.name,
                '`' + eu(package.shipping_phone),
                eu(package.email),
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response

    elif request.POST.get("type") == "hulianyi":
        response, writer = write_csv("hulianyi")
        writer.writerow(['客户单号', '运单号', '运输方式', '收件人', '收件人国家', '收件人邮编', '收件人地址',
                         '城市', '州/省', '收件人电话', '客户备注', '物品1', '中文品名1', '配货备注1', '净重1',
                         '价值1', '数量1'])
        shipping = request.POST.get('shipping', '1')
        ship_dict = {'1':'香港小包挂号', '2':'俄罗斯小包挂号', '3':'DHL小包挂号', '4':'新小包挂号',}

        for package_id in package_ids:
            try:
                package = Package.objects.get(id=package_id)
            except Exception, e:
                msg += u"| package_id为 %s 不存在" % package_id
                continue
            packageitem = package.set_to_logistics()
            row = [
                package_id,
                '',
                ship_dict[shipping],
                eu(package.name),
                eu(package.shipping_country.name),
                '`' + eu(package.shipping_zipcode),
                eu(package.address),
                eu(package.shipping_city),
                eu(package.shipping_state),
                '`' + eu(package.shipping_phone),
                eu(package.note),
                eu(packageitem.item.product.category.name),
                eu(packageitem.item.product.category.cn_name),
                '',
                package.weight,
                '10',
                package.qty,
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response

    elif request.POST.get('type') in ('sdhlws_shenbao_export', 'sfws_shenbao_export', 'donghang_shenbao_export'):
        filename = request.POST.get("type")[:-14] + 'export'
        response, writer = write_csv(filename)
        header = ['物流', 'Ordernum', 'Package ID', 'SKU', 'Qty', 'Total', 'product Name',
                  'Description', 'Description(中文)', 'Email', 'Phone Num', 'customer name',
                  'Shipping Address', 'Town/City', 'State/Province', 'Zip/Postal Code',
                  'Country Code', 'Country', 'Country(中文)', 'Shipping Amount', 'Weight',
                  'Note', 'Shop', 'Item URL']

        if request.POST['type'] == 'donghang_shenbao_export':
            header.append("comment")
        writer.writerow(header)

        not_exist_packages = []
        not_item_packages = []
        for package_id in package_ids:
            try:
                package = Package.objects.get(id=package_id)
            except Exception, e:
                not_exist_packages.append(package_id)
                continue

            packageitem = package.set_to_logistics()
            if not packageitem:
                not_item_packages.append(package_id)
                continue
            else:
                material = packageitem.item.product.material
                if material:
                    description = packageitem.name + '---' + material
                else:
                    description = packageitem.name

            row = [
                package.shipping.label,
                package.order.ordernum,
                package.id,
                packageitem.item.sku,
                package.qty,
                package.qty,
                packageitem.name,

                '',
                ship_dict[shipping],
                eu(package.name),
                eu(package.shipping_country.name),
                '`' + eu(package.shipping_zipcode),
                eu(package.address),
                eu(package.shipping_city),
                eu(package.shipping_state),
                '`' + eu(package.shipping_phone),
                eu(package.note),
                eu(packageitem.item.product.category.name),
                eu(packageitem.item.product.category.cn_name),
                '',
                package.weight,
                '10',
                package.qty,
            ]
            writer.writerow(row)
        if msg:
            messages.error(request, msg)
        else:
            return response




#处理字符串电话
def format_shipping_phone(shipping_phone):
    if shipping_phone:
        #将电话中的竖线替换成空格,去掉"+"  "/"
        shipping_phone = shipping_phone.encode('utf-8').replace('|', " ").replace("+","").replace("/","")
        #多个横线的只保留一个横线"-"
        shipping_phone = re.sub('-+','-',shipping_phone)
        shipping_phone = "`" + shipping_phone 
        return shipping_phone
    else:
        return ""


def print_barcode(request):
    """多个depotitem的id和qty之间用,链接
    url?package_id=1,2,3,4,5&qty=1,1,1,1&wash_mark=0
    """
    data = {}
    msg = ''
    try:
        depotitem_ids = [int(i.strip()) for i in request.GET.get('depotitem_id', '').split(',') if i]
        qty = [int(i.strip()) for i in request.GET.get('qty', '').split(',') if i]
        wash_mark = int(request.GET.get('wash_mark', '0'))
    except Exception, e:
        msg += u"请输入正确的depotitem的id和数量, %s |<br>" % str(e)
        return HttpResponse(msg)

    objs = []

    depotitems = zip(depotitem_ids, qty)
    for depotitem_id, qty in depotitems:
        depot_item = DepotItem.objects.filter(id=depotitem_id).first()
        if not depot_item:
            msg += u"这个depotitem ID: %s 不存在 |<br>" % depotitem_id
            continue

        for i in range(qty):
            obj = {
                'sku': depot_item.item.sku,
                'position': depot_item.position,
                'cn_name': depot_item.item.product.category.cn_name,
                'depot': depot_item.depot.get_code_display(),
                'id': depot_item.id,
                'print_time': get_now().strftime('%m-%d'),
            }
            if wash_mark:
                obj['wash_mark'] = True
                obj['kind'] = "Kind:" + depot_item.item.product.category.name
                obj['category'] = "Category:" + depot_item.item.product.category.get_root().name

                material = depot_item.item.product.material
                meterial_list = []

                init_x = 120
                init_y = 125

                for j in [material[i:i+13] for i in range(0, len(material), 13)]:
                    tempDict = {
                        "content": j,
                        "place_x": init_x,
                        "place_y": init_y,
                    }
                    init_x -= 8
                    init_y -= 8
                    meterial_list.append(tempDict)
                obj['material'] = meterial_list
                pp("Kind:" + depot_item.item.product.category.name)
                pp(obj)

            objs.append(obj)
    if msg:
        return HttpResponse(msg)

    data['objs'] = objs
    return render(request, 'print_barcode.html', data)
