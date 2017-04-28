# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from mptt.models import MPTTModel
import datetime
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings
import os
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
import product

class Depot(models.Model):

    CODE = (
        (0, u'无'),
        (1, u'南京仓'),
        (2, u'广州仓'),
        (3, u'亚马逊海外仓'),
        (4, u'速卖通海外仓'),
    )

    TYPE = (
        (0, u'正常'),
        (1, u'不发货'),
    )

    name = models.CharField(max_length=100, verbose_name=u"仓库名称")
    manager = models.ForeignKey(User, null=True, verbose_name=u"负责人")
    note = models.TextField(default="", blank=True, verbose_name=u"备注")

    # 拣货标识
    code = models.IntegerField(default=0, choices=CODE, verbose_name=u"实际的物理仓")
    type = models.IntegerField(default=0, choices=TYPE, verbose_name=u"仓库类型")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'仓库'
        verbose_name_plural = u'仓库'

    def __unicode__(self):
        return unicode(self.name)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))


class DepotItem(models.Model):
    depot = models.ForeignKey(Depot, verbose_name=u"仓库名称")
    item = models.ForeignKey(product.models.Item, verbose_name=u"分仓货品")
    position = models.CharField(max_length=100, default="",  verbose_name=u"库位")
    qty = models.IntegerField(default=0, verbose_name=u"实际库存量")
    total = models.FloatField(default=0.0,  verbose_name=u"成本", help_text=u"总成本")
    qty_locked = models.IntegerField(default=0, verbose_name=u"已锁库存量")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'分仓货品库存'
        verbose_name_plural = u'分仓货品库存'
        unique_together = ('depot', 'item',)

    def __unicode__(self):
        return u"%s %s" % (self.depot, self.item)
    
    # return in qty
    def item_in(self, qty, cost, note="", obj=None, type=0, operator=None):
            print '222',self.qty,self.total,qty,cost
            self.qty = self.qty + qty
            self.total = self.total + qty*cost
            self.save()
            if qty>0:
                print qty,cost,obj,note,operator,type
                DepotInLog.objects.create(depot=self.depot, item=self.item, qty=qty, cost=cost, content_object=obj, note=note, operator=operator, type=type)
            return self.qty

    # return qty
    def item_out(self, qty, note="", obj=None, type=0, operator=None):
        if self.qty_unlocked - qty < 0:
            return 0
        else:
            cost = round(self.total / self.qty, 2)
            total = cost * qty
            self.total = self.total - total
            self.qty = self.qty - qty
            self.save()
            if qty>0:
                DepotOutLog.objects.create(depot=self.depot, item=self.item, qty=qty, cost=cost, content_object=obj, note=note, operator=operator, type=type)
            return qty

    @property
    def qty_unlocked(self):
        return self.qty - self.qty_locked

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class DepotInLog(models.Model):

    TYPE = (
        (0, u'订单采入库'),
        (1, u'大批活动采入库'),
        (2, u'囤货入库'),
        (3, u'样品采入库'),
        (4, u'移库入库'),
        (5, u'杂入-made系统'),
        (6, u'杂入-新品？'),
        (7, u'杂入-生产手动？'),
        (8, u'杂入-订单退件'),
        (9, u'杂入-包裹取消'),
        (10, u'杂入-FBA调拨'),
        (11, u'杂入-换sku'),
        (12, u'杂入-改码'),
        (13, u'杂入-盘盈'),
        (14, u'杂入-福袋礼物'),
        (15, u'杂入-复检？'),

    )

    depot = models.ForeignKey(Depot, verbose_name=u"仓库")
    item = models.ForeignKey(product.models.Item, verbose_name=u"货品")
    operator = models.ForeignKey(User, verbose_name=u"入库操作者")
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.IntegerField(default=0, verbose_name=u"入库数量")
    cost = models.FloatField(default=0.0,  verbose_name=u"入库成本", help_text=u"单件成本")
    note = models.TextField(default="", blank=True,  verbose_name=u"备注")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"入库类型")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'入库纪录'
        verbose_name_plural = u'入库纪录'

    # #新增入库单表时，影响库存表depot_item
    # def update_depot_item_in(self):
    #     depot_item, is_created = DepotItem.objects.get_or_create(depot=self.depot, item=self.item)
    #     depot_item.qty = depot_item.qty + self.qty
    #     depot_item.total = self.cost * self.qty
    #     depot_item.save()

    def save(self, *args, **kwargs):
        super(DepotInLog, self).save(*args, **kwargs)
        #self.update_depot_item_in()

    def __unicode__(self):
        return u"%s %s" % (self.depot, self.item)

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class DepotOutLog(models.Model):

    TYPE = (
        (0, u'订单销售出库'),
        (1, u'移库'),
        (2, u'杂出-改码'),
        (3, u'杂出-复检？'),
        (4, u'杂出-拍照样衣'),
        (5, u'杂出-盘亏'),
        (6, u'杂出-亚马逊FBA调拨？'),
        (7, u'杂出-速卖通海外仓调拨？'),
        (8, u'杂出-改成本出库'),
        (9, u'杂出-广州电商？'),
        (10, u'杂出-质量问题出库'),
        (11, u'杂出-重复入库？'),
        (12, u'杂出-误对单货物/验单错误？'),
        (13, u'杂出-福袋礼物？'),

    )

    depot = models.ForeignKey(Depot, verbose_name=u"仓库")
    item = models.ForeignKey(product.models.Item, verbose_name=u"货品")
    operator = models.ForeignKey(User, verbose_name=u"出库人员")
    content_type = models.ForeignKey(ContentType, blank=True, null=True)
    object_id = models.PositiveIntegerField(blank=True, null=True)
    content_object = GenericForeignKey('content_type', 'object_id')
    qty = models.IntegerField(default=0, verbose_name=u"出库数量")
    cost = models.FloatField(default=0.0, verbose_name=u"出库成本", help_text=u"单件成本")
    note = models.TextField(default="", blank=True, verbose_name=u"备注")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"出库类型")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True,  verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'出库纪录'
        verbose_name_plural = u'出库纪录'

    # #新增出库单表时，影响库存表depot_item
    # def update_depot_item_out(self):
    #     depot_item, is_created = DepotItem.objects.get_or_create(depot=self.depot, item=self.item)
    #     depot_item.qty = depot_item.qty - self.qty
    #     depot_item.save()

    def save(self, *args, **kwargs):
        super(DepotOutLog, self).save(*args, **kwargs)
        #self.update_depot_item_out()

    def __unicode__(self):
        return u"%s %s" % (self.depot, self.item)

