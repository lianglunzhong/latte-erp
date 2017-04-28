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
from lib.iorder import import_order
from lib.models import Shipping, Country
from product.models import Product
from shipping.models import Package, PackageItem, NxbCode, ItemLocked, PackagePickError
from order.models import Channel, ChannelDepot, Alias, OrderItem
from depot.models import Depot, Pick, PickItem, DepotOutLog, DepotItem
from tongguan.models import Package3bao, Product3bao
from django.contrib.auth.decorators import login_required, permission_required


def handle(request):
    data = {}

    if request.POST.get('type') == 'orderitem_detail':

        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00+08:00")
            to_time = eparse(request.POST.get('to'), offset=" 00:00:00+08:00") or get_now()
        except Exception, e:
            messages.error(request, u'请输入正确的时间格式')
            return redirect('order_handle')
        shop = request.POST.get('shop')
        channel_id = request.POST.get('channel')

        response, writer = write_csv("order_cost")
        orderitem_detail(writer, from_time, to_time, shop, channel_id)
        return response

    elif request.POST.get("type") == 'order_cost':
        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00+08:00")
            to_time = eparse(request.POST.get('to'), offset=" 00:00:00+08:00") or get_now()
        except Exception, e:
            messages.error(request, u'请输入正确的时间格式%s' % str(e))
            return redirect('order_handle')

        shop = request.POST.get('shop')
        channel_id = request.POST.get('channel')

        response, writer = write_csv("order_cost")
        order_cost(writer, from_time, to_time, shop, channel_id)
        return response

    elif request.POST.get('type') == 'manual_import_order':
        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        try:
            channel = Channel.objects.get(id=request.POST.get('channel'))
        except Exception, e:
            messages.error(request, u"请选择正确的渠道账号")
            return redirect('order_handle')

        # 使用速卖通模板
        if channel.type == 2:
            header = next(reader)
            std_header = [
                "订单号", "买家邮箱", "产品总金额", "物流费用", "订单金额", "产品信息\n（双击单元格展开所有产品信息！）", "订单备注",
                "收货地址", "收货人名称", "收货国家", "州/省", "城市", "地址", "邮编", "联系电话", "手机", "买家选择物流",
            ]
            field_header = [
                "ordernum", 'email', 'amount_product', 'amount_shipping', "amount", "item_info", 'note', 'address',
                'shipping_firstname', 'country', 'shipping_state', 'shipping_city', 'shipping_address',
                'shipping_zipcode', 'phone', 'mobile', 'comment',
            ]

            # 由于bom头的问题, 就不比较第一列的header了
            if header[1:] != std_header[1:]:
                messages.error(request, u"请使用正确的模板, 并另存为utf-8格式")
                return redirect('order_handle')

            for i, row in enumerate(reader, 2):
                res = dict(zip(field_header, row))

                order_dict = {}
                order_dict['channel'] = channel
                order_dict['ordernum'] = res['ordernum']

                order_items = []
                items = res['item_info'].split('\n')
                item_num = len(items) / 4

                all_qty = 0
                for i in range(item_num):
                    all_qty += int(items[i * 4 + 3][14:-1].split(' ')[0])
                amount_product = float(row[2].strip().replace('$', ''))
                print all_qty
                if all_qty == 0:
                    msg += u'订单%s中产品总数为0, 请检查' % res['ordernum']
                    continue

                price = round(amount_product / all_qty, 2)

                for i in range(item_num):
                    attributes = items[i * 4 + 1][14:-1].split('、')
                    model = items[i * 4 + 2][14:-1]
                    qty = items[i * 4 + 3][14:-1].split(' ')[0]
                    size = "ONESIZE"
                    for attribute in attributes:
                        key, value = attribute.split(':')
                        if key == 'Size':
                            if value.upper() == 'FREE' or value.upper() == 'ONE SIZE':
                                size = 'ONESIZE'
                            else:
                                size = value
                    sku_items = []
                    sku_items.append(model)
                    sku_items.append(size)
                    sku = '-'.join([i for i in sku_items if i])
                    sku = sku.upper()

                    order_item = {
                        'sku': sku,
                        'qty': qty,
                        'price': price,
                    }
                    order_items.append(order_item)
                order_dict['order_items'] = order_items

                order_dict['add_user_id'] = request.user.id
                order_dict['email'] = res['email']
                order_dict['comment'] = res['comment']
                order_dict['note'] = res['note']
                order_dict['create_time'] = get_now()
                order_dict['import_type'] = 0

                order_dict['currency'] = 'USD'
                order_dict['amount'] = res['amount']
                order_dict['amount_shipping'] = res['amount_shipping']
                order_dict['shipping_type'] = 0 if order_dict['amount_shipping'] < 10 else 0

                order_dict['shipping_firstname'] = res['shipping_firstname']
                order_dict['shipping_address'] = res['shipping_address']
                order_dict['shipping_city'] = res['shipping_city']
                order_dict['shipping_state'] = res['shipping_state']
                try:
                    country = Country.objects.get(name=res['country'].strip())
                    order_dict['shipping_country_code'] = country.code
                except Exception, e:
                    order_dict['shipping_country_code'] = 'XX'
                order_dict['shipping_zipcode'] = res['shipping_zipcode']
                order_dict['shipping_phone'] = res['phone'] + "|" + res['mobile']
                order_dict['comment'] = res['comment']
                r = import_order(order_dict)

                if not r['success']:
                    msg += r['msg']

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'订单导入成功')
        return redirect('order_handle')

    data['shops'] = Channel.TYPE
    data['channels'] = Channel.objects.filter(deleted=False).values('id', 'name')
    return render(request, 'order_handle.html', data)


