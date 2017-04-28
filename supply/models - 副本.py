# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from mptt.models import MPTTModel
import datetime
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

import os
import product
import order
import depot
import lib
import uuid
from django.db.models import Sum


class ProductForSupplier(product.models.Product):

    def save(self, *args, **kwargs):
        self.status = 0
        super(ProductForSupplier, self).save(*args, **kwargs)

    class Meta:
        proxy = True
        verbose_name = u'供应商产品'
        verbose_name_plural = u'供应商产品'

class Supplier(models.Model):

    TYPE = (
        (0, u'线下'),
        (1, u'线上'),
        (2, u'工厂'),
    )
    SUPPLY_CLASS = (
        (0, u'A'),
        (1, u'B'),
        (2, u'C'),
        (3, u'D'),
    )

    STATUS = (
        (0, u'未审核'),
        (1, u'已审核'),
        (2, u'关闭'),
    )

    PURCHASE_WAY = (
        (0, u'零采'),
        (1, u'备货/囤货'),
        (2, u'做货'),
    )

    name = models.CharField(max_length=250, verbose_name=u"供应商名称")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"类型")
    site = models.CharField(max_length=250, blank=True, verbose_name=u"供应商访问网址")
    phone = models.CharField(max_length=250, blank=True, default="", verbose_name=u"电话")
    address = models.TextField(default="", blank=True, verbose_name=u"地址")
    note = models.TextField(default="", blank=True, verbose_name=u"备注")
    manager = models.ForeignKey(User, null=True,  verbose_name=u"负责人")
    products = models.ManyToManyField(product.models.Product, blank=True, through='supply.SupplierProduct', verbose_name=u"供应商产品")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    #新增字段
    supplier_class = models.IntegerField(choices=SUPPLY_CLASS, default=0,  verbose_name=u"供应商等级")
    payment_information = models.TextField(default="", blank=True, verbose_name=u"付款资料")
    tax_id = models.CharField(max_length=100, blank=True, verbose_name=u"税务登记号")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u"供应商状态")
    purchase_way = models.IntegerField(choices=PURCHASE_WAY, default=0, verbose_name=u"采购方式")
    category = models.ManyToManyField(product.models.Category,blank=True, verbose_name=u"供应商供应的产品分类", help_text=u"供应商供应的产品分类")
    login_user = models.ForeignKey(User, blank=True, null=True, verbose_name=u"系统登录用户", related_name='supplier_login_user', help_text=u"系统登录用户")


    class Meta(object):
        verbose_name = u'供应商'
        verbose_name_plural = u'供应商'

    def __unicode__(self):
        return "%03d.%s" % (self.id, self.name)

    def supplier_list(self,search,userid):
        if not search:
            return Supplier.objects.filter(deleted=0,manager_id=userid).order_by('id')
        else:
            return Supplier.objects.filter(deleted=0,name__contains=search,manager_id=userid).order_by('id')

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class SupplyImage(models.Model):
    image = models.ImageField(upload_to=product.models.get_product_image_upload_path, verbose_name=u"图片地址")#此处存储图片的规则和产品图片一致，方法直接引用产品图片
    supplier = models.ForeignKey(Supplier, verbose_name=u"供应商名称")

   #img_updater = models.ForeignKey(User, related_name='img_updater', verbose_name=u"修改图片人员")
    img_adder = models.ForeignKey(User, related_name='img_adder', verbose_name=u"新增图片人员")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'供应商三证合一图片'
        verbose_name_plural = u'供应商三证合一图片'

    def __unicode__(self):
        return 'SupplyImage %s' % self.id