# 分拣异常记录
#class PickError(models.Model):
#    pick = models.ForeignKey(Pick, verbose_name=u'异常拣货单')
#    package_id = models.IntegerField(default=0, verbose_name=u'包裹单')
#    item_list = models.TextField(default="", verbose_name=u'包裹物品列表')
#    created = models.DateTimeField(auto_now_add=True, verbose_name=u'包裹单新增时间')
#    is_process = models.BooleanField(u'是否处理', default=False)
#
#    class Meta:
#        verbose_name = u'拣货异常记录单'
#        verbose_name_plural = u'拣货异常记录单'

# class InPackage(models.Model):
#     STATUS = (
#         (0, u'未分拣'),
#         (1, u'分拣中'),
#         (2, u'分拣完成'),
#         (3, u'发货完成'),
#         (4, u'包装完成'),
#     )
#
#     TYPE = (
#         (0, u'捡货单'),
#         (1, u'入库单'),
#     )
#
#     status = models.IntegerField(u'拣货状态', choices=STATUS, default=0)
#     type = models.IntegerField(choices=TYPE, default=0)
#     depot = models.ForeignKey(Depot, verbose_name=u"仓库名称")
#
#     user_adder = models.ForeignKey(User, null=True, blank=True, verbose_name=u'新增拣货单人员')
#
#     is_print = models.BooleanField(u'是否打印', default=False)
#     print_time = models.DateTimeField(u'拣货单打印时间', blank=True, null=True)
#
#     #assigner = models.ForeignKey(User, null=True, blank=True, related_name="pick_assigner", verbose_name=u'拣货人') #拣货人
#     assign_time = models.DateTimeField(u'拣货日期', blank=True, null=True)
#
#     pick_start = models.DateTimeField(u'分拣开始时间', blank=True, null=True)
#     pick_end = models.DateTimeField(u'分拣结束时间', blank=True, null=True)
#
#     is_error = models.BooleanField(u'是否分拣异常', default=False)
#
#     created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
#     updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
#     deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
#
#     class Meta:
#         verbose_name = u'入库单'
#         verbose_name_plural = u'入库单'
#
# class InPackageItem(models.Model):
#     inpackage = models.ForeignKey(InPackage, verbose_name=u'拣货单')
#     item = models.ForeignKey(product.models.Item, null=True, verbose_name=u'拣货单物品')
#     qty = models.IntegerField(default=0, verbose_name=u'拣货物品数量')
#
#     created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
#     updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
#     deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
#
#     class Meta:
#         verbose_name = u'入库单物品'
#         verbose_name_plural = u'入库单物品'


