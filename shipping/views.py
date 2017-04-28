# -*- coding: utf-8 -*-
import json
import time
import csv
import StringIO

from django.shortcuts import render, get_object_or_404, redirect
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.template.response import TemplateResponse, HttpResponse
from django.core.urlresolvers import reverse
from django.db.models import Sum, Count
from django.contrib.contenttypes.models import ContentType
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import View
from django.http import JsonResponse, HttpResponseRedirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required

from lib.utils import pp, get_now, eu, write_csv, eparse
from lib.models import Shipping
from shipping.models import Package, PackageItem, NxbCode, ItemLocked, PackagePickError
from order.models import Channel, Alias
from depot.models import Depot, Pick, PickItem, DepotOutLog

from logistics.logistics import verify_can_shipping, logistics_tracking_no, ShippingList
from logistics.labels import get_label_data, get_pdf_label


@login_required
@permission_required('lib.pick_index')
def index(request):
    data = {}
    msg = ''
    if request.method == 'GET' and request.GET.get('type') == 'count_data':
        data = {
            "ready_from_shipping": 0,
            "assign_shipping": 0,
            "get_tracking_no": 0,
            "no_api_shipping": 0,
            "create_pick": 0,
            "pick_count": 0,
            "pick_no_assigner": 0,
            "dandan": 0,
            "danduo": 0,
            "duoduo": 0,
            "packaging": 0,
            "set_shipping": 0,
            "abnormal_package": 0,
        }

        packages = Package.objects.filter(status__in=[2, 3])\
                                  .values_list('shipping__label', 'status', 'tracking_no', 'pick_status')
        for shipping_label, status, tracking_no, pick_status in packages:
            if status == 2:
                data['ready_from_shipping'] += 1  # 配货中的数量(还未生成拣货单)
                if not tracking_no:
                    if not shipping_label:
                        data['assign_shipping'] += 1  # 需要分配物流方式的(锁完, 但是没有物流方式, 没有运单号)
                    else:
                        if shipping_label in ShippingList.have_api_shipping:
                            data['get_tracking_no'] += 1  # 自动物流商下单(锁完, 有物流方式, 但没有运单号)
                        else:
                            data['no_api_shipping'] += 1  # 无物流api单独发货
                else:
                    data['create_pick'] += 1  # 有运单号, 状态是2 默认: 一定先有物流方式, 才会再有运单号
            elif status == 3 and pick_status == 3:  # 包装完成, 但是还没有发货的
                data['set_shipping'] += 1  # 执行发货

        picks = Pick.objects.exclude(status=5)\
                            .values_list('printer', 'pick_type', 'status', 'assigner')
        for printer, pick_type, status, assigner in picks:
            if not printer:
                data['pick_count'] += 1  # 未打印拣货单
            elif not assigner:
                data['pick_no_assigner'] += 1  # 未拣货的拣货单

            elif status in (0, 1, 2):  # 限定未包装完成
                if pick_type == 1:
                    data['dandan'] += 1
                elif pick_type == 2:
                    data['danduo'] += 1
                elif pick_type == 3 and status != 2:
                    data['duoduo'] += 1
                elif pick_type == 3 and status == 2:
                    data['packaging'] += 1
        data['abnormal_package'] = PackagePickError.objects.filter(is_processed=False).count()
        # 默认展示的每中类型的包裹的数量
        return HttpResponse(json.dumps(data))

    elif request.POST.get("type") == "deliver_package_export":
        try:
            from_time = eparse(request.POST.get('from'), offset=" 00:00:00+08:00")
            to_time = eparse(request.POST.get('to'), offset=" 00:00:00+08:00") or get_now()
        except Exception, e:
            print str(e)

        packages = Package.objects.filter(ship_time__gte=from_time)\
                                  .filter(ship_time__lte=to_time)\
                                  .filter(status__in=(5, 6, 7))
        response, writer = write_csv('deliver_package_export')
        writer.writerow(["ship time", "package id", "shop", "ordernum", "订单创建时间",
                         "shipping", "trackno", "print time", "printer", "shipper",
                         "可否通关", "to_nanjing", "产品总数", "Items"])
        package_ids = [i.id for i in packages]
        packageitems = PackageItem.objects.filter(package_id__in=package_ids)\
                                          .values_list('package_id', 'item__sku', 'qty')
        # 生成每个package对应的package_items信息, 这样会快很多
        p_items = {}
        for package_id, sku, qty in packageitems:
            if package_id not in p_items:
                p_items[package_id] = {
                    "total_qty": qty,
                    "item_info": ["%s:%s" % (sku, qty), ]
                }
            else:
                p_items[package_id]['total_qty'] += qty
                p_items[package_id]['item_info'].append("%s:%s" % (sku, qty))

        for package in packages:
            p_item = p_items.get(package.id, {})
            row = [
                package.ship_time,
                package.id,
                eu(package.order.channel.get_type_display()),
                package.order.ordernum,
                package.order.created,
                (package.shipping and package.shipping.label) or '',
                package.tracking_no,
                package.print_time,
                (package.printer and package.printer.username) or '',
                (package.shipper and package.shipper.username) or '',
                eu(package.order.cannot_tongguan() or u"可以"),
                '否',  # todo package3bao的tonanjing
                p_item.get('total_qty', 0),
                ';'.join(p_item.get('item_info')),
            ]
            writer.writerow(row)
        return response
    data['title'] = u'分拣首页'
    return render(request, 'pick_index.html', data)