class SupplierProduct(models.Model):

    supplier = models.ForeignKey(Supplier, verbose_name=u"供应商名称")
    product = models.ForeignKey(product.models.Product, verbose_name=u"产品名称")
    order = models.PositiveIntegerField(default=1, verbose_name=u"产品绑定的供应商优先级")

    created = models.DateTimeField(auto_now_add=True,verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    # 新增字段
    # purchase_way = models.IntegerField(choices=PURCHASE_WAY, default=0, verbose_name=u"采购方式")#此字段移动到供应商表中
    supplier_period = models.IntegerField(default=0, verbose_name=u"供货周期")
    supplier_cost = models.FloatField(default=0.0, verbose_name=u"供货成本")
    supplier_min_qty = models.IntegerField(default=1, verbose_name=u"起订量")
    supplier_sku = models.CharField(max_length=200, verbose_name="供应商SKU", default='', blank=True)
    supplier_inventory = models.IntegerField(default=0,blank=True, verbose_name=u"供应商的参考库存")
    supplier_shipping_fee = models.FloatField(default=0.0,blank=True, verbose_name=u"物流费用")
    site_url = models.CharField(max_length=250, blank=True, verbose_name=u"供应商产品访问网址")

    class Meta:
        verbose_name = u'供应商产品'
        verbose_name_plural = u'供应商产品'

    def __unicode__(self):
        return "SUPPLYPRODUCT:%s" % self.id

class PurchaseOrder(models.Model):

    PURCHASE_STATUS = (
            (0, u'未处理'),
            (1, u'开始采购'),
            (2, u'完全入库'),
            (3, u'部分入库'),
            (4, u'取消'),
            )
# 暂时没有用，去掉
#     PURCHASE_ACTIVE = (
#             (0, u'未处理'),
#             (1, u'开始采购'),
#             (2, u'完全入库'),
#             (3, u'部分入库'),
#             (4, u'取消'),
#     )

    PURCHASE_CLOSE_STATUS= (
            (0, u'未结算'),
            (1, u'已结算'),
            (2, u'不参与结算'),
            )

    PURCHASE_TYPE = (
        (0, u'零采'),
        (1, u'样品采'),
        (2, u'做货'),
        (3, u'移库'),
    )
    # supplier = models.ForeignKey(Supplier, null=True, blank=True, verbose_name=u"供应商名称")
    supplier = models.ForeignKey(Supplier, verbose_name=u"供应商名称")#供应商不可以为空
    status = models.IntegerField(choices=PURCHASE_STATUS, default=0, verbose_name=u"采购单状态")
    close_status = models.IntegerField(choices=PURCHASE_CLOSE_STATUS, default=0, verbose_name=u"是否已结算")
    total = models.FloatField(default=0, blank=True, null=True, verbose_name=u"采购总成本")
    # active = models.IntegerField(choices=PURCHASE_ACTIVE, default=0, verbose_name=u"采购状态")
    note = models.TextField(default='', blank=True, null=True, verbose_name=u"备注")
    manager = models.ForeignKey(User, null=True, blank=True, verbose_name=u"采购人员")
    # shipping = models.ForeignKey(lib.models.Shipping, blank=True, null=True,default=None)没有用，指向的国际物流方式
    tracking = models.TextField(default='', blank=True, null=True, verbose_name=u"运单号")
    #is_forecast = models.BooleanField('是否囤货 ?', default=False)

    #选择"FBA采购"为True时，"渠道"必需填
    is_fba = models.BooleanField(default=False, verbose_name="FBA采购")
    channel = models.IntegerField(default=0, verbose_name=u"渠道")
    shipping_fee = models.FloatField(default=0, blank=True, null=True, verbose_name=u"采购单运费")

    creater = models.ForeignKey(User, null=True, blank=True, related_name="creater", verbose_name=u"录入单据人员")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    updater = models.ForeignKey(User, null=True, blank=True,related_name="updater", verbose_name=u"修改人员")
    depot = models.ForeignKey(depot.models.Depot, verbose_name=u"采购入库仓库")
    type = models.IntegerField(choices=PURCHASE_TYPE, default=0, verbose_name=u"采购类型")
    parent = models.ForeignKey('self', null=True, blank=True, verbose_name=u"主单")

    _status = None

    class Meta:
        verbose_name = u'采购单'
        verbose_name_plural = u'采购单'

    def __unicode__(self):
        return u"PURCHASE#%s" % self.id

    def __init__(self, *args, **kwargs):
        super(PurchaseOrder, self).__init__(*args, **kwargs)
        self._status = self.status

    def save(self, *args, **kwargs):
        super(PurchaseOrder, self).save(*args, **kwargs)
        if self.type == 2:
            MadeOrder.objects.get_or_create(purchaseorder=self)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class PurchaseOrderItem(models.Model):

    ACTION_STATUS = (
            (0, u'未处理'),
            (1, u'部分对单'),
            (2, u'全部对单'),
            )

    IN_STATUS = (
            (0, u'未处理'),
            (1, u'部分入库'),
            (2, u'完成入库'),
            )

    STATUS = (
            (1, u'正常'),
            (2, u'报缺'),
            (0, u'取消'),
            )

    # tracking = models.CharField(max_length=250, default="", blank=True, verbose_name=u"运单号")#暂时没有用去掉
    status = models.IntegerField(default=1, choices=STATUS, verbose_name=u"处理状态")
    action_status = models.IntegerField(default=0, choices=ACTION_STATUS, verbose_name=u"对单状态")
    in_status = models.IntegerField(default=0, choices=IN_STATUS, verbose_name=u"入库状态")
    purchaseorder = models.ForeignKey(PurchaseOrder, blank=True, null=True, verbose_name=u"采购单id")
    item = models.ForeignKey(product.models.Item, verbose_name=u"item_id")
    qty = models.IntegerField(default=0, verbose_name=u"采购数量")
    cost = models.FloatField(default=0, verbose_name=u"采购单价")
    note = models.TextField(default='', blank=True, null=True, verbose_name=u"备注")
    # purchaser = models.ForeignKey(User, null=True, blank=True,related_name="purchaser", verbose_name=u"采购人员")
    real_qty = models.IntegerField('对单数量', default=0)
    # signer = models.ForeignKey(User, null=True, blank=True, related_name="signer", verbose_name=u"签收人员")
    # sign_time = models.DateTimeField(null=True, blank=True, verbose_name=u"签收时间")
    #imperfect_status = models.IntegerField('残次状态', choices=IMPERFECT_STATUS, default=1)
    estimated_date = models.DateField(blank=True, null=True, verbose_name=u"估计到货时间")
    #新增字段
    depotinlog_qty = models.IntegerField(default=0, verbose_name=u"实际入库数量")
    depot = models.ForeignKey(depot.models.Depot, null=True,verbose_name=u"采购入库仓库")
    supplier = models.ForeignKey(Supplier, null=True, blank=True, verbose_name=u"供应商名称")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    _status = None
    _checked = None
    _qty = 0
    _real_qty = 0
    _cost = 0

   #class Meta:
   #    unique_together = ('purchase_order', 'item',)

    class Meta:
        verbose_name = u'采购单货品'
        verbose_name_plural = u'采购单货品'

    def __unicode__(self):
        if self.purchaseorder:
            return u"%s / %s" % (self.item.sku, self.purchaseorder.id)
        else:
            return u"%s / %s" % (self.item.sku, 0)

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderItem, self).__init__(*args, **kwargs)
        self._status = self.status
        #self._checked = self.checked
        self._qty = self.qty
        self._real_qty = self.real_qty
        self._depotinlog_qty = self.depotinlog_qty
        self._cost = self.cost

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def update_purchaseorder_status(self):
        # print self.status,self.purchaseorder.id
        # if self.status == 0:
        #     return False
        print 'update_purchaseorder_status'
        poi_status = PurchaseOrderItem.objects.filter(purchaseorder=self.purchaseorder).exclude(action_status=5).values_list('action_status', flat=True)
        poi_status2 = list(set(poi_status))
        print poi_status2
        if len(poi_status2) == 0:
            PurchaseOrder.objects.filter(id=self.purchaseorder_id).update(status=4)
        else:
            if 4 in poi_status2 and len(poi_status2) == 1:
                PurchaseOrder.objects.filter(id=self.purchaseorder_id).update(status=2)
            elif 3 in poi_status2 or 4 in poi_status2:
                PurchaseOrder.objects.filter(id=self.purchaseorder_id).update(status=3)

    def update_purchaseorder_cost(self):
        print 'update_purchaseorder_cost'
        # poi_sun_cost = PurchaseOrderItem.objects.filter(purchaseorder=self.purchaseorder).extra(select = {'total': 'SUM(qty * cost)'})#测试服务器上此方法报错
        # if poi_sun_cost and poi_sun_cost[0].total>0:
        #     PurchaseOrder.objects.filter(id=self.purchaseorder_id).update(total=poi_sun_cost[0].total)
        pois = PurchaseOrderItem.objects.filter(purchaseorder=self.purchaseorder).exclude(action_status=5)
        total = 0
        for poi in pois:
            total +=poi.qty * poi.cost
        if total>0:
            PurchaseOrder.objects.filter(id=self.purchaseorder_id).update(total=total)

    def save(self, *args, **kwargs):

        if self.depotinlog_qty > 0 and self.qty == self.depotinlog_qty:
            self.status = 4
        elif self.depotinlog_qty > 0 and self.qty > self.depotinlog_qty:
            self.status = 3
        elif self.real_qty > 0 and self.qty == self.real_qty:
            self.status = 2
        elif self.real_qty > 0 and self.qty > self.real_qty:
            self.status = 1
        self.update_purchaseorder_status()#根据采购物品的状态修改采购单状态
        super(PurchaseOrderItem, self).save(*args, **kwargs)
        self.update_purchaseorder_cost()#采购物品成本影响采购单成本


