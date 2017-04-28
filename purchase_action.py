# -*- coding: utf-8 -*-
import csv

import datetime
from django.utils import timezone
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')

sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()

from django.contrib.auth.models import User
from shipping.models import ItemWanted
from supply.models import *

# get all itemwanted, and itemrequested

from depot.models import Depot


def action_create_purchaseorder():
    for depot in Depot.objects.filter(deleted=False).filter(type=0):
        # print u'%s'% depot
        # 获得未处理的订单采购需求
        itemwanteds = ItemWanted.objects.filter(deleted=False).filter(depot=depot).filter(purchaseorderitem=None)

        itemwanted = ItemWanted()
        itemwanted.qty =0

        for itemwanted in itemwanteds:
            supplier_id = 0
            # supplierproduct = SupplierProduct.objects.filter(order=1,deleted=False,product=itemwanted.item.product).first()
            # if supplierproduct:
            #     supplier_id = supplierproduct.supplier_id
            # else:
            #     supplier_id = 1
            # print supplierproduct
            supplier_product = itemwanted.item.product.get_default_supply_product()
            if supplier_product:
                supplier_id = supplier_product.supplier_id
            else:
                supplier_id = 1
            print supplier_product

            try:
                purchaseorderitem = PurchaseOrderItem.objects.get(purchaseorder=None, depot=depot, item=itemwanted.item)
            except PurchaseOrderItem.DoesNotExist:
                purchaseorderitem = PurchaseOrderItem()
                purchaseorderitem.purchaseorder=None
                purchaseorderitem.depot=depot
                purchaseorderitem.supplier_id=supplier_id
                purchaseorderitem.item=itemwanted.item
                purchaseorderitem.cost=itemwanted.item.product.cost

            purchaseorderitem.qty = purchaseorderitem.qty + itemwanted.qty
            purchaseorderitem.save()
            itemwanted.purchaseorderitem = purchaseorderitem
            itemwanted.save()

        # purchaserequestitems = PurchaseRequestItem.objects.filter(deleted=False).filter(PurchaseOrder.depot=depot).filter(PurchaseOrder.status=1).filter(purchaseorderitem=None)
        purchaserequestitems = PurchaseRequestItem.objects.filter(deleted=False).filter(purchaserequest__depot=depot).filter(purchaserequest__status=1).filter(purchaseorderitem=None)
        for purchaserequestitem in purchaserequestitems:
            # supplierproduct = SupplierProduct.objects.filter(order=1,deleted=False,product=purchaserequestitem.item.product).first()
            # if supplierproduct:
            #     supplier_id = supplierproduct.supplier_id
            # else:
            #     supplier_id = 1
            # print supplierproduct
            supplier_product = purchaserequestitem.item.product.get_default_supply_product()
            if supplier_product:
                supplier_id = supplier_product.supplier_id
            else:
                supplier_id = 1
            print supplier_product

            try:
                purchaseorderitem = PurchaseOrderItem.objects.get(purchaseorder=None, purchaseorder__depot=depot, item=purchaserequestitem.item)

            except PurchaseOrderItem.DoesNotExist:
                purchaseorderitem = PurchaseOrderItem()
                purchaseorderitem.purchaseorder=None
                # purchaseorderitem.qty=purchaserequestitem.qty
                purchaseorderitem.depot=depot
                purchaseorderitem.supplier_id=supplier_id
                purchaseorderitem.item=purchaserequestitem.item
                purchaseorderitem.cost=purchaserequestitem.item.product.cost

            purchaseorderitem.qty = purchaseorderitem.qty + purchaserequestitem.qty
            purchaseorderitem.save()
            purchaserequestitem.purchaseorderitem = purchaseorderitem
            purchaserequestitem.save()
            PurchaseRequest.objects.filter(pk=purchaserequestitem.purchaserequest_id).update(status=2)

    #根据depot和supplier生成purchaseorder
    pois = PurchaseOrderItem.objects.filter(purchaseorder=None).values('depot','supplier').distinct()
    for poi in pois:
        supplier = Supplier.objects.filter(deleted=False,id=poi['supplier']).first()
        if supplier and supplier.type==2:
            p_type=2
        else:
            p_type=0
        po = PurchaseOrder.objects.create(supplier_id=poi['supplier'],type=p_type,creater_id=1,depot_id=poi['depot'],manager=supplier.manager)
        PurchaseOrderItem.objects.filter(purchaseorder=None,supplier_id=poi['supplier'],depot_id=poi['depot']).update(purchaseorder=po.id)

    return 'ok'