@login_required
@permission_required('lib.pick_assign_shipping')
def assign_shipping(request, assign_parm):
    """分配物流方式
    分配物流方式只有三种方式
    第一种:使用 自动分配物流
    第二种:手动分配物流
    第三种:更换物流商打印面单
    """
    if assign_parm == 'manual':
        data = {}
        packages = Package.objects.filter(status=2)\
                                  .filter(shipping__isnull=True)\
                                  .filter(tracking_no='')

        if request.GET.get('type') == 'do_search':
            if request.GET.get('shop'):
                packages = packages.filter(order__channel__type=request.GET.get('shop'))
            if request.GET.get('shipping_type'):
                packages = packages.filter(order__shipping_type=request.GET.get('shipping_type'))
            if request.GET.get('tongguan') == '1':
                packages = [i for i in packages if not i.order.cannot_tongguan()]
            elif request.GET.get('tongguan') == '0':
                packages = [i for i in packages if i.order.cannot_tongguan()]

        data['shops'] = Channel.TYPE
        data['shippings'] = Shipping.objects.all()
        data['objs'] = packages
        data['gets'] = request.GET
        return render(request, 'hand_assign_shipping.html', data)
    elif assign_parm == 'manual_assign_shipping':
        result = {'success': True, 'msg': '', }
        try:
            package = Package.objects.get(id=request.GET['package_id'])
            shipping = Shipping.objects.get(id=request.GET['shipping_id'])
            package.option_log += u'\n%s在%s通过 手动 将物流方式改为了%s, 原来为%s' % (request.user.username, get_now(), shipping, package.shipping)
            package.shipping_id = shipping.id
            package.save()
        except Exception, e:
            result['success'] = False
            result['msg'] += str(e)
        return HttpResponse(json.dumps(result))
    elif assign_parm == 'auto':
        msg = ''
        success = 0
        failure = 0
        packages = Package.objects.filter(shipping__isnull=True)\
                                  .filter(status=2)     # package状态为2, 即已经锁完

        for package in packages:
            carrier = package.get_carrier()
            if carrier:
                shipping = Shipping.objects.filter(label=carrier).first()
                if not shipping:
                    msg += u'%s 对应的shipping还没有创建 |' % carrier
                    continue
                package.shipping = shipping
                package.option_log += u'\n%s在%s 通过 自动分配物流 分配了物流方式%s' % (request.user.username, get_now(), shipping.label)
                package.save()
                success += 1
            else:
                failure += 1
        msg += u'success:%s, failure:%s' % (success, failure)
        messages.info(request, msg)
    return redirect('pick_index')


@login_required
@permission_required('lib.pick_get_tracking_no')
def get_tracking_no(request):
    """物流商下单"""
    data = {}

    base_packages = Package.objects.filter(status=2)\
                                   .filter(shipping__isnull=False)\
                                   .filter(tracking_no='')\
                                   .filter(shipping__label__in=ShippingList.have_api_shipping)

    if request.method == 'POST' and request.POST.get('shipping_label', ''):
        response = ''
        shipping_labels = request.POST.getlist('shipping_label')
        for shipping_label in shipping_labels:
            success = 0
            msg = ''
            packages = base_packages.filter(shipping__label=shipping_label)

            for package in packages:
                # 校验package是否能进行物流商下单
                can_shipping = verify_can_shipping(package)
                if not can_shipping['success']:
                    msg += u'<br>%s : %s' % (package.id, can_shipping['msg'])
                    continue

                # 物流商下单
                result = logistics_tracking_no(package)
                if result['success']:
                    # todo 记录谁在什么时候分配的运单号
                    package.tracking_no = result['tracking_no']
                    package.option_log += u'\n%s %s %s' % (request.user.username, get_now(), result['tracking_no'])
                    package.save()
                    success += 1
                else:
                    msg += u'<br>%s-%s : %s' % (shipping_label, package.id, result['msg'])

            info = u'<br><br>%s成功数: %s <br> ' % (shipping_label, success)
            if msg:
                response += info + u'以下package失败 %s' % msg
            else:
                response += info

        return HttpResponse(response)

    shipping_counts = base_packages.values('shipping__label').annotate(Count('id'))

    data['shipping_counts'] = shipping_counts
    data['shipping_list'] = ShippingList.all_list
    data['title'] = u'物流商下单'
    return render(request, 'get_tracking_no.html', data)


