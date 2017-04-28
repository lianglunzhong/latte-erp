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
import supply


class FbaSku(models.Model):
    fba_sku = models.CharField(max_length=100, blank=True, null=True)
    fn_sku = models.CharField(max_length=100)
    sku = models.CharField(max_length=100)
    item = models.ForeignKey(product.models.Item, null=True)
    title = models.CharField(max_length=100, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")

    class Meta:
        verbose_name = u'FBA-SKU对照表'
        verbose_name_plural = u'FBA-SKU对照表'

class FbaStock(models.Model):
    channel = models.ForeignKey(order.models.Channel, verbose_name=u"渠道账号")
    item = models.ForeignKey(product.models.Item, null=True)
    warehouse = models.IntegerField(default=0, verbose_name=u"在库总库存") #在库总库存=可用库存+不可用库存+预留库存
    fulfillable = models.IntegerField(default=0, verbose_name=u"可用库存")
    unsellable = models.IntegerField(default=0, verbose_name=u"不可用库存")
    reserved = models.IntegerField(default=0, verbose_name=u"预留库存")
    inboud = models.IntegerField(default=0, verbose_name=u"在途")
    total = models.IntegerField(default=0, verbose_name=u"总库存") #总库存=在库总库存+在途
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"创建时间")

    class Meta:
        verbose_name = u'FBA库存表'
        verbose_name_plural = u'FBA库存表'

class FbaForecast(models.Model):
    channel = models.ForeignKey(order.models.Channel, verbose_name=u"渠道账号")
    item = models.ForeignKey(product.models.Item)
    forecast_type = models.CharField(max_length=50, null=True, blank=True, verbose_name=u"囤货类型")
    sales_7 = models.IntegerField(default=0, verbose_name=u"7天销量")
    can_stock = models.IntegerField(default=0, verbose_name=u"可用库存")
    now_stock = models.IntegerField(default=0, verbose_name=u"当前库存")
    safe_stock = models.FloatField(default=0.0, verbose_name=u"安全库存")
    purchase_item_qty = models.IntegerField(default=0, verbose_name=u"采购中数量")
    fore_qty = models.FloatField(default=0.0, verbose_name=u"预测囤货量")
    real_qty = models.FloatField(default=0.0, verbose_name=u"实际囤货量")
    assigner = models.ForeignKey(User, null=True)
    is_purchase = models.BooleanField(default=False, verbose_name=u"采购负责人")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"创建时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'FBA预测囤货'
        verbose_name_plural = u'FBA预测囤货'