class PurchaseOrderCheckedItem(models.Model):
    PURCHASE_ORDER_CHECKED_ITEM_STATUS = (
            (0, u'未处理'),
            (1, u'部分入库'),
            (2, u'完全入库'),
            (3, u'取消'),
            )
    purchaseorder = models.ForeignKey(PurchaseOrder, verbose_name=u"采购单")
    purchaseorderitem = models.ForeignKey(PurchaseOrderItem, verbose_name=u"采购单条目")
    qty = models.IntegerField(default=0, verbose_name=u"对单数量")
    note = models.TextField(default='', blank=True, null=True, verbose_name=u"备注")
    add_user = models.ForeignKey(User, null=True, blank=True, related_name="PurchaseOrderCheckedItem_add_user", verbose_name=u"对单人员")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    #新增字段
    depotinlog_qty = models.IntegerField(default=0, verbose_name=u"实际入库数量")
    status = models.IntegerField(default=0, choices=PURCHASE_ORDER_CHECKED_ITEM_STATUS, verbose_name=u"入库状态")

    _qty = 0
    _deleted = False

    def __init__(self, *args, **kwargs):
        super(PurchaseOrderCheckedItem, self).__init__(*args, **kwargs)
        self._qty = self.qty
        self._depotinlog_qty = self.depotinlog_qty
        self._deleted = self.deleted

    class Meta:
        verbose_name = u'采购单对单'
        verbose_name_plural = u'采购单对单'

    def save(self, *args, **kwargs):
        if not self.deleted:
            #修改状态
            if self.status!=3 and self.depotinlog_qty!=0 and self.qty==self.depotinlog_qty:
                self.status=2
            elif self.status!=3 and self.depotinlog_qty!=0 and self.qty > self.depotinlog_qty:
                self.status=1

            depotinlog_qty_added =  self.depotinlog_qty - self._depotinlog_qty
            if depotinlog_qty_added != 0:
                self.purchaseorderitem.depotinlog_qty = self.purchaseorderitem.depotinlog_qty + depotinlog_qty_added#入库数量的变化
                self.purchaseorderitem.save()

        else:
            self._delete()
        super(PurchaseOrderCheckedItem, self).save(*args, **kwargs)

    def _delete(self):
        if self._qty != 0:
            self.purchaseorderitem.real_qty = self.purchaseorderitem.real_qty - self._qty
            self.purchaseorderitem.save()
        if self._depotinlog_qty != 0:
            self.purchaseorderitem.depotinlog_qty = self.purchaseorderitem.depotinlog_qty - self._depotinlog_qty
            self.purchaseorderitem.save()

    def delete(self, *args, **kwargs):
        self._delete()
        super(PurchaseOrderCheckedItem, self).delete(*args, **kwargs)