@login_required
def manual_deliver(request):
    """手动发货--无物流api的package"""
    data = {}
    objs = Package.objects.filter(status=2)\
                          .filter(shipping__isnull=False)\
                          .filter(tracking_no='')\
                          .exclude(shipping__label__in=ShippingList.have_api_shipping)\
                          .order_by('-id')
    if request.POST.get("type") == "print_deliver":
        response, writer = write_csv('print_package')
        writer.writerow(["Ordernum","Pacakge ID","SKU","Qty","Total","product Name","Description",
                         "Description(中文)","Email","Phone Num","customer name","Shipping Address",
                         "Town/City","State/Province","Zip/Postal Code","Country Code","Country",
                         "Country(中文)","Shipping Amount","Weight","Note","Shop","Item URL",
                         "celebrity红人","可否通关","location", "Shipping", "快递/小包",
                         "包裹申报金额", '手工发货说明'])

        package_ids = request.POST.getlist('package_id')
        package_items = PackageItem.objects.filter(package_id__in=package_ids).order_by("-package_id")
        for pi in package_items:
            package = pi.package
            package.set_to_logistics()
            pi.name, pi.cn_name = pi.get_item_name()

            try:
                phone = eu(package.shipping_phone.split('|')[0])
            except Exception, e:
                phone = ''
            csvlist = [
                "`"+str(package.order.ordernum),
                "`"+str(package.id).zfill(4),
                pi.item.sku,
                pi.qty,
                package.qty,
                pi.name,
                pi.name,
                eu(pi.cn_name),
                eu(package.email),
                "`" + phone,
                eu(package.name),
                eu(package.address),
                eu(package.shipping_city),
                eu(package.shipping_state),
                "`" + eu(package.shipping_zipcode),
                package.shipping_country.code,
                package.shipping_country.name,
                eu(package.shipping_country.cn_name),
                package.order.amount_shipping,
                package.weight,
                eu(package.order.note) + "|" + eu(package.note),
                eu(package.order.channel.get_type_display()),
                '',  # todo site_url
                '',  # todo 红人
                eu(package.order.cannot_tongguan() or u"可以"),
                eu(pi.get_positions()),
                eu(package.shipping and package.shipping.label),
                eu(package.order.get_shipping_type_display()),
                package.custom_amount,
                '',
            ]
            writer.writerow(csvlist)

            # 手动开始发货
            if package.status == 2:
                package.printer = request.user
                package.print_time = get_now()
                package.status = 3
                package.option_log += u'\n%s在%s 通过 无物流API单独发货 发送了产品' % (request.user.username, get_now())
                package.save()
        return response
    elif request.POST.get('type') == 'import_tracking_no':
        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)

        standard_header = ["package_id", "tracking_no", "shipping_method"]
        i = 1
        for row in reader:
            i += 1
            if header[1:] != standard_header[1:]:
                msg += u'请使用正确的模板文件'
                break

            if not row[0].isdigit():
                msg += u'第%s行的第一列不是正确的package_id |' % i
                continue

            package_id = row[0].strip()
            tracking_no = row[1].strip()
            shipping_method = row[2].strip()

            try:
                package = Package.objects.get(id=package_id, status=3)
                shipping = Shipping.objects.get(label=shipping_method)
            except Exception, e:
                msg += u'第%s行的package不存在, 或状态不是打包中, 或shipping不存在 |' % i
                continue

            if package.tracking_no:
                msg += u'第%s行的package %s 已经有运单号了, 修改运单号请联系IT |' % (i, package.id)
                continue

            # 保存好package的物流信息
            package.shipping_id = shipping.id
            package.tracking_no = tracking_no
            package.save()

            # 对包裹执行出库操作
            msg += package_deliver(package, request.user)

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'手动回传运单号成功')

    elif request.POST.get('type') == 'package_cost_import':
        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)
        standard_header = ['package_id', 'cost']

        for row in reader:
            if header[1:] != standard_header[1:]:
                msg += u'请使用正确的模板文件'
                break

            try:
                package = Package.objects.get(id=row[0].strip())
                cost = float(row[1].strip() or 0)
            except Exception, e:
                msg += u'Package id: %s 或金额有误' % row[0]
                continue

            if package.status not in (5, 6, 7):
                msg += u'Package id: %s 状态有误' % package.id
                continue

            package.cost = cost
            package.save()

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'手动回传运费成功')

    elif request.POST.get('type') == 'package_cost1_import':
        msg = ''
        reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
        header = next(reader)
        standard_header = ['package_id', 'cost1']

        for row in reader:
            if header[1:] != standard_header[1:]:
                msg += u'请使用正确的模板文件'
                break

            try:
                package = Package.objects.get(id=row[0].strip())
                cost1 = float(row[1].strip() or 0)
            except Exception, e:
                msg += u'Package id: %s 或金额有误' % row[0]
                continue

            if package.status not in (5, 6, 7):
                msg += u'Package id: %s 状态有误' % package.id
                continue

            if package.cost == 0:
                msg += u'Package id: %s cost为0不允许上传二次运费cost1 |' % package.id
            package.cost1 = cost1
            package.save()

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'手动回传二次运费成功')

    elif request.GET.get('type') == 'update_weight':
        result = {'success': True, 'msg': ''}
        try:
            package = Package.objects.get(id=request.GET['id'])
            package.weight = request.GET['weight']
            package.save()
        except Exception, e:
            result['success'] = False
            result['msg'] = str(e)
        return HttpResponse(json.dumps(result))
    elif request.GET.get('type') == 'do_search':
        if request.GET.get('package_id'):
            objs = objs.filter(id=request.GET.get('package_id'))

    per_num = request.GET.get('per_num', '100') or '100'

    paginator = Paginator(objs, int(per_num))

    try:
        p = int(request.GET.get('p', '1')) or 1
        objs = paginator.page(p)
    except(EmptyPage, InvalidPage):
        objs = paginator.page(paginator.num_pages)

    for obj in objs:
        obj.set_to_logistics()

    data['objs'] = objs
    return render(request, 'manual_deliver.html', data)


@login_required
@permission_required('lib.pick_create')
def pick_create(request):
    """生成拣货单"""
    data={}

    base_packages = Package.objects.exclude(tracking_no='')\
                                   .exclude(pick_type=0)\
                                   .filter(status=2)    # status=2 说明已经锁完了

    if request.method == "POST" and request.POST.get('pick_create') == 'pick_create':
        depots = [int(i) for i in request.POST.getlist('depot')]
        shippings = request.POST.getlist('shipping')
        pick_types = [int(i) for i in request.POST.getlist('pick_type')]
        channel_types = [int(i) for i in request.POST.getlist('channel_type')]
        user = request.user

        all_qty = 0
        # 从物理仓库, 物流方式, 拣货类型三个维度, 生成pick单, 包裹数量为选中的channel_types
        for depot in depots:
            for shipping in shippings:
                for pick_type in pick_types:
                    # 未删除 # 包裹产品齐全, 可以发货了 # 同一物理仓 # 同一物流方式 # 同一拣货类型 # 未生成拣货单
                    package_ids = base_packages.filter(order__channel__type__in=channel_types)\
                                               .filter(code=depot)\
                                               .filter(shipping__label=shipping)\
                                               .filter(pick_type=pick_type)\
                                               .values_list('id', flat=True)
                    # 单单/单多
                    if pick_type in (1, 2) :
                        result = create_single_sku_pick(list(package_ids), depot, shipping, pick_type, user)
                    # 多多
                    elif pick_type in (3, ):
                        result = create_multi_sku_pick(list(package_ids), depot, shipping, pick_type, user)
                    all_qty += result

        messages.success(request, u'成功创建%s个拣货单' % all_qty)
        return redirect('/pick/list/no_print/')

    shippings = base_packages.values_list('shipping__label', flat=True).distinct()
    data['channel_types'] = Channel.TYPE
    data['pick_types'] = Pick.PICK_TYPES
    data['depots'] = Depot.CODE
    data['shippings'] = shippings
    data['count'] = base_packages.count()
    data['title'] = u'生成拣货单'
    return render(request, 'pick_create.html', data)


