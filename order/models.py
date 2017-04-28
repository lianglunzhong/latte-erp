#  -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
from mptt.models import MPTTModel
import datetime
import re
from django.dispatch import receiver
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse

import lib
import product
import depot
import lib
from shipping.models import Package

class ChannelGroup(models.Model):
    name = models.CharField(max_length=255, verbose_name=u"渠道分组名称")
    note = models.TextField(blank=True, default="", verbose_name=u"备注")
    manager = models.ForeignKey(User, null=True, verbose_name=u"负责人")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

   #class Meta:
   #    unique_together = ('attribute', 'label',)

    class Meta:
        verbose_name = u'渠道分组'
        verbose_name_plural = u'渠道分组'

    def __unicode__(self):
        return self.name

class Channel(models.Model):

    TYPE = (
        (0, u'Choies'),
        (1, u'Amazon'),
        (2, u'Smt'),
        (3, u'Wish'),
        (4, u'Shopify'),
        (5, u'Cdiscount'),
        (6, u'Priceminister'),
        (7, u'Ebay'),
        (8, u'tmp1'),
        (9, u'tmp2'),
        (10, u'tmp3'),
    )

    name = models.CharField(max_length=255, verbose_name=u"销售渠道账号")
    note = models.TextField(blank=True, verbose_name=u"备注")
    manager = models.ForeignKey(User, null=True, verbose_name=u"负责人")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"渠道类型")
    # 暂时使用渠道类型即可, channel_group暂时用不到, 所以设置null=True
    channel_group = models.ForeignKey(ChannelGroup, blank=True, null=True, verbose_name=u"渠道组别")
    depots = models.ManyToManyField(depot.models.Depot, through='order.ChannelDepot')
    is_fba = models.BooleanField(default=False, verbose_name="FBA发货")
    # fba_default_loaction = models.CharField(max_length=100, default='', blank=True, verbose_name=u'FBA默认库位')
    default_depot = models.ForeignKey(depot.models.Depot,null=True, verbose_name=u"默认入库仓库", related_name="default_depot")
    main_depot = models.ForeignKey(depot.models.Depot,null=True, verbose_name=u"主仓库", related_name="main_depot", help_text=u"预测囤货等入库仓库")

    # 秘钥相关, 重命名在from中进行
    arg1 = models.CharField(max_length=100, default='', blank=True, verbose_name=u'arg1')
    arg2 = models.CharField(max_length=100, default='', blank=True, verbose_name=u'arg2')
    arg3 = models.CharField(max_length=100, default='', blank=True, verbose_name=u'arg3')
    arg4 = models.CharField(max_length=100, default='', blank=True, verbose_name=u'arg4')
    arg5 = models.CharField(max_length=100, default='', blank=True, verbose_name=u'arg5')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'渠道'
        verbose_name_plural = u'渠道'

    def __unicode__(self):
        return self.name

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class ChannelDepot(models.Model):
    channel = models.ForeignKey(Channel, verbose_name=u"渠道")
    depot = models.ForeignKey(depot.models.Depot, verbose_name=u"仓库")
    order = models.PositiveIntegerField(default=1, verbose_name=u"渠道发货仓库优先级")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'渠道发货仓库'
        verbose_name_plural = u'渠道发货仓库'
        unique_together = ('channel', 'order',)

    def __unicode__(self):
        return str(self.id)


