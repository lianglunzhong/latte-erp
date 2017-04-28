# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from mptt.models import MPTTModel
import datetime
from django.db.models.signals import pre_save, post_save, m2m_changed
from django.contrib.auth.models import User
from django.conf import settings
import uuid
import hashlib
import os
from django.core.files import File
import urllib
import itertools
from django.core.urlresolvers import reverse

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
import slugify
import supply

class Attribute(models.Model):
    name = models.CharField(max_length=100, verbose_name=u"属性名称")
    note = models.TextField(blank=True, verbose_name=u"备注")
    #is_variant = models.BooleanField(default=False, help_text=u"变形产品属性", verbose_name=u"是否是变形产品属性")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    # 新增字段
    #sort = models.PositiveIntegerField(default=1, verbose_name=u"属性排序" ,help_text=u"颜色属性的sort值必须比其它属性sort值大！！")

    class Meta:
        verbose_name = u'产品属性'
        verbose_name_plural = u'产品属性'
        #ordering = ['sort']

    def __unicode__(self):
        return self.name

class Option(models.Model):
    attribute = models.ForeignKey(Attribute, verbose_name=u"属性名称")
    code = models.CharField(max_length=1, help_text=u"0-Z")
    name = models.CharField(max_length=100, verbose_name=u"属性选项名称")
    note = models.CharField(max_length=100, blank=True, null=True, verbose_name=u"备注")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'属性选项'
        verbose_name_plural = u'属性选项'
        unique_together = ('attribute', 'code',)

    def __unicode__(self):
        if self.note:
            return "%s (%s)" % (self.name, self.note)
        else:
            return "%s" % self.name

class Category(MPTTModel):
    name = models.CharField(max_length=100, verbose_name=u"分类名称")
    cn_name = models.CharField(max_length=100, verbose_name=u"中文名称", default="")
    code = models.CharField(max_length=2, help_text=u"00-ZZ")
    parent = models.ForeignKey("self", blank=True, null=True, related_name="children", verbose_name=u"父级分类")
    brief = models.TextField(blank=True, verbose_name=u"分类简介")
    status = models.BooleanField(default=True)

    color = models.ForeignKey(Attribute, verbose_name=u"颜色", blank=True, null=True, related_name="category_color")
    size = models.ForeignKey(Attribute, verbose_name=u"尺码", blank=True, null=True, related_name="category_size")

    attributes = models.ManyToManyField(Attribute, blank=True, verbose_name=u"分类属性", related_name="category_attributes")
    manager = models.ForeignKey(User, null=True, verbose_name=u"负责人")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'产品分类'
        verbose_name_plural = u'产品分类'

    def __unicode__(self):
        #return self.name
        return "%s %s" % (self.name, self.cn_name)

    @property
    def link(self):
        return slugify(self.name)

    @models.permalink
    def get_absolute_url(self):
        return ('category', (), {'id':self.id, "link":self.link,})

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

class ProductAttribute(models.Model):
    product = models.ForeignKey("Product")
    attribute = models.ForeignKey(Attribute)
    options = models.ManyToManyField(Option, blank=True)

    def __unicode__(self):
        return  self.attribute.name

    class Meta:
        verbose_name = u'产品属性'
        verbose_name_plural = u'产品属性'

