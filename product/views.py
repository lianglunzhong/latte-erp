# -*- coding: utf-8 -*-
import os
import sys
import json
import StringIO
import csv
import urllib2

from urlparse import urlparse
from django.core.files.base import ContentFile

from django.shortcuts import render, get_object_or_404, redirect
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.utils.http import urlencode
from django.core.urlresolvers import reverse

from django.conf import settings
from django.template.response import TemplateResponse, HttpResponse
from django.utils.translation import ugettext as _

from product.models import Category, Product, Item, Option, ProductAttribute, ProductImage
from django.views.generic import View
from project import settings as p_settings

from django.http import JsonResponse
from django.contrib import messages
from django.forms import formset_factory
from order.models import Alias, Order
from supply.models import SupplierProduct, Supplier
from depot.models import DepotInLog, DepotItem
from shipping.models import Package
from django.contrib.auth.decorators import login_required, permission_required

from lib.utils import pp, get_now, eu, write_csv, eparse, add8
from product.models import *


def handle(request):
    data = {}
    if request.POST.get('type') == 'get_product_img_by_ws_sku':
        skus = request.POST.get('skus', '').strip().split('\r\n')
        msg = save_imgs_by_skus(skus)
        if msg:
            messages.error(request, msg)
        else:
            messages.success(request, u'图片保存成功')
        return redirect('product_handle')
    return render(request, 'product_handle.html', data)


# 导入的产品
def import_ws_product_detail(re_notice):
    msg = ''
    success_ids = []
    for j in re_notice:

        p = Product.objects.filter(choies_sku=re_notice[j]['model']).first()
        if p:
            continue
            pass
        else:
            try:
                product = Product()
                product.category_id = re_notice[j]['category']
                product.name = re_notice[j]['name']
                product.cn_name = re_notice[j]['cn_name']
                product.cost = re_notice[j]['cost']
                product.manager_id = 1
                product.choies_sku = re_notice[j]['model']
                product.weight = re_notice[j]['weight']
                product.description = re_notice[j]['size']
                product.choies_supplier_name = re_notice[j]['supplier_name']
                product.choies_site_url = re_notice[j]['site_url']
                product.price=re_notice[j]['other']
                product.save()
                success_ids.append(product.id)

                supplier = Supplier.objects.filter(deleted=False,name=re_notice[j]['supplier_name']).first()
                if not supplier:
                    supplier = Supplier.objects.create(name=re_notice[j]['supplier_name'])

            except Exception,e :
                msg += "失败创建product:%s%s%s |" % (re_notice[j]['model'],re_notice[j]['category'], str(e))

    ### 开始生成item
    products = Product.objects.filter(id__in=success_ids)
    for p in products:       
        product_attributes = ProductAttribute.objects.filter(product_id=p.id).exclude(attribute_id=11)
        for product_attribute in product_attributes:
            options = p.description.split('#')
            for opx in options:
                op = opx.replace('SIZE:', '').replace(' ', '').strip().upper()

                if "ONE" in op:
                    op = 'ONESIZE'
                elif not op:
                    op = 'ONESIZE'
                elif op in ('????', "均码",'???','error'):
                    op = 'ONESIZE'
                elif op == 'X':
                    op = "XL"
                elif len(op) == 3 and op[1:] == 'XL' and op[0] != 'X':
                    try:
                        op = int(op[0]) * 'X' + 'L'
                    except Exception,e:
                        msg += "尺码有误:%s%s%s%s |" % (opx, p.id, p.sku, p.choies_sku)

                # print 'op',op
                try:
                    option = Option.objects.get(name=op,attribute_id=product_attribute.attribute_id)
                    product_attribute.options.add(option)
                except Exception,e:
                    msg += "创建产品失败:%s%s%s%s |" % (opx, p.id, p.sku, p.choies_sku)
    ### update_item
    products = Product.objects.filter(id__in=success_ids)
    # products = Product.objects.filter(id=5393).order_by('id')
    for p in products:
        p.update_items()
        for ii in Item.objects.filter(product_id=p.id,deleted=False):
            key_arrs = ii.key.split("-")[1:]
            # print 'key_arrs',key_arrs
            sku_str = p.choies_sku.upper()
            for k in key_arrs:
                k = int(k)
                if k==0:
                    continue
                product_option = Option.objects.get(pk=k)
                # print product_option
                sku_str = sku_str+'-'+str(product_option.name.upper())
                # print 'sku_str',sku_str
            try:

                Alias.objects.get_or_create(sku=sku_str,channel_id=1,item_id=ii.id)
            except Exception,e:
                msg += "创建item别名失败:%s%s |" % (p.id, str(e))

    return msg

