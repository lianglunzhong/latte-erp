# coding: utf-8
from __future__ import unicode_literals

from django.db import models

# Create your models here.

import product
import shipping

class Product3bao(models.Model):
    product = models.ForeignKey(product.models.Product, verbose_name=u"产品")
    sku = models.CharField(default="", blank=True, max_length=100, verbose_name=u'3宝SKU')
    hs_code = models.CharField(default="", max_length=20, blank=True, verbose_name=u"hs code")
    unit = models.CharField(default="", blank=True, max_length=15)
    f_model = models.CharField(default="", max_length=400, verbose_name=u'规格型号')
    status = models.IntegerField(default=0, blank=True)
    cn_name = models.CharField(default="", max_length=100, blank=True, verbose_name=u"中文名")

    choies_models = models.CharField(default="", blank=True, max_length=300, verbose_name=u"choies对应sku列表") # 一个3bao产品可能对应多个choies的model
    note = models.TextField(default="", blank=True, verbose_name=u"备注")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    def __unicode__(self):
        return u"3宝SKU: %s" % self.sku

    def get_choies_model(self):
        try:
            return self.choies_models.split(',')[0]
        except Exception, e:
            return self.sku


class Package3bao(models.Model):
    package = models.ForeignKey(shipping.models.Package)
    is_tonanjing = models.BooleanField(default=False, verbose_name=u'发往南京')
    is_over = models.BooleanField(default=False, verbose_name=u'海关审结')
    remark = models.TextField(default ="", blank=True, verbose_name=u'备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    def __unicode__(self):
        return u"Package ID: %s" % self.package_id