class Product(models.Model):

    STATUS = (
            (0, u'未审核'),
            (1, u'已审核'),
            (2, u'选中'),
            (3, u'可销售'),
            (4, u'不可销售/停止销售'),
        )

    SHIP_TYPE = (
            (0, u'正常'),
            (1, u'液体'),
            (2, u'电池'),
            (3, u'粉末'),
            (4, u'其它'),
        )

    edit_status = models.BooleanField(default=False, verbose_name=u"是否已编辑完成")
    sku = models.CharField(max_length=200,verbose_name="model",)
    category = models.ForeignKey(Category, verbose_name=u"分类", help_text=u"更改产品分类后，请立即保存")
    name = models.CharField(max_length=300, verbose_name=u"名称", blank=True, default="")
    cn_name = models.CharField(max_length=300, verbose_name=u"中文名称", blank=True, default="")
    cost = models.FloatField(default=0.0, verbose_name=u"参考成本 RMB")
    price = models.FloatField(default=0.0, verbose_name=u"参考销售价格 USD")

    color = models.ForeignKey(ProductAttribute, verbose_name=u"颜色", blank=True, null=True, related_name="productattribute_color")
    size = models.ForeignKey(ProductAttribute, verbose_name=u"尺码", blank=True, null=True, related_name="productattribute_size")


    status = models.IntegerField(choices=STATUS, default=1, verbose_name=u"状态")
    ship_type = models.IntegerField(choices=SHIP_TYPE, default=0, verbose_name=u"物流规则")
    material = models.CharField(max_length=300, blank=True, default="", verbose_name=u"材质")
    brief = models.TextField(blank=True,  default="", verbose_name=u"其它说明")
    description = models.TextField(blank=True, null=True, default='', verbose_name=u"描述信息")
    note = models.TextField(blank=True, default='', verbose_name=u"备注")
    #washing_mark = models.TextField(blank=True, default='', verbose_name=u"水洗标")
    weight = models.FloatField(default=0.0, help_text=u"基本单位为KG 千克", verbose_name=u"产品重量")

    options = models.ManyToManyField(Option, blank=True, verbose_name=u"产品属性")

    manager = models.ForeignKey(User, blank=True, null=True, verbose_name=u"负责人")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    #新增字段
    #updater = models.ForeignKey(User, related_name='product_updater',blank=True, null=True, verbose_name=u"修改人员")
    manager = models.ForeignKey(User, blank=True, null=True, verbose_name=u"负责人")
    adder = models.ForeignKey(User, related_name='product_adder', null=True, verbose_name=u"添加人员")
    #adder = models.ForeignKey(User, related_name='product_adder', null=True, verbose_name=u"录入人员")
    choies_site_url = models.CharField(max_length=250, blank=True, verbose_name=u"产品choies访问网址")
    choies_sku = models.CharField(max_length=200,blank=True,  default="",verbose_name="choies的model",)
    choies_supplier_name = models.CharField(max_length=250, blank=True,default="", verbose_name=u"choies的供应商名称")

    _category_id = None

    class Meta:
        verbose_name = u'产品'
        verbose_name_plural = u'产品'

    def __init__(self, *args, **kwargs):
        super(Product, self).__init__(*args, **kwargs)
        if self.category_id:
            self._category_id = self.category_id

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def update_items(self):
        _options_ids = []


        if self.color:
            color_option_ids = self.color.options.order_by('id').values_list('id', flat=True)
            if color_option_ids:
                _options_ids.append(color_option_ids)
            else:
                color_option_ids = [0,]
            print 'color:'
            print color_option_ids
                
        if self.size:
            size_option_ids = self.size.options.order_by('id').values_list('id', flat=True)
            if size_option_ids:
                _options_ids.append(size_option_ids)
            else:
                size_option_ids = [0,]
            print 'size:'
            print size_option_ids

        print _options_ids

        keys=[]
        
        for color_id in color_option_ids:
            for size_id in size_option_ids:
                keys.append("%s-%s-%s" % (self.id, color_id, size_id))

       #for x in itertools.product(*_options_ids):
       #    keys.append(str(self.id) + '-' + '-'.join([str(i) for i in x ]))

        Item.objects.filter(product_id=self.id).update(deleted=True)
        print keys

        if not keys:
            keys = [ "%s-" % self.id]

        for key in keys:
            item, is_created = Item.objects.get_or_create(product_id=self.id, key=key)

            color_code = "0"
            size_code = "0"
            try:
                color_option_id = key.split('-')[1]
                
                print key
                print color_option_id
                if color_option_id and color_option_id != '0':
                    color_code = Option.objects.get(id=long(color_option_id)).code.upper()
            except IndexError:
                pass

            try:
                size_option_id = key.split('-')[2]
                if size_option_id and size_option_id != '0':
                    size_code = Option.objects.get(id=long(size_option_id)).code.upper()
            except IndexError:
                pass

            item.sku = self.sku + color_code + size_code

            if item.cost == 0:
                item.cost = self.cost
            if item.weight == 0:
                item.weight = self.weight

            item.deleted = False
            item.save()

    def __unicode__(self):
        return self.sku + '|' + self.name

    def get_images(self):
        #images = self.productimage_set.order_by('order').all()
        images = self.productimage_set.order_by('id').all()
        return images

    def get_image_thumb(self):
        images = self.productimage_set.order_by('id').filter(deleted=False).first()
        if images:
            image_url = str(images.image)
            image_url_array = image_url.split('/')
            url = 'http://erp.wxzeshang.com:8000/'+image_url_array[0]+'/100/'+image_url_array[2]
        else:
            url = "/static/admin/img/100x100.png"

        return u'<img src="%s" />' % (url)

    def get_image(self, size=100):
        images = self.productimage_set.order_by('id').filter(deleted=False).first()
        if images:
            image_url = str(images.image)
            image_url_array = image_url.split('/')
            url = u"http://erp.wxzeshang.com:8000/%s/%s/%s" % (image_url_array[0], size, image_url_array[2])
        else:
            url = "/static/admin/img/100x100.png"

        return url

    def get_default_supply_product(self):
        sp = supply.models.SupplierProduct.objects.filter(deleted=False,product_id=self.id).order_by('order').first()
        return sp

    def get_model(self):
        alphabet, base36 = ['0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ', '']
        number = self.id
        while number:
            number, i = divmod(number, 36)
            base36 = alphabet[i] + base36
        _sku = base36 or alphabet[0]

        return "%s%s" % (self.category.code, _sku.rjust(6, '0'))

   #def update_attributes(self):
   #    color_attribute = self.category.color
   #    size_attribute = self.category.size

   #    if color_attribute:
   #        color_product_attribute, is_created = ProductAttribute.objects.get_or_create(product=self, attribute=color_attribute)
   #        self.color = color_product_attribute
   #    else:
   #        self.color = None

   #    if size_attribute:
   #        size_product_attribute, is_created = ProductAttribute.objects.get_or_create(product=self, attribute=size_attribute)
   #        self.size = size_product_attribute
   #    else:
   #        self.size = None
   #    self.save()

    def save(self, *args, **kwargs):
        super(Product, self).save(*args, **kwargs)
        if not self.sku:
            self.sku = self.get_model()

        color_attribute = self.category.color
        size_attribute = self.category.size

        if color_attribute:
            color_product_attribute, is_created = ProductAttribute.objects.get_or_create(product=self, attribute=color_attribute)
            self.color = color_product_attribute
        else:
            self.color = None

        if size_attribute:
            size_product_attribute, is_created = ProductAttribute.objects.get_or_create(product=self, attribute=size_attribute)
            self.size = size_product_attribute
        else:
            self.size = None
        super(Product, self).save(*args, **kwargs)

    """产品列表的查询"""
    def product_list(self,search):
        if not search:
            return Product.objects.filter(deleted=0).order_by('id')
        else:
            return Product.objects.filter(deleted=0,sku__contains=search).order_by('id')