#检查导入的产品
def import_ws_product_detail_notice(reader):
    from product.models import *
    msg = ''
    # reader2 = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
    en_herder = ['model','size','inventory','name','cn_name','category','category_cn_name','supplier_name','cost','total','weight','supplier_link','other','site_url','supplier_sku']
    datas_row = {}
    # header = next(reader2)
    success_ids = []
    j=0
    for row in reader:
        j +=1
        print row
        model = row[0].strip()
        erp_model = Product.objects.filter(choies_sku=model).first()

        row = [i.strip() for i in row]
        res = dict(zip(en_herder, row))
        for key in res.keys():
            if key in ['cost','weight']:
                try:
                    res[key] = float(res[key])
                except Exception,e:
                    res[key]=0
            #售价
            if key in ['other']:
                try:
                    res[key] = res[key].split('|')[0]
                    res[key]=float(res[key])
                except Exception,e:
                    res[key]=0
            #分类id
            if key in ['category']:
                cate = Category.objects.filter(brief__icontains=res['category']).order_by('id').first()
                if not cate:
                    msg += "第%s行无效的分类名称: %s %s |" % (j, row[0], row[5])
                else:
                    res[key] = cate.id

            #size是否存在无法判断！！！

        datas_row[j] = res

    if msg:
        return msg
    else:
        return datas_row


