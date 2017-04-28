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

#from order.models import Order
#import order


class RightsSupport(models.Model):

    class Meta:

        managed = False  # No database table creation or deletion operations \
                         # will be performed for this model.

        permissions = (
            #product
            ('import_buyer_product', 'import buyer product 批量导入产品'),
            ('import_update_product', 'import update product 批量更新已有产品'),
            #supply
            ('purchaseorderitem_check', 'purchaseorderitem check 采购对单'),
            ('purchaseorderitem_error_notice', 'purchaseorderitem error notice 采购异常'),
            ('itemin_single','single itemin 单件扫描入库'),
            ('itemin','multiple itemin 多件扫描入库'),

            ('auto_create_purchaseorder','auto create purchaseorder 一键生成采购单'),
            #depot
            ('import_depotitem_location','import depotitem location 南京仓批量更新货品库位'),
            ('import_depotinlog','import depotinlog 南京仓手动杂入'),
            ('import_depotoutlog','import depotoutlog 南京手动杂出'),
            ('bulk_print_barcode','depot bulk print barcode 仓库批量打印条码'),
            ('export_depotitem_cost_inventory','export depotitem cost inventory 仓库批量导出成本库存'),
            #order
            ('import_channel_sku','import channel sku 渠道别名sku导入'),
            #pick
            ('pick_index','pick index 分拣系统-默认页面'),
            ('pick_assign_shipping','pick assign shipping 分拣系统-分配物流方式'),
            ('pick_get_tracking_no','pick_get_tracking_no 物流商下单'),
            ('pick_create','pick create 生成拣货单'),
            ('pick_list_all','pick list all 打印拣货单'),
            ('pick_sort','pick sort 单品单件包装'),
            # ('pick_sort','pick sort 单品多件包装'),
            # ('pick_sort','pick sort 多品多件分拣'),
            ('pick_packaging','pick packaging 多品多件包装'),
            #3bao
            ('product_3bao','product 3bao 通关报关-3宝产品'),

        )

class Country(models.Model):
    name = models.CharField(max_length=100, verbose_name=u'国家名称')
    cn_name = models.CharField(max_length=100, default="", blank=True, verbose_name=u'国家中文名称')
    code = models.CharField(max_length=2, unique=True, verbose_name=u'国家简写编码')
    number = models.IntegerField(default=0, verbose_name=u'国家数字码')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'国家'
        verbose_name_plural = u'国家'

    def __unicode__(self):
        return "%s|%s|%s" % (self.code, self.name, self.cn_name)

class Notify(models.Model):
    title = models.CharField(max_length=250)
    action = models.CharField(max_length=250, blank=True)
    content = models.TextField(default="", blank=True)
    user = models.ForeignKey(User, null=True)
    is_read = models.BooleanField(default=False)
    read_time = models.DateTimeField()

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    def __unicode__(self):
        return self.title

    class Meta:
        verbose_name = u'信息'
        verbose_name_plural = u'信息'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return urlresolvers.reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))
        #return urlresolvers.reverse("admin:%s_%s_change" % (self._meta.app_label, self._meta.module_name), args=(self.id,))

def process_order():
    # 订单 未处理:0, 订单 数据出错:7
    query = order.models.Order.objects.filter(status__in=[1, 7])
    total = query.count()


    print total
    for order in query:
        order
    #orders = Order.objects.filter(status__in=[0, 7])

def do_package():
    print 'do_package'
    # get orders