@login_required
@permission_required('lib.pick_list_all')
def pick_list(request, pick_parm):
    """拣货单列表"""
    data = {}
    base_pick = Pick.objects.order_by('-id')

    if pick_parm == 'all':
        objs = base_pick
    elif pick_parm == 'no_print':
        objs = base_pick.filter(printer__isnull=True)
    elif pick_parm == 'printed':
        objs = base_pick.filter(printer__isnull=False)
    elif pick_parm == 'detail':
        pick_ids = request.GET.getlist('pick_id')
        pick_list = []
        for pick_id in pick_ids:
            pick_data = Pick.objects.get(id=pick_id)
            package_ids = list(Package.objects.filter(pick_id=pick_id).values_list('id', flat=True))
            pick_items = group_by_depotitem(package_ids)
            pick_list.append({
                'pick': pick_data,
                'pick_items': pick_items,
                'package_total': len(package_ids),
                'sku_total': len(pick_items),
                'item_total': sum([i['qty'] for i in pick_items]),
            })
        data['pick_list'] = pick_list
        data['pick_ids'] = ','.join(pick_ids)

        return render(request, 'detail.html', data)
    elif pick_parm == 'print':
        # 在拣货单中记录拣货单的打印的人和时间
        pick_ids = request.GET.get('pick_ids', '').split(',')
        Pick.objects.filter(id__in=pick_ids)\
                    .filter(printer__isnull=True)\
                    .update(printer=request.user,
                            print_time=get_now())
        return HttpResponse(json.dumps({'result':True}))

    if request.GET.get('type') == 'do_search':
        filter_params = {
            'pick_num': request.GET.get('pick_num') or '',
            'status': request.GET.get('status') or 0,
            'pick_type': request.GET.get('pick_type') or 0,
            'created__gte': request.GET.get('created_from') or '',
            'created__lte': request.GET.get('created_to') or '',
        }
        for key, values in filter_params.iteritems():
            if values:
                kwargs = {key: values}
                objs = objs.filter(**kwargs)

    per_num = request.GET.get('per_num', '100') or '100'

    paginator = Paginator(objs, int(per_num))

    try:
        p = int(request.GET.get('p', '1')) or 1
        objs = paginator.page(p)
    except(EmptyPage, InvalidPage):
        objs = paginator.page(paginator.num_pages)

    data['pick_parm'] = pick_parm
    data['objs'] = objs
    data['pick_status'] = Pick.STATUS
    data['pick_types'] = Pick.PICK_TYPES
    data['gets'] = request.GET
    data['title'] = u'拣货单列表'
    return render(request, 'list.html', data)


@login_required
def assign_assigner(request):
    """分配拣货人"""
    data = {}
    msg = ''
    user_id = ''
    if request.POST.get('type') == 'assign_assigner':
        user_id = request.POST.get('pick_user')
        pick_num = request.POST.get('pick_num')
        if not (user_id and pick_num):
            msg += u"请同时输入用户ID和拣货单号\n"

        pick = Pick.objects.filter(pick_num=pick_num).first()
        if not pick:
            msg += u"该拣货单不存在\n"

        elif not pick.printer:
            msg += u"该拣货单还未打印\n"

        elif pick.assigner:
            msg += u"您扫描或输入的拣货单【%s】已经有人在拣货, 拣货人:%s\n" % (pick_num, pick.assigner.username)

        if not msg:
            try:
                pick.assigner_id = user_id
                pick.assign_time = get_now()
                pick.save()
            except Exception, e:
                msg += str(e)
        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u"分配拣货人成功")
    user_id = user_id or request.user.id
    obj_list = Pick.objects.filter(assigner_id=user_id).order_by('-id')

    p = int(request.GET.get('p','')) if request.GET.get('p','').isdigit() else 1
    # set pagination
    paginator = Paginator(obj_list, 1)

    try:
        objs = paginator.page(p)
    except(EmptyPage, InvalidPage):
        objs = paginator.page(paginator.num_pages)

    for obj in objs:
        pick_items = PackageItem.objects.filter(package__pick_id=obj.id).aggregate(Count('id'), Sum('qty'))
        obj.sku_count = pick_items.get('id__count') or 0
        obj.sku_sum = pick_items.get('qty_sum') or 0
    data['objs'] = objs

    return render(request, 'assign.html', data)