@login_required
@permission_required('lib.import_update_product')
def import_update_product(request):
    data_notice= {}
    if request.POST:
        if request.POST.get("type") == 'bulk_import_product':
            data_error = ''
            data ={}
            if not request.FILES:
                data_error = u'请选择文件后再提交'
                messages.add_message(request, messages.ERROR, data_error)
            else:
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)

                headers = next(reader)#去掉首行
                std_header1 = ['model','size','库存(各种尺码之和)','产品名称','中文名称','category','category中文名称','供货商名称','参考成本','total','重量','链接','others','site_url网站链接','供应商货号']
                std_header = ['\xef\xbb\xbfmodel','size','库存(各种尺码之和)','产品名称','中文名称','category','category中文名称','供货商名称','参考成本','total','重量','链接','others','site_url网站链接','供应商货号']
                en_herder = ['model','size','inventory','name','cn_name','category','category_cn_name','supplier_name','cost','total','weight','supplier_link','other','site_url','supplier_sku']

                if headers != std_header1 and headers != std_header:
                    data_error = u'提交的文件头列表和范本不一致，请确认是否另存为utf-8'
                    print headers,'_________________'
                    print std_header1
                    messages.add_message(request, messages.ERROR, data_error)
                else:

                    re_notice = import_ws_product_detail_notice(reader)#检查数据
                    if type(re_notice)==str:
                        messages.add_message(request, messages.ERROR, re_notice)
                    else:
                        insert_re = import_ws_product_detail(re_notice)#新增产品数据
                        if insert_re:
                            #下载表格,错误提示
                            response, writer = write_csv("bulk_import_product_error")
                            writer.writerow(['error model'])
                            data_array = insert_re.split('|')
                            for p in data_array:
                                writer.writerow([p])
                            return response
                        else:
                            messages.add_message(request, messages.SUCCESS, u"产品导入成功，请再次更新产品完善捆绑供应商")

        elif request.POST.get("type") == 'import_update_product':
            data_error = ''
            msg=''
            datas_row = {}
            if not request.FILES:
                data_error = u'请选择文件后再提交'
                messages.add_message(request, messages.ERROR, data_error)
            else:
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)

                headers = next(reader)#去掉首行
                std_header1 = ['model','size','库存(各种尺码之和)','产品名称','中文名称','category','category中文名称','供货商名称','参考成本','total','重量','链接','others','site_url网站链接','供应商货号']
                std_header = ['\xef\xbb\xbfmodel','size','库存(各种尺码之和)','产品名称','中文名称','category','category中文名称','供货商名称','参考成本','total','重量','链接','others','site_url网站链接','供应商货号']
                en_herder = ['model','size','inventory','name','cn_name','category','category_cn_name','supplier_name','cost','total','weight','supplier_link','other','site_url','supplier_sku']

                if headers != std_header and headers != std_header1:

                    data_error +=u"表格与范本不一致,可能是没有另存为utf-8  |"
                    messages.add_message(request, messages.ERROR, data_error)
                else:
                    j=0
                    for row in reader:
                        j +=1
                        print row
                        model = row[0].strip()
                        erp_model = Product.objects.filter(choies_sku=model).first()
                        if not erp_model:
                            data_error +=u"ERROR,%s model号在新系统里不存在,无法更新  |"% model

                        row = [i.strip() for i in row]
                        res = dict(zip(en_herder, row))
                        for key in res.keys():
                            if key in ['cost']:
                                try:
                                    res[key] = float(res[key])
                                except Exception,e:
                                    res[key]=0
                                # res[key] = res[key] or 0#如果不是数字会报错
                        datas_row[j] = res

                if not data_error:
                    for k in datas_row:
                        # print '777',k
                        # print datas_row[k]
                        erp_model = Product.objects.get(choies_sku=datas_row[k]['model'])
                        erp_model.name = datas_row[k]['name']
                        erp_model.cn_name=datas_row[k]['cn_name']
                        erp_model.cost = datas_row[k]['cost']
                        if not datas_row[k]['supplier_name']:
                            erp_model.choies_supplier_name = datas_row[k]['supplier_name']
                        erp_model.save()
                        if not datas_row[k]['supplier_name']:
                            continue


                        supplier = Supplier.objects.filter(name=datas_row[k]['supplier_name'],deleted=False).first()
                        if supplier:
                            SupplierProduct.objects.filter(product_id=erp_model.id,deleted=False).update(order=10)
                            sp = SupplierProduct.objects.filter(supplier_id=supplier.id,product_id=erp_model.id,deleted=False).first()
                            if sp:
                                sp.supplier_sku=datas_row[k]['supplier_sku']
                                sp.site_url=datas_row[k]['supplier_link']
                                sp.order=1
                                sp.save()
                            else:
                                SupplierProduct.objects.create(supplier_id=supplier.id,product_id=erp_model.id,supplier_sku=datas_row[k]['supplier_sku'],site_url=datas_row[k]['supplier_link'],order=1)

                        else:
                            SupplierProduct.objects.filter(product_id=erp_model.id,deleted=False).update(order=10)
                            supplier_id = Supplier.objects.create(name=datas_row[k]['supplier_name'])
                            SupplierProduct.objects.create(supplier_id=supplier_id.id,product_id=erp_model.id,supplier_sku=datas_row[k]['supplier_sku'],site_url=datas_row[k]['supplier_link'],order=1)
                        # msg +=u"%s 产品和%s 供应商的信息已更新"%(datas_row[k]['model'],datas_row[k]['supplier_name'])
                    messages.add_message(request, messages.SUCCESS, u"%s 文件里的%s 行产品更新成功"% (filename,j))
                else:
                    # messages.add_message(request, messages.ERROR, data_error)
                    #下载表格,错误提示
                    response, writer = write_csv("import_update_product_error")
                    writer.writerow(['error model'])
                    data_array = data_error.split('|')
                    for p in data_array:
                        writer.writerow([p])
                    return response

    return TemplateResponse(request,'import_update_product.html',{'data_notice':data_notice})