COUNTRIES = (
    ('00', 'None'),
    ('GB', 'United Kingdom'),
    ('US', 'United States'),
    ('AF', 'Afghanistan'),
    ('AX', u'Åland Islands'),
    ('AL', 'Albania'),
    ('DZ', 'Algeria'),
    ('AS', 'American Samoa'),
    ('AD', 'Andorra'),
    ('AO', 'Angola'),
    ('AI', 'Anguilla'),
    ('AQ', 'Antarctica'),
    ('AG', 'Antigua and Barbuda'),
    ('AR', 'Argentina'),
    ('AM', 'Armenia'),
    ('AW', 'Aruba'),
    ('AU', 'Australia'),
    ('AT', 'Austria'),
    ('AZ', 'Azerbaijan'),
    ('BS', 'Bahamas'),
    ('BH', 'Bahrain'),
    ('BD', 'Bangladesh'),
    ('BB', 'Barbados'),
    ('BY', 'Belarus'),
    ('BE', 'Belgium'),
    ('BZ', 'Belize'),
    ('BJ', 'Benin'),
    ('BM', 'Bermuda'),
    ('BT', 'Bhutan'),
    ('BO', 'Bolivia, Plurinational State of'),
    ('BQ', 'Bonaire, Sint Eustatius and Saba'),
    ('BA', 'Bosnia and Herzegovina'),
    ('BW', 'Botswana'),
    ('BV', 'Bouvet Island'),
    ('BR', 'Brazil'),
    ('IO', 'British Indian Ocean Territory'),
    ('BN', 'Brunei Darussalam'),
    ('BG', 'Bulgaria'),
    ('BF', 'Burkina Faso'),
    ('BI', 'Burundi'),
    ('KH', 'Cambodia'),
    ('CM', 'Cameroon'),
    ('CA', 'Canada'),
    ('CV', 'Cape Verde'),
    ('KY', 'Cayman Islands'),
    ('CF', 'Central African Republic'),
    ('TD', 'Chad'),
    ('CL', 'Chile'),
    ('CN', 'China'),
    ('CX', 'Christmas Island'),
    ('CC', 'Cocos (Keeling) Islands'),
    ('CO', 'Colombia'),
    ('KM', 'Comoros'),
    ('CG', 'Congo'),
    ('CD', 'Congo, The Democratic Republic of the'),
    ('CK', 'Cook Islands'),
    ('CR', 'Costa Rica'),
    ('CI', "Côte d'Ivoire"),
    ('HR', u'Croatia'),
    ('CU', 'Cuba'),
    ('CW', u'Curaçao'),
    ('CY', 'Cyprus'),
    ('CZ', 'Czech Republic'),
    ('DK', 'Denmark'),
    ('DJ', 'Djibouti'),
    ('DM', 'Dominica'),
    ('DO', 'Dominican Republic'),
    ('EC', 'Ecuador'),
    ('EG', 'Egypt'),
    ('SV', 'El Salvador'),
    ('GQ', 'Equatorial Guinea'),
    ('ER', 'Eritrea'),
    ('EE', 'Estonia'),
    ('ET', 'Ethiopia'),
    ('FK', 'Falkland Islands (Malvinas)'),
    ('FO', 'Faroe Islands'),
    ('FJ', 'Fiji'),
    ('FI', 'Finland'),
    ('FR', 'France'),
    ('GF', 'French Guiana'),
    ('PF', 'French Polynesia'),
    ('TF', 'French Southern Territories'),
    ('GA', 'Gabon'),
    ('GM', 'Gambia'),
    ('GE', 'Georgia'),
    ('DE', 'Germany'),
    ('GH', 'Ghana'),
    ('GI', 'Gibraltar'),
    ('GR', 'Greece'),
    ('GL', 'Greenland'),
    ('GD', 'Grenada'),
    ('GP', 'Guadeloupe'),
    ('GU', 'Guam'),
    ('GT', 'Guatemala'),
    ('GG', 'Guernsey'),
    ('GN', 'Guinea'),
    ('GW', 'Guinea-bissau'),
    ('GY', 'Guyana'),
    ('HT', 'Haiti'),
    ('HM', 'Heard Island and McDonald Islands'),
    ('VA', 'Holy See (Vatican City State)'),
    ('HN', 'Honduras'),
    ('HK', 'Hong Kong'),
    ('HU', 'Hungary'),
    ('IS', 'Iceland'),
    ('IN', 'India'),
    ('ID', 'Indonesia'),
    ('IR', 'Iran, Islamic Republic of'),
    ('IQ', 'Iraq'),
    ('IE', 'Ireland'),
    ('IM', 'Isle of Man'),
    ('IL', 'Israel'),
    ('IT', 'Italy'),
    ('JM', 'Jamaica'),
    ('JP', 'Japan'),
    ('JE', 'Jersey'),
    ('JO', 'Jordan'),
    ('KZ', 'Kazakhstan'),
    ('KE', 'Kenya'),
    ('KI', 'Kiribati'),
    ('KP', "Korea, Democratic People's Republic of"),
    ('KR', 'Korea, Republic of'),
    ('KW', 'Kuwait'),
    ('KG', 'Kyrgyzstan'),
    ('LA', "Lao People's Democratic Republic"),
    ('LV', 'Latvia'),
    ('LB', 'Lebanon'),
    ('LS', 'Lesotho'),
    ('LR', 'Liberia'),
    ('LY', 'Libyan Arab Jamahiriya'),
    ('LI', 'Liechtenstein'),
    ('LT', 'Lithuania'),
    ('LU', 'Luxembourg'),
    ('MO', 'Macao'),
    ('MK', 'Macedonia, The Former Yugoslav Republic of'),
    ('MG', 'Madagascar'),
    ('MW', 'Malawi'),
    ('MY', 'Malaysia'),
    ('MV', 'Maldives'),
    ('ML', 'Mali'),
    ('MT', 'Malta'),
    ('MH', 'Marshall Islands'),
    ('MQ', 'Martinique'),
    ('MR', 'Mauritania'),
    ('MU', 'Mauritius'),
    ('YT', 'Mayotte'),
    ('MX', 'Mexico'),
    ('FM', 'Micronesia, Federated States of'),
    ('MD', 'Moldova, Republic of'),
    ('MC', 'Monaco'),
    ('MN', 'Mongolia'),
    ('ME', 'Montenegro'),
    ('MS', 'Montserrat'),
    ('MA', 'Morocco'),
    ('MZ', 'Mozambique'),
    ('MM', 'Myanmar'),
    ('NA', 'Namibia'),
    ('NR', 'Nauru'),
    ('NP', 'Nepal'),
    ('NL', 'Netherlands'),
    ('NC', 'New Caledonia'),
    ('NZ', 'New Zealand'),
    ('NI', 'Nicaragua'),
    ('NE', 'Niger'),
    ('NG', 'Nigeria'),
    ('NU', 'Niue'),
    ('NF', 'Norfolk Island'),
    ('MP', 'Northern Mariana Islands'),
    ('NO', 'Norway'),
    ('OM', 'Oman'),
    ('PK', 'Pakistan'),
    ('PW', 'Palau'),
    ('PS', 'Palestinian Territory, Occupied'),
    ('PA', 'Panama'),
    ('PG', 'Papua New Guinea'),
    ('PY', 'Paraguay'),
    ('PE', 'Peru'),
    ('PH', 'Philippines'),
    ('PN', 'Pitcairn'),
    ('PL', 'Poland'),
    ('PT', 'Portugal'),
    ('PR', 'Puerto Rico'),
    ('QA', 'Qatar'),
    ('RE', 'Réunion'),
    ('RO', 'Romania'),
    ('RU', 'Russian Federation'),
    ('RW', 'Rwanda'),
    ('BL', 'Saint Barthélemy'),
    ('SH', 'Saint Helena, Ascension and Tristan Da Cunha'),
    ('KN', 'Saint Kitts and Nevis'),
    ('LC', 'Saint Lucia'),
    ('MF', 'Saint Martin (French Part)'),
    ('PM', 'Saint Pierre and Miquelon'),
    ('VC', 'Saint Vincent and the Grenadines'),
    ('WS', 'Samoa'),
    ('SM', 'San Marino'),
    ('ST', 'Sao Tome and Principe'),
    ('SA', 'Saudi Arabia'),
    ('SN', 'Senegal'),
    ('RS', 'Serbia'),
    ('SC', 'Seychelles'),
    ('SL', 'Sierra Leone'),
    ('SG', 'Singapore'),
    ('SX', 'Sint Maarten (Dutch Part)'),
    ('SK', 'Slovakia'),
    ('SI', 'Slovenia'),
    ('SB', 'Solomon Islands'),
    ('SO', 'Somalia'),
    ('ZA', 'South Africa'),
    ('GS', 'South Georgia and the South Sandwich Islands'),
    ('SS', 'South Sudan'),
    ('ES', 'Spain'),
    ('LK', 'Sri Lanka'),
    ('SD', 'Sudan'),
    ('SR', 'Suriname'),
    ('SJ', 'Svalbard and Jan Mayen'),
    ('SZ', 'Swaziland'),
    ('SE', 'Sweden'),
    ('CH', 'Switzerland'),
    ('SY', 'Syrian Arab Republic'),
    ('TW', 'Taiwan'),
    ('TJ', 'Tajikistan'),
    ('TZ', 'Tanzania, United Republic of'),
    ('TH', 'Thailand'),
    ('TL', 'Timor-leste'),
    ('TG', 'Togo'),
    ('TK', 'Tokelau'),
    ('TO', 'Tonga'),
    ('TT', 'Trinidad and Tobago'),
    ('TN', 'Tunisia'),
    ('TR', 'Turkey'),
    ('TM', 'Turkmenistan'),
    ('TC', 'Turks and Caicos Islands'),
    ('TV', 'Tuvalu'),
    ('UG', 'Uganda'),
    ('UA', 'Ukraine'),
    ('AE', 'United Arab Emirates'),
    ('UM', 'United States Minor Outlying Islands'),
    ('UY', 'Uruguay'),
    ('UZ', 'Uzbekistan'),
    ('VU', 'Vanuatu'),
    ('VE', 'Venezuela, Bolivarian Republic of'),
    ('VN', 'Viet Nam'),
    ('VG', 'Virgin Islands, British'),
    ('VI', 'Virgin Islands, U.S.'),
    ('WF', 'Wallis and Futuna'),
    ('EH', 'Western Sahara'),
    ('YE', 'Yemen'),
    ('ZM', 'Zambia'),
    ('ZW', 'Zimbabwe'),
    ('KO', 'Kosovo'),
)