@login_required
@csrf_exempt
@permission_required('lib.pick_sort')
def pick_sort(request):
    """分拣"""
    data = {}
    if request.GET.get('type') == 'start_pick':
        # 开始分拣一个拣货单
        pick_num = request.GET.get('pick_num')
        if not pick_num:
            return render(request, 'sort.html', data)
        pick = Pick.objects.get(pick_num=pick_num)

        # 判断是否打印, 未打印不能进行分拣
        if not pick.printer:
            messages.error(request, u'拣货单%s还未打印, 请先打印'%(pick_num))
            return redirect("pick_sort")

        # 判断拣货单的状态
        if pick.status in [2, 3, 4]:
            messages.error(request, u'拣货单%s已经分拣状态为%s, 已分拣完成'%(pick_num, pick.get_status_display()))
            return redirect("pick_sort")

        # 再判断这个拣货单是新的还是已经有人分拣了 
        if not pick.picker:
            pick.status = 1
            pick.picker = request.user
            pick.pick_start = get_now()
            pick.save()
        elif pick.picker != request.user:
            messages.error(request, u'拣货单%s已经由%s分拣了'%(pick_num, pick.picker.username))
            return redirect("pick_sort")

        # 在session中保存这个拣货单的数据
        if pick_num in request.session:
            # 未完成的拣货单, 取出保存的packages
            packages = request.session[pick_num]
        else:
            # 未分拣的拣货单, 初始化这个pick单的packages

            packages = group_by_package(pick.id)
            request.session[pick_num] = packages
        data['pick'] = pick
        data['packages'] = packages

    elif request.GET.get('type') == 'cancel_sort':
        pick_num = request.GET.get('pick_num')
        if pick_num in request.session:
            del request.session[pick_num]

        pick = Pick.objects.get(pick_num=pick_num)
        pick.status = 0
        pick.picker = None
        pick.pick_start = None
        pick.save()
        # 同时也要讲拣货单对应的package的pick_status更新为未分拣
        Package.objects.filter(pick_id=pick.id).update(pick_status=0)

        return redirect("pick_sort")
    elif request.POST.get('type') == 'update_package_status':
        # 当包裹面单打印完成之后, 再进行更新package的状态
        result = {
            'success': True,
            'package': '',
        }
        pick_num = request.POST.get('pick_num')
        packages = request.session[pick_num]
        for package in packages:
            if package['id'] != int(request.POST.get('package_id', '0')):
                continue

            if package['item_qty'] == package['pick_item_qty']:
                the_package = Package.objects.get(id=package['id'])

                # 单单和单多是包装完成, 记录包裹的打印人和打印时间
                if pick_num[1] in ('1', '2'):
                    package['pick_status'] = 3
                    the_package.pick_status = package['pick_status']
                    the_package.printer = request.user
                    the_package.print_time = get_now()
                    the_package.option_log += u'\n%s在%s 打印了该包裹的面单' % (request.user.username, get_now())
                    the_package.save()

                # 多多是分拣完成, 暂时没出面单, 所以不记录打印人和时间
                else:
                    package['pick_status'] = 2
                    the_package.pick_status = package['pick_status']
                    the_package.option_log += u'\n%s在%s 分拣完成该包裹' % (request.user.username, get_now())
                    the_package.save()
                request.session[pick_num] = packages

                result['package'] = package
            break
        return HttpResponse(json.dumps(result))

    elif request.POST.get('type') == 'can_finish':
        # 校验这个包裹是否分拣完成
        result = {
            'success': True,
        }
        pick_num = request.POST.get('pick_num')
        packages = request.session[pick_num]
        # 只要有一个包裹的状态不是分拣完成或包装完成, 那么就认为这个拣货单未分拣完
        for package in packages:
            if package['pick_status'] not in (2, 3):
                result['success'] = False
                break
        return HttpResponse(json.dumps(result))

    elif request.POST.get('type') == 'finish_pick':
        # 结束分拣, 保存异常信息, 释放这个pick_num的session        
        pick_num = request.POST.get('pick_num')
        packages = request.session[pick_num]
        pick = Pick.objects.get(pick_num=pick_num)
        # 异常跟着包裹走, 使用json保存异常信息到PackagePickError表中
        for package in packages:
            if pick.pick_type in (1, 2) and package['pick_status'] != 3:
                # 单单和单多, 包装异常
                package['pick_status'] = 5
            elif pick.pick_type == 3 and package['pick_status'] != 2:
                # 多多, 分拣异常
                package['pick_status'] = 4

            if package['pick_status'] in (4, 5):
                # 没有异常的包裹, 已经在分拣的时候, 完成了状态的改变, 所以这里只要保存异常状态即可
                p = Package.objects.get(id=package['id'])
                p.pick_status = package['pick_status']
                p.save()

                pick_err, flag = PackagePickError.objects.get_or_create(pick_id=p.pick_id,
                                                                        package=p,
                                                                        is_processed=False, 
                                                                        error_type=package['pick_status'],)
                pick_err.error_info = json.dumps(package)
                pick_err.save()

        # 拣货单完成, 单单/单多是包装完成, 多多是分拣完成
        if pick.pick_type in (1, 2):
            pick.status = 3
        elif pick.pick_type in (3, ):
            pick.status = 2
        pick.pick_end = get_now()
        pick.save()

        # pick的session删除
        del request.session[pick_num]

        result = {'path': request.path}
        return HttpResponse(json.dumps(result))

    else:
        # 默认展示当前用户未包装完成的拣货单, 不区分单单, 单多, 多多
        picks = Pick.objects.filter(status__in=[0, 1, 2, ])\
                            .filter(picker=request.user)

        data['picks'] = picks

    return render(request, 'sort.html', data)

@csrf_exempt
def ajax_sort(request):
    """三种分拣类型的package分拣都走这里
    理念: 已知pick_id和sku, 将这个sku在这个pick下所有的package, 
         然后package的packageitem进行循环, 找出这个sku应该属于哪个package
    """
    result = {
        'success': True,
        'package': '',
        'packageitem': '',
        'msg': ''
    }
    pick_num = request.POST['pick_num']
    pick_type = int(request.POST['pick_type'])
    sort_sku = request.POST['sku'].strip()
    packages = request.session[pick_num]    # 从session中取出这个拣货单号对应的packages
    for package in packages:
        # 如果package分拣完成, 或包装完成, 那么跳过这个package的判断
        if package['pick_status'] in (2, 3):
            continue

        # 将sku在这个package的所有item中进行循环判断
        for pi in package['items']:
            if sort_sku != pi['choies_sku'] and sort_sku != pi['sku']:
                continue

            # 这个sku已捡完, 则跳过. 注意: 多多里, 可能一个item已捡完, 但是package的pick_status任然为1
            if pi['status'] == 1:
                continue

            # 处理这个package item的状态
            pi['pick_qty'] += 1
            if pi['pick_qty'] == pi['qty']:
                pi['status'] = 1

            # 处理这个package的状态, package中的item_qty是这个包裹中所有items的qty之和
            package['pick_item_qty'] += 1

            # 返回选中的这个package及packageitem
            result['pick_type'] = pick_type
            result['package'] = package
            result['packageitem'] = pi
            break
        if result['package']:
            break

    # 没有找到匹配的信息
    if not result['package']:
        result['success'] = False
        result['msg'] = u'此SKU没有可匹配的包裹!'
    request.session[pick_num] = packages
    return HttpResponse(json.dumps(result))