@login_required
@permission_required('lib.import_buyer_product')
def import_buyer_product(request):

    data_notice= {}
    if request.POST:
            data_error = ''
            data ={}
            if not request.FILES:
                data_error = u'请选择文件后再提交'
                messages.add_message(request, messages.ERROR, data_error)
            else:
                datas = request.FILES['csvFile']
                filename = datas.name.split('.')[0]
                csvdata = StringIO.StringIO(datas.read())
                reader = csv.reader(csvdata)

                headers = next(reader)#去掉首行

                std_header1 = ['产品分类','产品中文名称','颜色','尺码','产品净重','尺码描述','材质','供应商ID','供应商名称','供应商货号','择尚拿货价','供应商提供的参考库存','快递费用','[备注]','[是否有弹性(0:否,1:是)]','[拉链(0:无,1:前拉链,2:侧,3后)]','[是否透明(0:否,1:是)]','[配件说明]']
                std_header = ['\xef\xbb\xbf产品分类','产品中文名称','颜色','尺码','产品净重','尺码描述','材质','供应商ID','供应商名称','供应商货号','择尚拿货价','供应商提供的参考库存','快递费用','[备注]','[是否有弹性(0:否,1:是)]','[拉链(0:无,1:前拉链,2:侧,3后)]','[是否透明(0:否,1:是)]','[配件说明]']
                field_header = ['category','cn_name','color','size','weight','description','material','supplier_ID','supplier_name','supplier_sku','supplier_cost','supplier_inventory','shipping_fee','note','note1','note2','note3','note4',]

                # for i in range(1,18):
                #     # print i
                #     if std_header[i] != headers[i]:
                #         data_error +=u',%s表格与范本不一致,可能是没有另外为utf-8'
                if headers != std_header and headers != std_header1:
                    data_error +=u"表格与范本不一致,可能是没有另存为utf-8 |"
                else:
                    j = 0
                    for row in reader:
                        j +=1
                        row = [i.strip() for i in row]
                        res = dict(zip(field_header, row))
                        for key in res.keys():
                            if key in ['supplier_ID','supplier_inventory']:
                                try:
                                    res[key] = int(res[key])
                                except Exception,e:
                                    res[key]=0

                            if key in ['weight','supplier_cost','shipping_fee']:
                                try:
                                    res[key] = float(res[key])
                                except Exception,e:
                                    res[key]=0
                            if key=='size':
                                res['size'] = res['size'].upper()
                            if key in ['category','color']:
                                res[key] = res[key].capitalize()
                        #验证供应商id
                        supplier = Supplier.objects.filter(deleted=False,id=res['supplier_ID']).first()
                        if not supplier:
                            data_error +=u'第%d行的%s供应商id系统不存在 |'% (j+1,res['supplier_ID'])
                        #验证分类和属性
                        cate = Category.objects.get(deleted=False,name=res['category'])
                        try:
                            if res['color']:
                                # attr = cate.attributes.filter(attribute_id=11).values_list('attribute_id', flat=True)
                                option = Option.objects.filter(deleted=False,attribute_id=11,name=res['color']).first()
                                if not option:
                                    data_error +=u'第%d行的%s颜色系统不存在 |'% (j+1,res['color'])

                            if res['size']:
                                diff_size = []
                                table_size = list(set(res['size'].split('#')))
                                attr = cate.attributes.filter(id=cate.id).values_list('id', flat=True)

                                option2 = Option.objects.filter(deleted=False,attribute_id__in=attr).values_list('name', flat=True)
                                diff_size = list(set(table_size).difference(set(option2)))
                                diff_size_str = ','.join(diff_size)
                                if diff_size:
                                    data_error +=u'第%d行的%s尺码系统不存在 |'% (j+1,diff_size_str)
                        except Category.DoesNotExist:
                            data_error +=u'第%d行的%s产品分类名称系统不存在 |'% (j+1,res['category'])
                        data[j] = res

                    #验证结束
                if data_error:
                    # messages.add_message(request, messages.ERROR, data_error)
                    #下载表格,错误提示
                    response, writer = write_csv("import_buyer_product_error")
                    writer.writerow(['error notice'])
                    data_array = data_error.split('|')
                    for p in data_array:
                        writer.writerow([p])
                    return response
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

                    messages.add_message(request, messages.SUCCESS, u'%s表格中的产品已全部上传：%d'% (filename,j))
    return TemplateResponse(request,'import_buyer_product.html',{'data_notice':data_notice})