class Shipping(models.Model):
    """物流方式

    用户下单的时候提供物流方式的选择
    现在输入的价格是rmb,与产品等其他数据的币种不一样，需要注意


    off:
        价格折扣设置

    price:
        在没有找到ShippingZone, ShippingPrice的时候使用这个价格，目前这个价格的单位是rmb

    link:
        物流追踪信息查询网址
    """

    OFF = (
            (1.0,'100%'),
            (0.9,'90%'),
            (0.8,'80%'),
            (0.7,'70%'),
            (0.6,'60%'),
            (0.5,'50%'),
            (0.45,'45%'),
            (0.4,'40%'),
            )

    name = models.CharField(max_length=100, verbose_name=u'物流名称')
    label = models.CharField(max_length=100, verbose_name=u'物流标签')
    brief = models.TextField(default="", blank=True, verbose_name=u'物流简介')
    link = models.CharField(max_length=300, default="", blank=True, verbose_name=u'物流运单号查询网址')
    sort = models.IntegerField(default=1000, verbose_name=u'排序')
    active = models.BooleanField(default=True, verbose_name=u'是否激活')
    default = models.BooleanField(default=False)
    price = models.FloatField(default=0.0, verbose_name=u'默认运费成本')
    off = models.FloatField(default=1.0, verbose_name=u'价格折扣《=1')
    #off = models.FloatField(default=1.0, choices=OFF)

    shipping_adder = models.ForeignKey(User, default=1, related_name='shipping_adder', verbose_name=u"新增操作人")
    shipping_updater = models.ForeignKey(User, default=1, related_name='shipping_updater', verbose_name=u"修改操作人")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'物流方式'
        verbose_name_plural = u'物流方式'

    def __unicode__(self):
        return self.label

    def get_price(self, country="US", weight=0.0):
        weight = float(weight)
        if weight == 0.0 :
            return 0.0

        try:
            country = Country.objects.filter(code=country)
            shipping_zone = ShippingZone.objects.filter(shipping=self).filter(countries__in=country).get()
            shipping_price = ShippingPrice.objects.filter(shipping_zone=shipping_zone).filter(weight__lte=weight).order_by('-weight')[0]
            price = shipping_price.price + float(weight-shipping_price.weight) * float(shipping_price.offset_price) + self.price
        except:
            price = 0

        #price = price * self.off
        return price