class Pick(models.Model):

    PICK_TYPES = (
        (0, u'无'),
        (1, u'单品单件'),
        (2, u'单品多件'),
        (3, u'多品多件'),
    )

    STATUS = (
        (0, u'未分拣'),
        (1, u'分拣中'),
        (2, u'分拣完成'),
        (3, u'包装完成'),
        (4, u'发货完成'),
        (5, u'取消'),
    )

    TYPE = (
        (0, u'捡货单'),
        (1, u'出库单'),
    )
    pick_num = models.CharField(u'拣货单号', max_length=50, db_index=True, default="")

    status = models.IntegerField(u'拣货状态', choices=STATUS, default=0)
    type = models.IntegerField(choices=TYPE, default=0)
    pick_type = models.IntegerField(u'拣货单类型', choices=PICK_TYPES, default=0)

    code = models.IntegerField(u'物理仓名称', choices=Depot.CODE, default=0)
    shipping = models.CharField(u'物流类型', max_length=50, default="")
    is_error = models.BooleanField(u'是否分拣异常', default=False)
    
    # 打印人和打印时间
    printer = models.ForeignKey(User, blank=True, null=True, related_name="pick_printer", verbose_name=u'打印人')
    print_time = models.DateTimeField(u'拣货单打印时间', blank=True, null=True)

    # 拣货人和拣货时间
    assigner = models.ForeignKey(User, null=True, blank=True, related_name="pick_assigner", verbose_name=u'拣货人')
    assign_time = models.DateTimeField(u'拣货时间', blank=True, null=True)

    # 分拣人和分拣的开始及结束时间
    picker = models.ForeignKey(User, blank=True, null=True, related_name="pick_picker", verbose_name=u"分拣人")
    pick_start = models.DateTimeField(u'分拣开始时间', blank=True, null=True)
    pick_end = models.DateTimeField(u'分拣结束时间', blank=True, null=True)

    # 多多特有:包装人和包装时间
    packager = models.ForeignKey(User, blank=True, null=True, related_name="pick_packager", verbose_name=u'包装人')
    package_start = models.DateTimeField(u"多多包装开始时间", blank=True, null=True)
    package_end = models.DateTimeField(u"多多包装结束时间", blank=True, null=True)

    # 拣货单创建人和创建时间
    user_adder = models.ForeignKey(User, null=True, blank=True, related_name="pick_user_adder", verbose_name=u'添加人员')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    class Meta:
        verbose_name = u'拣货单'
        verbose_name_plural = u'拣货单'

    def __unicode__(self):
        return u"%s" % self.id


class PickItem(models.Model):
    pick = models.ForeignKey(Pick, verbose_name=u'拣货单')
    # item = models.ForeignKey(product.models.Item, null=True, verbose_name=u'拣货单物品')
    #修改字段
    depot_item = models.ForeignKey(DepotItem, null=True, verbose_name=u'拣货单物品')
    qty = models.IntegerField(default=0, verbose_name=u'拣货物品数量')
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    class Meta:
        verbose_name = u'拣货单物品'
        verbose_name_plural = u'拣货单物品'

    def __unicode__(self):
        return u"%s" % self.id


