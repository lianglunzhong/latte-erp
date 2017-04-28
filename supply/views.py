# -*- coding: utf-8 -*-
from django.shortcuts import render,get_object_or_404,redirect
from django.template.response import TemplateResponse,HttpResponse
from django.db.models import Sum
from django.contrib.contenttypes.models import ContentType
# Create your views here.

from project import settings as p_settings
from supply.models import Supplier,PurchaseOrderItem,PurchaseOrder,PurchaseOrderCheckedItem,SupplierProduct
from product.models import Category,Product,Item,Option
from django.views.generic import View
from django.http import JsonResponse
import json
from django.contrib import messages
from supply.forms import SupplyAddForm
from lib.utils import get_now
from depot.models import DepotInLog,DepotItem
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required, permission_required


class SupplierEdit(View):

    module_name='supplier';

    def get(self,request,id,flag):
        context = {}
        context['class_name']=self.module_name
        context['flag']=flag
        if flag == 'add':
            context['form'] = SupplyAddForm()
        elif flag == 'edit':
            obj=get_object_or_404(Supplier,id=id)
            context['form'] = SupplyAddForm(instance=obj)

        return TemplateResponse(request, self.module_name+'_add.html', context)

    def post(self,request,id,flag):
        context ={}
        context['class_name']=self.module_name
        context['flag']=flag
        if flag == 'add':
            post_arr = request.POST
            abc = SupplyAddForm(post_arr)

            if abc.is_valid():
                add=abc.save()
                messages.add_message(request, messages.SUCCESS, self.module_name+' add success')
                return redirect(self.module_name+'_edit', id=add.id)
            else:
                messages.add_message(request, messages.ERROR, self.module_name+' add ERROR')
                context['form'] = abc
                return TemplateResponse(request, self.module_name+'_add.html', context)
        elif flag == 'edit':
            object_to_edit = get_object_or_404(Supplier,id=id) #Or slug=slug
            abc = SupplyAddForm(data = request.POST, instance=object_to_edit)

            if abc.is_valid():
                abc.save()
                messages.add_message(request, messages.SUCCESS, self.module_name+' edit success')
                return redirect(self.module_name+'_edit', id=id)
            else:
                context['form'] = SupplyAddForm(request.POST)
                messages.add_message(request, messages.ERROR, self.module_name+' edit ERROR')
                return TemplateResponse(request, self.module_name+'_add.html',context)


def supplier_list(request):

    from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger

    search = request.GET.get('search')
    if not search:
        search = ''
    page_want = request.GET.get('p')
    supplier = Supplier()
    list = supplier.supplier_list(search)
    # print list
    paginator = Paginator(list, p_settings.Supplier_Per_Page_Num)

    try:
        page_info = paginator.page(page_want)
    except PageNotAnInteger:
        page_info = paginator.page(1)
    except EmptyPage:
        page_info = paginator.page(paginator.num_pages)

    return TemplateResponse(request,'supplier_list.html',{'info':page_info,'search':search})


def supplier_delete(request):
    """
    product edit
    """
    ids=request.POST.get('ids')
    data=json.loads(ids)
    str = {}
    for i in data['data']:
        try:
            i = int(i)
            Supplier.objects.filter(id=i).update(deleted=1)

            str[i] = 1
        except:
            str[i] = 0

    return JsonResponse(str)