def import_ws_product(request):
    data_notice= {}
    if request.POST:
        
        if request.POST.get("type") == 'import_product_cost':
            msg = ''
            reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
            header = next(reader)
            for row in reader:
                for j in range(0,3):
                    # row[j] = row[j].decode('gbk').encode('utf-8')#不要相信业务提供的表格
                    row[j] = row[j].strip()
                    if j == 3:
                        try:
                           row[j]=float(row[j])
                        except Exception,e:
                            row[j] = 0

                alias = Alias.objects.filter(sku=row[0]).first()
                if alias:
                    msg +="SUCCESS,%s |"% row[0]
                    if row[3]>0:
                        DepotInLog.objects.filter(depot_id=2,item=alias.item,type=4).update(cost=row[3])
                        try:
                            depotitem = DepotItem.objects.get(depot_id=2,item=alias.item)

                            depotin_cost = DepotInLog.objects.filter(depot_id=2,item=alias.item,type=4).first()
                            if depotin_cost:
                                depotitem.total = depotitem.qty * float(row[3])
                                depotitem.save()

                        except depotitem.DoesNotExist:
                            pass

                else:
                    msg +="ERROR,%s,alias not exist |"% row[0]

            if msg:
                #下载表格
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="import_product_cost_errors.csv"'

                writer = csv.writer(response)
                writer.writerow(['product_sku'])
                datas = msg.split('|')
                for pd in datas:
                    writer.writerow([pd])
                return response


        if request.POST.get("type") == 'import_product_material':
            msg = ''
            reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
            header = next(reader)
            for row in reader:
                for j in range(0,1):
                    # row[j] = row[j].decode('gbk').encode('utf-8')#不要相信业务提供的表格
                    row[j] = row[j].strip()
                p = Product.objects.filter(choies_sku=row[0]).update(material=row[1])
                if p:
                    msg +="SUCCESS,%s |"% row[0]
                else:
                    msg +="ERROR,%s |"% row[0]

            if msg:
                #下载表格
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="import_product_material_errors.csv"'

                writer = csv.writer(response)
                writer.writerow(['product_sku'])
                datas = msg.split('|')
                for pd in datas:
                    writer.writerow([pd])
                return response


        if request.POST.get("type") == "import_used_ky_tracking_no":
            from lib.utils import get_now
            from lib.models import Shipping
            msg = ''
            reader = csv.reader(StringIO.StringIO(request.FILES['csvFile'].read()))
            header = next(reader)
            for ordernum, label, tracking_no in reader:
                order = Order.objects.filter(ordernum=ordernum).first()
                if not order:
                    msg += u'order:%s没找到 |' % ordernum
                    continue

                package = Package.objects.filter(order_id=order.id).first()
                if not package:
                    msg += u'order:%s没有创建packge |' % ordernum
                    continue

                shipping = Shipping.objects.filter(label=label).first()
                if not shipping:
                    msg += u'%s没有对应的shipping |' % label
                    continue

                package.shipping = shipping
                package.tracking_no = tracking_no
                package.option_log += u'\n%s在%s 导入了旧的物流信息:%s %s' %(request.user.username, get_now(), label, tracking_no)
                package.save()
            if not msg:
                messages.success(request, u"导入成功")
            else:
                messages.error(request, msg)
    return TemplateResponse(request,'import_ws_product.html',{'data_notice':data_notice})


def ws_img_url(value):
    return "http://ws.jinjidexiaoxuesheng.com/static/pimage/%s.jpg" % (value, )


def tribute_img_url(value):
    """需要将sku解析成正确的图片url"""
    num_str = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'

    a = num_str.index(value[2]) * (34 ** 3)
    b = num_str.index(value[3]) * (34 ** 2)
    c = num_str.index(value[4]) * (34 ** 1)
    d = num_str.index(value[5])

    the_id = a + b + c + d - 393040

    return "http://ws.jinjidexiaoxuesheng.com/media/tributeImages/%s-1.jpg" % the_id


def save_imgs_by_skus(skus):
    msg = ''
    for the_sku in skus:
        try:
            p = Product.objects.get(choies_sku=the_sku)
            p_images = ProductImage.objects.filter(product__choies_sku=the_sku).first()
            if p_images:
                try:
                    file_size = os.path.getsize('media/' + str(p_images.image))
                except Exception, e:
                    photo = p_images
                    file_size = 0

                if file_size:
                    continue
                else:
                    photo = p_images

            else:
                photo = ProductImage()
                photo.product_id = p.id

            try:
                the_url = ws_img_url(the_sku)
                photo.choies_url = the_url
                name = urlparse(the_url).path.split('/')[-1]
                content = ContentFile(urllib2.urlopen(the_url, timeout=5).read())
                photo.image.save(name, content, save=True)
            except Exception, e:
                try:
                    the_url = tribute_img_url(the_sku)
                    photo.choies_url = the_url
                    name = urlparse(the_url).path.split('/')[-1]
                    content = ContentFile(urllib2.urlopen(the_url, timeout=5).read())
                    photo.image.save(name, content, save=True)
                except Exception, e:
                    print str(e)
                    continue

        except Exception, e:
            msg += u'Failure:%s, %s |' % (the_sku, str(e))