def get_image_upload_path(instance, filename):
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    #name = time.strftime('%y-%m/%d',time.localtime(time.time()))
    name = str(uuid.uuid4())
    return os.path.join('img', name[0:3], name[3:]+ext)

def get_product_image_upload_path(instance, filename):
    #return os.path.join('photos', str(instance.id), filename)
    fn, ext = os.path.splitext(filename)
    if not ext:
        ext = '.jpg'
    #name = time.strftime('%y-%m/%d',time.localtime(time.time()))
    name = str(uuid.uuid4())
    return os.path.join('pimg', name[0:3], name[3:]+ext)


class ProductImage(models.Model):
    image = models.ImageField(upload_to=get_product_image_upload_path, verbose_name=u"图片地址")
    product = models.ForeignKey(Product, verbose_name=u"产品名称")
    choies_url = models.CharField(max_length=300, verbose_name=u"choies网站链接", default='')
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

   #img_updater = models.ForeignKey(User, related_name='img_updater', verbose_name=u"修改图片人员")
   #img_adder = models.ForeignKey(User, related_name='img_adder', verbose_name=u"新增图片人员")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    class Meta:
        verbose_name = u'产品图片'
        verbose_name_plural = u'产品图片'

    def __unicode__(self):
        return 'Image %s' % self.id