def itemin_action(sku, qty=0, depot=0, user=None, purchaseorderitem_id=None,):
    print sku
    data = {}
    data['msg'] = ''

    if not sku or not sku.strip():
        data['msg'] += u'请输入sku'
        data['success'] = False
        return data

    try:
        input_qty = int(qty)
        all_number = input_qty
    except:
        data['msg'] += u'请输入正确的数量'
        data['success'] = False
        return data

    if not input_qty:
        data['msg'] += u'请输入数量必须大于0'
        data['success'] = False
        return data

    depotitem = DepotItem.objects.filter(depot__code=depot,item__sku=sku,deleted=False).first()
    if not depotitem or not depotitem.position:
        data['msg'] += u'此仓库的sku不存在或者库位为空，请完善数据再入库'
        data['success'] = False
        return data

    product = Item.objects.filter(sku=sku,deleted=False).first()
    if not product or not product.weight:
        data['msg'] += u'此货品不存在或者sku重量为空，请完善数据再入库'
        data['success'] = False
        return data



    # pois = PurchaseOrderItem.objects.filter(item__sku=sku).filter(checked=1, status__in=(0,3), cost_approved=1).exclude(item__location__isnull=True).exclude(item__weight=0)

    if not purchaseorderitem_id:
        # pois = PurchaseOrderItem.objects.filter(item__sku=sku).filter(status__in=(0,3), cost_approved=1)
        poci_sql = PurchaseOrderCheckedItem.objects.filter(deleted=False,purchaseorderitem__item__sku=sku,status__in=(0,1),purchaseorder__depot__code=depot)
    else:
        # pois = PurchaseOrderItem.objects.filter(item__sku=sku).filter(checked=1, status__in=(0,3), cost_approved=1,purchase_order__depot=depot,purchase_order_id = purchaseorder_id).exclude(item__weight=0)
        # pois = PurchaseOrderItem.objects.filter(item__key=sku).filter(status__in=(0,3),purchase_order__depot_id=depot,purchase_order_id = purchaseorder_id)
        # pois = PurchaseOrderItem.objects.filter(pk=purchaseorderitem_id).filter(status__in=(0,3))
        poci_sql = PurchaseOrderCheckedItem.objects.filter(deleted=False,purchaseorderitem_id=purchaseorderitem_id,status__in=(0,1),purchaseorder__depot__code=depot)
    if not poci_sql:
        data['msg'] += u'此sku没有采购货品需等待入库'
        data['success'] = False
        return data

    pois_real_qty = poci_sql.aggregate(Sum('depotinlog_qty')).get('real_qty__sum', 0)#sku已经入库的总数量
    pois_qty = poci_sql.aggregate(Sum('qty')).get('qty__sum', 0)#sku已经对单的总数量
    pois_waiting_qty = pois_qty - pois_real_qty#等待入库的数量

    print 'pois_real_qty',pois_real_qty
    print 'pois_waiting_qty',pois_waiting_qty
    print 'input_qty',input_qty
    if input_qty > pois_waiting_qty:
        data['msg'] += u'待入库数量为%s, 不可超出!' % pois_waiting_qty
        data['success'] = False
        return data
    elif input_qty == 0:
        data['msg'] += u'待入库数量不可为0'
        data['success'] = False
        return data
    else:
        #优先处理部分入库的
        poci_sql = poci_sql.order_by('-status')
        for poci in poci_sql:
            print 'poi',poci.id
            need_qty = poci.qty - poci.depotinlog_qty#需要入库的数量
            if need_qty<=0:
                continue
            #输入的数量number如果比该poi的need_qty大, 则将该poi入满, 继续循环
            if input_qty > need_qty:
                input_qty -= need_qty
                poci.depotinlog_qty += need_qty
                poci.status = 2
                poci.save()
                poci_depotinlog(poci,need_qty,user)

                data['msg'] = u'%s成功收货%s件' %(sku, all_number)
                data['success'] = True
            #相等则完成该poi后退出循环
            elif input_qty == need_qty:
                #入库完成, 之后结束
                poci.depotinlog_qty += need_qty
                poci.status = 2
                poci.save()
                poci_depotinlog(poci,need_qty,user)

                data['msg'] = u'%s成功收货%s件' %(sku, all_number)
                data['success'] = True
                break
            #将这个poi进行部分入库, 然后结束
            elif input_qty < need_qty:
                poci.depotinlog_qty += input_qty
                poci.status = 1
                poci.save()
                poci_depotinlog(poci,input_qty,user)

                data['msg'] = u'%s成功收货%s件' %(sku, all_number)
                data['success'] = True
                break
    print data
    return data