@csrf_exempt
@permission_required('lib.pick_packaging')
def pick_packaging(request):
    """多多包装"""
    data = {}
    if request.GET.get('type') == 'start_packaging':
        # 开始分拣一个拣货单
        pick_num = request.GET.get('pick_num')
        if not pick_num:
            return render(request, 'sort.html', data)

        pick = Pick.objects.get(pick_num=pick_num)
        # 判断拣货单的状态
        if pick.status != 2:
            messages.error(request, u'拣货单%s状态为%s, 不是分拣完成'%(pick_num, pick.get_status_display()))
            return redirect('pick_packaging')

        # 再判断这个拣货单是新的还是已经有人分拣了 
        if not pick.packager:
            pick.packager = request.user
            pick.package_start = get_now()
            pick.save()
        elif pick.packager != request.user:
            messages.error(request, u'拣货单%s已经由%s包装了'%(pick_num, pick.picker.username))
            return redirect('pick_packaging')

        # 在session中保存这个拣货单的数据
        if pick_num in request.session:
            # 未完成的拣货单, 取出保存的packages
            packages = request.session[pick_num]
        else:
            # 未分拣的拣货单, 初始化这个pick单的packages, pick_status改成2即分拣完成
            packages = group_by_package(pick.id)
            for package in packages:
                package['pick_status'] = 2
            request.session[pick_num] = packages
        
        data['pick'] = pick
        data['packages'] = packages
    elif request.POST.get('type') == 'map_package':
        # 前台完成一个包裹的分拣, 则到后台匹配包裹
        result = {
            'success': True,
            'package': '',
            'msg': '',
        }
        pick_num = request.POST.get('pick_num', '')
        packages = request.session[pick_num]

        # 只匹配状态为分拣完成的包裹
        for package in packages:
            package['item_info'] = {i['sku']:str(i['qty']) for i in package['items'] if package['pick_status'] == 2}

        package_items = json.loads(request.POST.get('packageitems', ''))

        # 比较传来的package_items和package中的item_info是否有匹配的
        for package in packages:
            # 匹配上, 则更新packages的信息, 更新package的状态为 包装完成
            if package['item_info'] == package_items:

                result['package'] = package
                package['pick_status'] = 3
                the_package = Package.objects.get(id=package['id'])
                the_package.pick_status = package['pick_status']
                the_package.printer = request.user
                the_package.print_time = get_now()
                the_package.option_log += u'\n%s在%s 打印了该包裹的面单' % (request.user.username, get_now())
                the_package.save()
                break
        request.session[pick_num] = packages
        if not result['package']:
            result['success'] = False
            result['msg'] = u'未匹配倒任何包裹，是否扫描新的包裹!'

        return HttpResponse(json.dumps(result))
    elif request.POST.get('type') == 'can_finish':
        result = {
            'success': True,
        }
        pick_num = request.POST.get('pick_num')
        packages = request.session[pick_num]
        # 如果有一个包裹不是包装完成, 则说明不是正确的包装完成
        for package in packages:
            if package['pick_status'] not in (3, ):
                result['success'] = False
                break
        return HttpResponse(json.dumps(result))

    elif request.POST.get('type') == 'finish_packaging':
        # 结束包装, 保存异常信息, 释放这个pick_num的session        
        pick_num = request.POST.get('pick_num')
        packages = request.session[pick_num]

        # 异常跟着包裹走, 使用json保存异常信息到PackagePickError表中
        for package in packages:
            if package['pick_status'] != 3:
                package['pick_status'] = 5

                p = Package.objects.get(id=package['id'])
                p.pick_status = package['pick_status']
                p.save()

                pick_err, flag = PackagePickError.objects.get_or_create(pick_id=p.pick_id,
                                                                        package=p,
                                                                        error_type=package['pick_status'])
                pick_err.error_info = json.dumps(package)
                pick_err.save()

        # 拣货单完成
        pick = Pick.objects.get(pick_num=pick_num)
        pick.status = 3
        pick.pick_end = get_now()
        pick.save()

        # pick的session删除
        del request.session[pick_num]

        result = {'path': request.path}
        return HttpResponse(json.dumps(result))
    else:
        # 默认展示当前用户分拣完成的拣货单
        picks = Pick.objects.filter(status=2)\
                            .filter(pick_type=3)\
                            .filter(picker=request.user)
        data['picks'] = picks

    return render(request, 'packaging.html', data)

@csrf_exempt
def pick_abnormal(request):
    data = {}
    objs = PackagePickError.objects.all()\
                                   .order_by('-created')

    if request.method == 'POST' and request.POST.get('type') == 'finish_deal':
        error_id = request.POST.get('error_id')
        the_error = PackagePickError.objects.get(id=error_id)
        the_error.is_processed = True
        the_error.processor = request.user
        the_error.process_time = get_now()
        the_error.save()

        package = the_error.package
        if the_error.error_type == 4:
            # 分拣异常改为分拣完成
            package.pick_status = 2
        elif the_error.error_type == 5:
            # 包装异常改为包装完成
            package.pick_status = 3
        package.save()

        result = {'success': True, 'processor': request.user.username, 'process_time': str(get_now())[5:-6], }
        return HttpResponse(json.dumps(result))

    if request.GET.get('type') == 'do_search':
        filter_params = {
            'package_id': request.GET.get('package_id') or '',
            'package__pick_type': request.GET.get('pick_type') or 0,
            'error_type': request.GET.get('error_type') or 0,
            'is_processed': request.GET.get('is_processed') or 0,
            'created__gte': request.GET.get('created_from') or '',
            'created__lte': request.GET.get('created_to') or '',
        }
        for key, values in filter_params.iteritems():
            if values:
                kwargs = {key: values}
                objs = objs.filter(**kwargs)

    per_num = request.GET.get('per_num', '100') or '100'

    paginator = Paginator(objs, int(per_num))

    try:
        p = int(request.GET.get('p', '1')) or 1
        objs = paginator.page(p)
    except(EmptyPage, InvalidPage):
        objs = paginator.page(paginator.num_pages)

    for obj in objs:
        obj.packageitems = json.loads(obj.error_info).get('items', {})



    data['objs'] = objs
    data['error_type'] = Package.PICK_STATUS[4:]
    data['pick_types'] = Pick.PICK_TYPES[1:]
    data['gets'] = request.GET

    return render(request, 'abnormal.html', data)