class PurchaseOrderQualityTesting(models.Model):

    STATUS = (
            (0, u'破洞'),
            (1, u'污迹'),
            (2, u'材质不符'),
            (3, u'其它'),
            )


    purchaseorder = models.ForeignKey(PurchaseOrder, verbose_name=u"采购单")
    purchaseorderitem = models.ForeignKey(PurchaseOrderItem, verbose_name=u"采购单条目")
    status = models.IntegerField(default=0, choices=STATUS, verbose_name=u"类型")
    qty = models.IntegerField(default=0, verbose_name=u"采购数量")
    note = models.TextField(default='', blank=True, null=True, verbose_name=u"备注")
    add_user = models.ForeignKey(User, null=True, blank=True, related_name="PurchaseOrderQualityTesting_add_user", verbose_name=u"对单人员")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'采购单对单问题记录'
        verbose_name_plural = u'采购单对单问题记录'


class ItemForSupplier(product.models.Item):
    class Meta:
        proxy = True
        verbose_name = u'供应商货品'
        verbose_name_plural = u'供应商货品'

class PurchaseRequest(models.Model):

    STATUS = (
            (0, u'未处理'),
            (1, u'开始处理'),
            (2, u'完成'),
            (3, u'废除'),
        )

    name = models.CharField(max_length=200, verbose_name=u"标题")
    depot = models.ForeignKey(depot.models.Depot, verbose_name=u"仓库")
    note = models.TextField(blank=True, verbose_name=u"详细备注")
    manager = models.ForeignKey(User, null=True,  verbose_name=u"负责人", related_name="purchaserequest_manager")
    add_user = models.ForeignKey(User, null=True,  verbose_name=u"发起人", related_name="purchaserequest_add_user")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u"状态")
    #products = models.ManyToManyField(Product, blank=True, verbose_name=u"产品")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    # 新增字段
    active_time = models.DateTimeField(verbose_name=u"有效时间")
    related_sku_note = models.TextField(blank=True, verbose_name=u"关联产品的备注", help_text='批量管理产品，用英文,分割，捆绑成功的产品将从此字段中消失，否则是未成功的')

    class Meta:
        verbose_name = u'采购方案'
        verbose_name_plural = u'采购方案'

    def __unicode__(self):
        return u'%s-%s' % (self.id,self.name)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