#扫描入库，新增入库记录item_in(self, qty, cost, note="", obj=None, type=0, operator=None)
def poci_depotinlog(poci,depotinlog_qty,user):
    depotitem,flag = DepotItem.objects.get_or_create(depot=poci.purchaseorder.depot,item=poci.purchaseorderitem.item)
    # depotitem.qty= depotinlog_qty
    # depotitem.cost= poci.purchaseorderitem.cost
    note=''
    type=0
    depotitem.item_in(depotinlog_qty,poci.purchaseorderitem.cost,note,poci.purchaseorder,type,user)
    # depot_in_log = DepotInLog()
    # depot_in_log.depot = poci.purchaseorderitem.depot
    # depot_in_log.item = poci.purchaseorderitem.item
    # depot_in_log.qty = depotinlog_qty
    # depot_in_log.cost = poci.purchaseorderitem.cost
    # depot_in_log.object_id = poci.purchaseorder_id
    # content_type = ContentType.objects.get(model='purchaseorder')
    # depot_in_log.content_type_id = content_type.id
    # depot_in_log.operator_id = user_id
    # depot_in_log.type = 0
    # depot_in_log.save()#生成入库记录，修改属性产品库存

# <QueryDict: {u'sku': [u'fds'], u'category': [u''], u'purchaseorderitem_purchaser
# ': [u''], u'tracking': [u''], u'factory': [u''], u'purchaseorder_created_to': [u
# ''], u'factory_sku': [u''], u'purchaseorder_created_from': [u''], u'status': [u'
# 0'], u'csrfmiddlewaretoken': [u'WQwyzLjyWrCIqwE1suozdmzNqKinWRRk'], u'type': [u'
# do_search'], u'purchaseorder_assigner': [u''], u'per_num': [u'']}>
def checkorder_select(request):

    search_condition = {}
    search_condition['tracking'] = request.GET.get('tracking', "").strip()
    search_condition['sku'] = request.GET.get('sku', "").strip()
    search_condition['factory'] = request.GET.get('factory', "").strip()
    search_condition['factory_sku'] = request.GET.get('factory_sku', "").strip()
    search_condition['category'] = request.GET.get('category', "").strip()
    # search_condition['checked'] = request.GET.get('checked', '0')
    search_condition['per_num'] = request.GET.get('per_num',50)
    search_condition['status'] = request.GET.get('status', '99')

    search_condition['purchaseorder_created_from'] = request.GET.get('purchaseorder_created_from', "")
    search_condition['purchaseorder_created_to'] = request.GET.get('purchaseorder_created_to', "")
    search_condition['purchaseorder_assigner'] = request.GET.get('purchaseorder_assigner', "")
    search_condition['purchaseorderitem_purchaser'] = request.GET.get('purchaseorderitem_purchaser', "")

    poi = PurchaseOrderItem.objects.filter(purchaseorder__deleted=False).order_by('-id').exclude(status__in=[0,2]).exclude(purchaseorder__status__in=[0,4])
    if search_condition['status'] == '100':
        pass
    elif search_condition['status'] == '99':
        poi = poi.exclude(action_status=2)
    else:
        poi = poi.filter(action_status=search_condition['status'])

    if search_condition['sku']:
        poi = poi.filter(item__sku__icontains=search_condition['sku'])

    if search_condition['tracking']:
        poi = poi.filter(purchaseorder__tracking__icontains=search_condition['tracking'])

    if search_condition['factory']:
        supplierproduct = SupplierProduct.objects.filter(supplier__name__icontains=search_condition['factory']).filter(deleted=False,order=1).values_list('product_id',flat=True)
        # supp = [1,2]
        poi = poi.filter(item__product_id__in=supplierproduct)

    if search_condition['factory_sku']:
        supplierproduct_sku = SupplierProduct.objects.filter(supplier_sku__icontains=search_condition['factory_sku']).filter(deleted=False,order=1).values_list('product_id',flat=True)
        # supp = [1,2]
        poi = poi.filter(item__product_id__in=supplierproduct_sku)

    if search_condition['category']:
        poi = poi.filter(item__product_category__name__icontains=search_condition['category'])

    if search_condition['purchaseorder_created_from']:
        poi = poi.filter(purchaseorder__created__gte=search_condition['purchaseorder_created_from'])

    if search_condition['purchaseorder_created_to']:
         poi = poi.filter(purchaseorder__created__lte=search_condition['purchaseorder_created_to'])

    if search_condition['purchaseorder_assigner']:
        poi = poi.filter(purchaseorder__creater__first_name__icontains=search_condition['purchaseorder_assigner'])

    if search_condition['purchaseorderitem_purchaser']:
        poi = poi.filter(purchaseorder__manager__first_name__icontains=search_condition['purchaseorderitem_purchaser'])

    poi = poi.order_by('purchaseorder__supplier')
    from django.core.paginator import Paginator,EmptyPage,PageNotAnInteger
    search_condition['p'] = request.GET.get('p', 1)
    if not search_condition['per_num']:
        search_condition['per_num']=50
    paginator = Paginator(poi,search_condition['per_num'])

    try:
        page_info = paginator.page(search_condition['p'])
    except PageNotAnInteger:
        page_info = paginator.page(1)
    except EmptyPage:
        page_info = paginator.page(paginator.num_pages)

    print 'page_info',page_info

    for purchaseorderitem in page_info:
        supplierproduct_sku = SupplierProduct.objects.filter(supplier=purchaseorderitem.purchaseorder.supplier,product=purchaseorderitem.item.product).filter(deleted=False).first()
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

    data = {
        "queryset": poi,
        "search_condition": search_condition,
        "page_info":page_info
    }

    return data