class ShippingZone(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name=u'物流发货地区')
    shipping = models.ForeignKey(Shipping, verbose_name=u'物流名称')
    countries = models.ManyToManyField(Country, blank=True, verbose_name=u'国家')

    class Meta:
        verbose_name = u'物流地区'
        verbose_name_plural = u'物流地区'

    def __unicode__(self):
        return self.name

class ShippingPrice(models.Model):
    weight = models.FloatField(default=0.0, verbose_name=u'物流发货重量')
    price = models.FloatField(default=0.0, verbose_name=u'运费')
    offset_price = models.FloatField(default=0.0, verbose_name=u'运费折扣')
    shipping_zone = models.ForeignKey(ShippingZone, verbose_name=u'物流发货地区')

    shipping_price_adder = models.ForeignKey(User, default=1, related_name='shipping_price_adder', verbose_name=u"新增操作人")
    shipping_price_updater = models.ForeignKey(User, default=1, related_name='shipping_price_updater', verbose_name=u"修改操作人")
    created = models.DateTimeField(auto_now_add=True,  verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True,  verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'物流价格'
        verbose_name_plural = u'物流价格'
        unique_together = ('weight', 'shipping_zone',)

    def __unicode__(self):
        return str(self.id)

class ShippingCost(models.Model):
    MAP_STATUS = (
        (0, '尚未匹配'),
        (1, '成功'),
        (2, '失败'),
        (3, '无需匹配'),
    )
    CHECK_STATUS = (
        (0, '尚未核对'),
        (1, '通过'),
        (2, '未通过'),
        (3, '手工通过'),
    )
    tracking_no = models.CharField(u'运单号', max_length=50, db_index=True)
    invoice_no = models.CharField(u'发票号码', max_length=100)

    map_status = models.IntegerField(u'匹配状态', default=0, choices=MAP_STATUS)
    check_status = models.IntegerField(u'核对状态', default=0, choices=CHECK_STATUS)

    cost = models.FloatField(u'运费', default=0)
    weight = models.FloatField(u'重量', default=0)
    logistics_name = models.CharField(u'物流商名称', max_length=100, default='', blank=True)
    payment_company = models.CharField(u'付款公司', max_length=100, default='', blank=True)

    shipping_cost_adder = models.ForeignKey(User, default=1, related_name='shipping_cost_adder', verbose_name=u"新增操作人")
    shipping_cost_updater = models.ForeignKey(User, default=1, related_name='shipping_cost_updater', verbose_name=u"修改操作人")
    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'物流成本'
        verbose_name_plural = u'物流成本'

    def __unicode__(self):
        return "%s:%s" % (self.id, self.tracking_no)

class ScriptLog(models.Model):

    RUNNING_STATUS = (
        (0, u'失败'),
        (1, u'成功'),
        (2, u'正在运行'),
    )

    process = models.CharField(u'进程名称', max_length=200, default="", blank=True)
    running_status = models.IntegerField(u'运行状态', default=0, choices=RUNNING_STATUS)
    date_from = models.DateTimeField(u"进程开始时间", blank=True, null=True)
    date_to = models.DateTimeField(u"进程开始时间", blank=True, null=True)
    run_time = models.FloatField(u"运行时间", default=0)
    content = models.TextField(u"运行内容", default="")
    note = models.TextField(u"运行备注", default='')