def print_label(request):
    package_ids = request.GET.get('package_list', '').split(',')
    packages = Package.objects.filter(id__in=package_ids)
    result = get_label_data(packages)
    return render(request, 'labels/' + result['template'], result)

def pick_re_print(request):
    """原面单重新打印等各种操作"""
    data = {}
    if request.POST.get('type') == "re_print_by_package_id":
        package_id = request.POST.get('package_id')
        return redirect("/pick/print_label/?package_list=%s"%package_id)

    elif request.POST.get('type') == "re_print_by_tracking_no":
        tracking_no = request.POST.get('tracking_no')
        package = Package.objects.filter(tracking_no=tracking_no).first()
        if package:
            return redirect("/pick/print_label/?package_list=%s"%package_id)
        else:
            messages.error(request, u"没有查询到该运单号匹配的包裹")

    elif request.POST.get('type') == "get_pdf_by_package_id":
        package = Package.objects.filter(id=request.POST.get('package_id')).first()
        if package:
            link = get_pdf_label(package)
            return redirect(link)
        else:
            messages.error(request, u"没有查询到该运单号匹配的包裹")
    elif request.POST.get('type') == "print_user_username":
        usernames = request.POST.get('usernames').split('\r\n')
        users = User.objects.filter(username__in=usernames)
        data['users'] = users
        return render(request, 'print_username.html', data)            

    return render(request, 're_print.html', data)


def execute_deliver(request, status):
    """执行发货"""
    data = {}
    data['status'] = status

    msg = ''

    base_packages = Package.objects.filter(pick_status=3).filter(shipping__label__in=ShippingList.have_api_shipping)

    # 未发货的
    if status == "not":
        objs = base_packages.filter(status=3)
    elif status == 'already':
        objs = base_packages.filter(status__gte=4)
    else:
        objs = []

    if request.GET.get('type') == 'do_search':
        filter_params = {
            'id': request.GET.get('package_id') or '',
            'shipping_id': request.GET.get('shipping_id') or 0,
            'print_time__gte': request.GET.get('print_time_from') or '',
            'print_time__lte': request.GET.get('print_time_to') or '',
            'ship_time__gte': request.GET.get('ship_time_from') or '',
            'ship_time__lte': request.GET.get('ship_time_to') or '',
        }
        for key, values in filter_params.iteritems():
            if values:
                kwargs = {key: values}
                objs = objs.filter(**kwargs)
        
    elif request.GET.get('type') == 'signle_deliver':
        tracking_no = request.GET.get('tracking_no')
        package = Package.objects.filter(tracking_no=tracking_no).first()
        
        # return 
        if not package:
            msg += u'运单号为%s 没有对应包裹' % tracking_no
        else:
            msg += package_deliver(package, request.user)

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'执行发货成功')

        return redirect('pick_execute_deliver', status=status)
    elif request.POST.get('type') == 'bulk_deliver':
        package_ids = request.POST.getlist('package_id')
        packages = objs.filter(id__in=package_ids)
        for package in packages:
            msg += package_deliver(package, request.user)

        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'执行发货成功')

        return redirect('pick_execute_deliver', status=status)
        # return redirect('pick_execute_deliver', )




    per_num = request.GET.get('per_num', '100') or '100'

    paginator = Paginator(objs, int(per_num))

    try:
        p = int(request.GET.get('p', '1')) or 1
        objs = paginator.page(p)
    except(EmptyPage, InvalidPage):
        objs = paginator.page(paginator.num_pages)


    data['objs'] = objs
    data['api_shipping'] = Shipping.objects.filter(label__in=ShippingList.have_api_shipping)
    data['gets'] = request.GET
    return render(request, 'execute_deliver.html', data)


############################
###### 下面都是内部方法 ######
############################
def group_by_package(pick_id):
    """将这个拣货单中的package及其packageitem整理成用来展示的dict, 以package为最小单位, 并添加一些必要的key"""
    # 获取这个拣货单的数据, 以package为单位, 并按package的id进行排序
    package_status_choies = dict(Package.STATUS)
    packageitems = PackageItem.objects.filter(package__pick_id=pick_id)\
                                      .exclude(package__pick_status__in=(4, 5))\
                                      .values('id', 'package_id', 'item__sku', 'qty', 'package__tracking_no',
                                              'package__order__channel__name', 'package__status', 'package__pick_status')
    skus = [i['item__sku'] for i in packageitems]
    choies_skus = dict(Alias.objects.filter(item__sku__in=skus).filter(channel_id=1).values_list('item__sku', 'sku'))

    # 因为一个产品可能会对应多个ItemLocked, 不同的ItemLocked又可能会对应不同的depotitem
    # 每个depotitem的库位, 是用','连接, 所以会将多个position进行分割再连接, 同时去重
    positions = ItemLocked.objects.filter(package_item__package__pick_id=pick_id)\
                                  .values_list('package_item_id', 'depot_item__position')
    pi_id_position = {}
    for pi_id, position in positions:
        if pi_id not in pi_id_position:
            pi_id_position[pi_id] = position.split(',')
        else:
            for i in position.split(','):
                if i not in pi_id_position[pi_id]:
                    pi_id_position[pi_id].append(i)
    pi_id_position = {i: ','.join(j) for i, j in pi_id_position.iteritems()}

    packages = {}
    for packageitem in packageitems:
        sku = packageitem['item__sku']
        pi_id = packageitem['id']
        package_id = packageitem['package_id']

        # fix 如果session消失, 重新分拣的时候, 为了不出错, 在生成数据的时候, 处理一下数据
        package_pick_status = packageitem['package__pick_status']
        if package_pick_status == 3:
            picked_qty = packageitem['qty']
            pi_status = 1 # 这个packageitem已分拣完成
        else:
            picked_qty = 0
            pi_status = 0 # 这个packageitem已分拣完成

        package_item = {
            'id': pi_id,
            'sku': sku,
            'qty': packageitem['qty'],
            'pick_qty': picked_qty,
            'status': pi_status,
            'choies_sku': choies_skus.get(sku, ''),
            'position': pi_id_position.get(pi_id, ''),
        }

        if package_id not in packages:
            packages[package_id] = {
                'id': package_id,
                'pick_status': 1,
                'item_qty': packageitem['qty'],
                'pick_item_qty': 0,
                'tracking_no': packageitem['package__tracking_no'],
                'items': [package_item, ],
                'status': package_status_choies[packageitem['package__status']],
                'shop': packageitem['package__order__channel__name'],
            }
        else:
            packages[package_id]['items'].append(package_item)
            packages[package_id]['item_qty'] += packageitem['qty']

        # 包裹如果完成, 那么直接更新pick_status和pick_item_qty
        if package_pick_status == 3:
            packages[package_id]['pick_status'] = 3
            packages[package_id]['pick_item_qty'] = packages[package_id]['item_qty']

    packages = [package for package_id, package in packages.iteritems()]
    packages.sort(key=lambda x: x['id'])
    for index, package in enumerate(packages, start=1):
        package['index'] = index
    return packages