class Order(models.Model):

    ORDER_STATUS = (
        (0, u'未处理'),
        (1, u'开始处理'),
        (2, u'数据错误'),
        (3, u'验证通过/准备发货'),
        (4, u'开始发货'),
        (5, u'发货完成'),
        (6, u'订单完成'),
        (7, u'取消'),
        (8, u'报等/报缺/不可销售'),
    )

    SHIPPING_TYPE = (
        (0, u'小包'),
        (1, u'快递'),
    )

    IMPORT_TYPE = (
        (0, u'手工导单'),
        (1, u'API自动导单'),
    )

    channel = models.ForeignKey(Channel, verbose_name=u"渠道账号")
    ordernum = models.CharField(max_length=30, unique=True, verbose_name=u"订单号")

    status = models.IntegerField(choices=ORDER_STATUS, default=0, verbose_name=u"订单状态")
    priority = models.IntegerField(default=0, verbose_name=u"优先级")

    import_note = models.TextField(default='', blank=True, verbose_name=u'导单备注') # add 记录订单校验的错误信息

    add_user = models.ForeignKey(User, blank=True, null=True, verbose_name=u"添加人员")
    manager = models.ForeignKey(User, blank=True, null=True, related_name="order_manager")
    
    channel_ordernum = models.CharField(max_length=100, default='', blank=True, verbose_name=u'渠道订单号') # add 有的渠道对订单号有别名
    email = models.EmailField(default='', blank=True, verbose_name=u"订单邮箱")
    comment = models.TextField(default='', blank=True, verbose_name=u"订单留言")
    note = models.TextField(default='', blank=True, verbose_name=u"备注")
    create_time = models.DateTimeField(blank=True, null=True, verbose_name=u'真实创建时间')
    latest_ship_date = models.DateTimeField(blank=True, null=True, verbose_name=u'最迟发货时间')
    import_type = models.IntegerField(choices=IMPORT_TYPE, default=0, verbose_name=u'导入方式')
    
    currency = models.CharField(max_length=3, default='USD', blank=True, verbose_name=u"币种")
    rate = models.FloatField(default=1.0, verbose_name=u'汇率') # add
    amount = models.FloatField(default=0.0, verbose_name=u"销售金额")
    amount_shipping = models.FloatField(default=0.0, blank=True, verbose_name=u'运费金额') # add
    shipping_type = models.IntegerField(choices=SHIPPING_TYPE, default=0, verbose_name=u'物流类型')
    payment = models.CharField(max_length=20, default='', blank=True, verbose_name=u'付款方式')
    
    shipping_firstname = models.CharField(max_length=100, default='', blank=True, verbose_name=u"收货人姓")
    shipping_lastname = models.CharField(max_length=100, default='', blank=True, verbose_name=u"收货人名")
    shipping_address = models.CharField(max_length=500, default='', blank=True, verbose_name=u"收货地址1")
    shipping_address1 = models.CharField(max_length=500, default='', blank=True, verbose_name=u"收货地址2")
    shipping_city = models.CharField(max_length=250, default='', blank=True, verbose_name=u"收货城市")
    shipping_state = models.CharField(max_length=250, default='', blank=True, verbose_name=u"收货地址州")
    shipping_country = models.ForeignKey(lib.models.Country, blank=True, null=True, verbose_name=u"收货国家")
    shipping_country_code = models.CharField(max_length=2, default='XX', blank=True, verbose_name=u"国家编码")
    shipping_zipcode = models.CharField(max_length=100, default='', blank=True, verbose_name=u"收货邮编∫")
    shipping_phone = models.CharField(max_length=100, default='', blank=True, verbose_name=u"收货人电话")

    is_fba = models.BooleanField(default=False, blank=True, verbose_name=u"FBA单")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否删除")

    # to determin
    # id_address

    _original_status = None

    class Meta:
        verbose_name = u'订单'
        verbose_name_plural = u'订单'

    def __init__(self, *args, **kwargs):
        super(Order, self).__init__(*args, **kwargs)
        self._original_status = self.status

    @models.permalink
    def get_absolute_url(self):
        return ('order', (), {'ordernum':self.ordernum, })

    def cannot_tongguan(self):
        """如果msg为空, 说明可以通关"""
        msg = u''
        if self.amount - self.amount_shipping <= 0:
            msg += u'不可以: amount <= amount_shipping'
        if self.amount <= 0.1:
            msg += u'不可以:amount <= 0.1'

        # todo 红人单不通关
        # todo luckybag 不通关
        # todo hscode为6404190000的产品，设置其不通关

        return msg

    def save(self, *args, **kw):
        super(Order, self).save(*args, **kw)
        pass

    def update_package_address(self):
        packages = Package.objects.filter(order_id=self.id)
        for package in packages:
            package.email = self.email
            package.shipping_firstname = self.shipping_firstname
            package.shipping_lastname = self.shipping_lastname
            package.shipping_address = self.shipping_address
            package.shipping_address1 =self.shipping_address1
            package.shipping_city = self.shipping_city
            package.shipping_state = self.shipping_state
            package.shipping_country = self.shipping_country
            package.shipping_zipcode = self.shipping_zipcode
            package.shipping_phone = self.shipping_phone
            package.save()

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def __unicode__(self):
        return str(self.id)

class OrderItem(models.Model):
    order = models.ForeignKey(Order, verbose_name=u"订单号", related_name='items')
    item = models.ForeignKey(product.models.Item, blank=True, null=True, verbose_name=u"订单物品")
    #depot = models.ForeignKey(depot.models.Depot, verbose_name=u"仓库", null=True, blank=True)
    qty = models.PositiveIntegerField(default=1, verbose_name=u"购买数量")
    sku = models.CharField(max_length=200, default="", blank=True)
    note = models.TextField(default="", blank=True, verbose_name=u"备注")

    price = models.FloatField(default=0, blank=True, verbose_name=u'销售价格') # add
    channel_oi_id = models.CharField(max_length=50, default='', blank=True, verbose_name=u'渠道中order_item的id') # add

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'订单货品'
        verbose_name_plural = u'订单货品'

    # @property
    # def symbol(self):
    #     return get_symbol(self.currency)

    def __unicode__(self):
        return str(self.id)

class ProductSale(models.Model):

    STATUS = (
        (0, u'准备上架'),
        (1, u'正在上架'),
        (2, u'上架成功'),
        (3, u'上架失败'),
        (4, u'暂不上架'),
        (5, u'待更新'),
        (6, u'已下架'),
    )

    product = models.ForeignKey(product.models.Product, verbose_name=u"产品名称")
    # 不保存对应的user, 使用channel中的manager即可, 后面如果需要再添加
    channel = models.ForeignKey(Channel, null=True,  verbose_name=u"渠道")

    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u'上架状态')
    note = models.TextField(default='', blank=True, verbose_name='备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    def __unicode__(self):
        return "{0}-{1}".format(self.product.sku, self.channel.name)

    # todo
    # 1. 一个channel中一个产品只能出现一次的管控--get_or_create, 是否要使用together_unique
    # 2. 

    class Meta:
        verbose_name = u'渠道销售产品'
        verbose_name_plural = u'渠道销售产品'

        unique_together = ('product', 'channel')

    def save(self, *args, **kwargs):
        super(ProductSale, self).save(*args, **kwargs)
        if self.status==0:#产品绑定渠道时，产品状态修改成资料完善
            p = product.models.Product.objects.get(pk=self.product_id)
            p.status=2
            p.save()

class Alias(models.Model):
    item = models.ForeignKey(product.models.Item, related_name="order_product_alias", verbose_name=u"货品")
    sku = models.CharField(max_length=100, unique=True, verbose_name=u"渠道sku销售别名")
    channel = models.ForeignKey(Channel, null=True, verbose_name=u"渠道名称")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    def __unicode__(self):
        return self.sku

    class Meta:
        verbose_name = u'渠道产品销售别名'
        verbose_name_plural = u'渠道产品销售别名'