class Item(models.Model):

    STATUS = (
            (1, u'可销售'),
            (2, u'报等/报缺'),
            (0, u'停止销售'),
        )

    product = models.ForeignKey(Product, verbose_name=u"产品名称", related_name='items')
    key = models.CharField(max_length=200, verbose_name=u"产品属性") #记录方式option_id-option_id
    weight = models.FloatField(default=0.0, help_text=u"基本单位为KG 千克", verbose_name=u"产品重量")
    sku = models.CharField(max_length=200, verbose_name=u"sku")
    qty = models.IntegerField(default=0, verbose_name=u"库存数量")#暂时无效
    cost = models.FloatField(default=0, blank=True, null=True, verbose_name=u"参考成本")
    status = models.IntegerField(choices=STATUS, default=1, verbose_name=u"状态")
    estimated_date = models.DateField(blank=True, null=True, verbose_name=u"估计到货时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
        #return reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

    class Meta:
        unique_together = ('key', 'product',)
        verbose_name = u'货品/变形产品'
        verbose_name_plural = u'货品/变形产品'

    def __unicode__(self):
        return self.sku

# class ProductForSale(Product):
#     class Meta:
#         proxy = True
#         verbose_name = u'产品销售'
#         verbose_name_plural = u'产品销售'
#
# class ProductForDevelop(Product):
#     class Meta:
#         proxy = True
#         verbose_name = u'产品开发'
#         verbose_name_plural = u'产品开发'


class ProductRequest(models.Model):

    STATUS = (
            (0, u'未处理'),
            (1, u'开始处理'),
            (2, u'完成'),
            (3, u'废除'),
        )

    name = models.CharField(max_length=200, verbose_name=u"标题")
    note = models.TextField(blank=True, verbose_name=u"详细备注")
    manager = models.ForeignKey(User, null=True,  verbose_name=u"负责人", related_name="manager")
    add_user = models.ForeignKey(User, null=True,  verbose_name=u"发起人", related_name="add_user")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u"状态")
    products = models.ManyToManyField(Product, blank=True, verbose_name=u"产品")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")
    # 新增字段
    active_time = models.DateTimeField(verbose_name=u"有效时间")
    related_sku_note = models.TextField(blank=True, verbose_name=u"关联产品的备注", help_text='批量管理产品，用英文,分割，捆绑成功的产品将从此字段中消失，否则是未成功的')

    class Meta:
        verbose_name = u'组货方案'
        verbose_name_plural = u'组货方案'

    def __unicode__(self):
        return u'%s-%s' % (self.id,self.name)

# 组货方案绑定产品
    def related_product(self):
        products = self.related_sku_note.split(',')
        # print products
        str = ''
        for pro in products:
            pro = pro.strip()
            try:
                product = Product.objects.get(sku=pro)
                self.products.add(product)
            except:
                str = str + pro + ',\n'
        return str


class ProductRequestImage(models.Model):
    image = models.ImageField(upload_to=get_product_image_upload_path, verbose_name=u"图片地址")
    product_request = models.ForeignKey(ProductRequest)

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'组货方案图片'
        verbose_name_plural = u'组货方案图片'



class ProductAction(models.Model):

    TYPE = (
        (0,u'资料编辑'),
        (1,u'拍照'),
        (2,u'图片编辑'),
    )
    STATUS = (
            (0, u'未处理'),
            (1, u'开始处理'),
            (2, u'完成'),
            (3, u'废除'),
        )

    product = models.ForeignKey(Product, verbose_name=u"产品名称")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"任务名称")
    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u"进度")
    note = models.TextField(default="", verbose_name=u"备注", blank=True)

    manager = models.ForeignKey(User, null=True,  verbose_name=u"负责人", related_name="productaction_manager")
    add_user = models.ForeignKey(User, null=True,  verbose_name=u"发起人", related_name="productaction_add_user")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'产品任务'
        verbose_name_plural = u'产品任务'

class ProductFeedback(models.Model):

    TYPE = (
        (0,u'尺码问题'),
        (1,u'材质问题'),
        (2,u'价格问题'),
    )

    product = models.ForeignKey(Product, verbose_name=u"产品名称")
    type = models.IntegerField(choices=TYPE, default=0, verbose_name=u"任务名称")
    note = models.TextField(default="", verbose_name=u"备注")

    add_user = models.ForeignKey(User, null=True,  verbose_name=u"发起人", related_name="productfeedback_add_user")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'产品反馈'
        verbose_name_plural = u'产品反馈'