def group_by_depotitem(package_ids):
    """将package中的产品, 根据depot_item进行分组, 并将分组好的数据根据库位进行排序"""
    item_lockeds = ItemLocked.objects.filter(package_item__package_id__in=package_ids)\
                                     .filter(deleted=False)\
                                     .values_list('depot_item_id', 'depot_item__position', 
                                                  'package_item__package_id', 'qty', 'depot_item__item__sku',
                                                  'depot_item__item__product__category__cn_name')

    skus = [i[4] for i in item_lockeds]
    choies_skus = dict(Alias.objects.filter(item__sku__in=skus).filter(channel_id=1).values_list('item__sku', 'sku'))

    # 根据depot_item进行分组
    depot_items = {}
    for depot_item_id, position, package_id, qty, sku, cn_name in item_lockeds:                                     
        if depot_item_id not in depot_items:
            depot_items[depot_item_id] = {
                'depot_item_id': depot_item_id,
                'qty': qty,
                'package_ids': {package_id:qty, },
                'position': position,
                'sku': sku,
                'cn_name': cn_name,
                'choies_sku': choies_skus.get(sku, ''),
            }
        else:
            depot_items[depot_item_id]['qty'] += qty
            depot_items[depot_item_id]['package_ids'][package_id] = qty

    items = [value for depot_item_id, value in depot_items.iteritems()]

    # 把产品根据position进行排序
    items.sort(key=lambda x:x['position'])
    return items

def create_pick_num(pick):
    """创建pick_num"""
    the_char_dict = {
        1: 'N',
        2: "G",
    }
    the_char = the_char_dict[pick.code]
    pick_num = "{0}{1}{2:0>8}".format(the_char, pick.pick_type, pick.id)
    pick.pick_num = pick_num
    pick.save()

# 单单和单多
def create_single_sku_pick(package_ids, depot, shipping, pick_type, user):
    """单单和单多都可以使用这个方法"""
    # 获取package中产品, 并分组, 排序
    items = group_by_depotitem(package_ids)

    # 每次取25个items, 用于生成pick单
    per_page = 25
    pick_nums = 0
    for sub_items in [items[i:i+per_page] for i in xrange(0, len(items), per_page)]:
        # 生成pick单
        pick = Pick.objects.create(code=depot,
                                   shipping=shipping,
                                   pick_type=pick_type,
                                   user_adder=user,)
        create_pick_num(pick) # 创建拣货单号

        # 更新这些产品对应package的pick, 同时生成对应的packageitem
        all_package_ids = []
        for sub_item in sub_items:
            PickItem.objects.create(pick=pick, depot_item_id=sub_item['depot_item_id'], qty=sub_item['qty'])

            all_package_ids.extend(sub_item['package_ids'].keys())

        Package.objects.filter(id__in=all_package_ids).update(pick_id=pick.id, status=3)

        pick_nums += 1

    return pick_nums


# 多多
def create_multi_sku_pick(package_ids, depot, shipping, pick_type, user):
    """多多packages根据库位得分进行排序, 每个pick表捡20个package"""
    #
    packages = list(Package.objects.filter(id__in=package_ids).values_list('id', 'position_score'))
    packages.sort(key=lambda x:x[1])

    per_page = 20
    pick_nums = 0
    for sub_packages in [packages[i:i+per_page] for i in xrange(0, len(packages), per_page)]:
        # 生成pick单
        pick = Pick.objects.create(code=depot, shipping=shipping, pick_type=pick_type, user_adder=user)
        create_pick_num(pick) # 创建拣货单号

        sub_pids = [i[0] for i in sub_packages]
        # 获取package中产品, 并分组, 排序, 从而创建pickitem
        items = group_by_depotitem(sub_pids)
        for sub_item in items:
            PickItem.objects.create(pick=pick, depot_item_id=sub_item['depot_item_id'], qty=sub_item['qty'])
            
        Package.objects.filter(id__in=sub_pids).update(pick_id=pick.id, status=3)

        pick_nums += 1

    return pick_nums

def package_deliver(package, user):
    # 取出这个package下所有的item_locked
    msg = ''
    item_lockeds = ItemLocked.objects.filter(package_item__package_id=package.id, deleted=False)
    if item_lockeds:
        try:
            for item_locked in item_lockeds:
                # 先标记删除
                item_locked.deleted = True
                item_locked.save()

                # 记录出库记录
                out_qty = item_locked.depot_item.item_out(item_locked.qty, obj=item_locked.package_item.package, type=0, operator=user)
            if out_qty:
                package.status = 5
                package.shipper = user
                package.ship_time = get_now()
                package.option_log += u"\n%s在%s 执行了发货" %(user.username, get_now())
                package.save()
            else:
                package.option_log += u"\n%s在%s 执行了发货, 但出库失败, 请联系技术部" %(user.username, get_now())
                package.save()

        except Exception, e:
            msg = u'%s 失败: %s |' % (package.id, str(e))


    return msg