# 采购物品对单界面 修改产品重量
@csrf_exempt
def ajax_item_weight(request):
    result = False
    if 'weight' in request.POST and 'id' in request.POST and 'model' in request.POST:
        try:
            # product = Product.objects.get(id=request.POST['id'])
            # product.weight = request.POST['weight']
            # product.save()
            item = Item.objects.get(id=request.POST['id'])
            item.weight = request.POST['weight']
            item.save()
            result = True
        except Exception, e:
            pass

    return HttpResponse(json.dumps(result))

# ajax 修改物流号
@csrf_exempt
def ajax_update_poi_trackingNo(request):
    result = {}
    result["message"] = ""
    result["status"] = 0
    if 'poiId' in request.POST and 'trackingNo' in request.POST:
        try:
            # PurchaseOrderItem.objects.filter(id=request.POST.get('poiId')).update(tracking=request.POST.get('trackingNo'))
            PurchaseOrder.objects.filter(id=request.POST.get('poiId')).update(tracking=request.POST.get('trackingNo'))
            result["message"] = "更新成功"
            result["status"] = 1
        except:
            result["message"] = "更新失败"
    else:
        result["message"] = "不存在此采购单"
    return HttpResponse(json.dumps(result))

@csrf_exempt
def ajax_update_checkorder_num(request):
    result ={}
    result['status'] =False
    result['msg'] = u'test'
    pois = request.POST.get('pois')
    poi_arrs = pois.split(',')

    poi_ids = []
    for poi_arr in poi_arrs:
        arr = poi_arr.split('#')
        poi_id = int(arr[0])
        poi_real_qty = int(arr[1])

        poi = PurchaseOrderItem.objects.get(pk=poi_id)
        PurchaseOrderCheckedItem.objects.create(purchaseorder=poi.purchaseorder,purchaseorderitem_id=poi.id,qty=poi_real_qty,add_user_id=request.user.id)
        #修改采购物品里的对单数量
        poi.real_qty=poi.real_qty+poi_real_qty
        poi.save()
        result['msg']=u'操作成功'
        result['status']=True
        poi_ids.append(poi_id)
    poi_ids_str = ','.join([str(i) for i in poi_ids])
    print poi_ids_str
    path = '/admin/supply/purchaseorderitem/purchaseorderitem_check/?type=show_checked&poi_ids=%s'% poi_ids_str
    result['path'] = path

    return HttpResponse(json.dumps(result))


@login_required
@permission_required('lib.auto_create_purchaseorder')
def create_purchaseorder(request):
    data_notice={}
    if request.POST:
        from purchase_action import action_create_purchaseorder
        re = action_create_purchaseorder()
        if re=='ok':
            messages.add_message(request, messages.SUCCESS, '采购单生成成功')
        else:
            messages.add_message(request, messages.ERROR, '采购单生成成功')


    return TemplateResponse(request,'create_purchaseorder.html',{'data_notice':data_notice})