def orderitem_detail(writer, from_time, to_time, shop, channel_id):
    writer.writerow([
        '订单创建时间', "ordernum", "sku", "qty", "price", "currency", "shop", "category", "supplier",
        "supplier.assigner", "参考成本", "实际成本", "选款人ID", "create time", "model", "order_from"
    ])
    order_items = OrderItem.objects.filter(order__created__gte=from_time)\
                                   .filter(order__created__lte=to_time)\
                                   .exclude(order__status=7)\
                                   .exclude(deleted=True)\
                                   .select_related()

    if shop:
        order_items = order_items.filter(order__channel__type=shop)

    if channel_id:
        order_items = order_items.filter(order__channel_id=channel_id)

    for oi in order_items:
        order = oi.order
        item = oi.item
        if not item:
            continue

        supplier_product = item.product.get_default_supply_product()
        if not supplier_product:
            supplier = ''
            manager = ''
        else:
            supplier = supplier_product.supplier.name
            manager = supplier_product.supplier.manager

        channel_depot = ChannelDepot.objects.filter(channel=order.channel).order_by('order').first()
        depot_item = DepotItem.objects.filter(depot=channel_depot.depot, item=item).first()
        try:
            real_cost = round(depot_item.total / depot_item.qty, 2)
        except Exception, e:
            real_cost = 0

        row = [
            add8(order.created),
            order.ordernum,
            item.sku,
            oi.qty,
            oi.price,
            order.currency,
            eu(order.channel.get_type_display()),
            item.product.category.name,
            supplier,
            manager,
            item.cost or item.product.cost,
            real_cost,
            '',
            add8(order.create_time),
            item.product.sku,
            order.channel.name,
        ]
        writer.writerow(row)


def order_cost(writer, from_time, to_time, shop, channel_id):
    writer.writerow([
        "Shop", "Channel", "package id", "sku", "Ordernum", "Currency", "amount", "shipping amount", "参考cost",
        "实际cost", "shipping", "track no", "track price", "红人admin", "ship time", "订单日期", "Qty",
        "shipping label", "shipping country", "预分配物流商", "sku重量"
    ])

    package_items = PackageItem.objects.filter(package__order__created__gte=from_time)\
                                       .filter(package__order__created__lte=to_time)\
                                       .exclude(package__order__status=7)\
                                       .order_by("package__order__ordernum")\
                                       .select_related()

    if shop:
        package_items = package_items.filter(package__order__channel__type=shop)

    if channel_id:
        package_items = package_items.filter(package__order__channel_id=channel_id)

    exist_ordernum = set()
    exist_package_id = set()
    for pi in package_items:
        package = pi.package
        order = pi.package.order

        if order.ordernum in exist_ordernum:
            amount = ''
        else:
            amount = order.amount
            exist_ordernum.add(order.ordernum)

        shipping_name = (package.shipping and package.shipping.name) or ''
        forecast_shipping = (package.get_carrier() or "无法自动分配物流,需手工分配") if not shipping_name else ''

        if package.id in exist_package_id:
            package_total_cost = ""
        else:
            package_total_cost = package.cost + package.cost1
            exist_package_id.add(package.id)

        row = [
            eu(order.channel.get_type_display()),
            eu(order.channel.name),
            pi.package_id,
            pi.item.sku,
            '`' + order.ordernum,
            order.currency,
            amount,
            order.amount_shipping,
            pi.item.cost,
            pi.get_total(),
            eu(shipping_name),
            package.tracking_no,
            package_total_cost,
            '',
            add8(package.ship_time),
            add8(order.created),
            pi.qty,
            (package.shipping and package.shipping.label) or '',
            package.shipping_country.code,
            forecast_shipping,
            pi.qty * pi.item.weight,
        ]
        writer.writerow(row)