# 采购方案绑定属性产品
    def related_item(self):
        items = self.related_sku_note.split(',')
        # print products
        str = ''
        for pro in items:
            pro = pro.strip()
            try:
                item = product.models.Item.objects.get(sku=pro)
                i = PurchaseRequestItem.objects.get_or_create(purchaserequest_id=self.id,qty=1,item_id=item.id)
            except:
                str = str + pro + ',\n'
        return str

class PurchaseRequestItem(models.Model):
    purchaserequest = models.ForeignKey(PurchaseRequest, verbose_name=u"采购方案")
    item = models.ForeignKey(product.models.Item, verbose_name=u"物品")
    qty = models.PositiveIntegerField(default=1, verbose_name=u"购买数量")
    note = models.TextField(default="", blank=True, verbose_name=u"备注")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    #新增字段
    purchaseorderitem = models.ForeignKey('supply.PurchaseOrderItem', null=True, blank=True,verbose_name=u"采购物品 / 采购单id")

    class Meta:
        verbose_name = u'采购方案条目'
        verbose_name_plural = u'采购方案条目'

    # @property
    # def symbol(self):
    #     return get_symbol(self.currency)

    def __unicode__(self):
        return str(self.id)

class MadeOrder(models.Model):

    STATUS = (
        (0, u'未审核'),
        (1, u'已审核'),
        (2, u'取消'),
    )

    PROCESS_STATUS = (
        (0, u'下单'),
        (1, u'审版'),
        (2, u'面辅料'),
        (3, u'车间上线'),
        (4, u'发货'),
        (5, u'完成'),
    )

    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u"状态")
    process = models.IntegerField(choices=PROCESS_STATUS, default=0, verbose_name=u"生产环节")
    purchaseorder = models.OneToOneField(PurchaseOrder, verbose_name=u"单据")
    manager = models.ForeignKey(User, null=True,  verbose_name=u"负责人")

    factory_date = models.DateField(null=True,blank=True, verbose_name=u"下单到工厂日期")
    check_template_date = models.DateField(null=True,blank=True, verbose_name=u"审版日期")
    material_prepare_date = models.DateField(null=True,blank=True, verbose_name=u"面辅料到工厂日期")
    produce_date = models.DateField(null=True,blank=True, verbose_name=u"车间上线日期")
    estimated_date = models.DateField(null=True,blank=True, verbose_name=u"预计发货日期")
    end_date = models.DateField(null=True,blank=True, verbose_name=u"实际送货日期")
    note = models.TextField(default="", blank=True, verbose_name=u"备注")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    #deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'生产流程'
        verbose_name_plural = u'生产流程'

    # @property
    # def symbol(self):
    #     return get_symbol(self.currency)

    def __unicode__(self):
        return str(self.id)
