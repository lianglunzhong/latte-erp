# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.db import models
import datetime
from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.core.urlresolvers import reverse
from django.db.models import Sum

import lib
import order
import product
import depot
import supply

class Package(models.Model):

    STATUS = (
        (0, u'未处理'),
        (1, u'开始处理'),#手动审核
        (2, u'配货中'),#开始pick，全部用库存
        (3, u'打包中'),
        (5, u'已发货'),
        (6, u'妥投'),
        (7, u'到达待取'),
        (4, u'取消'),
    )

    PICK_STATUS = (
        (0, u'未分拣'),
        (1, u'分拣中'),
        (2, u'分拣完成'),
        (3, u'包装完成'),
        (4, u'分拣异常'),
        (5, u'包装异常'),
    )

    order = models.ForeignKey('order.Order', verbose_name=u'订单')#与订单表中import 冲突
    status = models.IntegerField(choices=STATUS, default=0, verbose_name=u'包裹发货状态')
    shipping = models.ForeignKey(lib.models.Shipping, null=True, blank=True, verbose_name=u'物流方式')
    note = models.TextField(default='', blank=True, null=True, verbose_name=u'备注')

    tracking_no = models.CharField(max_length=250, default="", blank=True, db_index=True, verbose_name=u'运单号')
    ship_time = models.DateTimeField(blank=True, null=True, verbose_name=u'执行发货时间')
    shipper = models.ForeignKey(User, null=True, blank=True, related_name="package_shipper", verbose_name=u'执行发货人') #执行发货人
    print_time = models.DateTimeField(blank=True, null=True, verbose_name=u'包裹打印时间')
    printer = models.ForeignKey(User, null=True, blank=True, related_name="package_printer", verbose_name=u'打印包裹/面单人') #打印面单人

    email = models.EmailField(default='', verbose_name=u'收件人邮箱')
    shipping_firstname = models.CharField(u'收件人姓', max_length=100, default='', blank=True, null=True)
    shipping_lastname = models.CharField(u'收件人名', max_length=100, default='', blank=True, null=True)
    shipping_address = models.CharField(u'收件人地址', max_length=500, default='', blank=True, null=True)
    shipping_address1 = models.CharField(u'收件人地址1', max_length=500, default='', blank=True, null=True)
    shipping_city = models.CharField(u'收件人城市', max_length=250, default='', blank=True, null=True)
    shipping_state = models.CharField(u'收件人州', max_length=250, default='', blank=True, null=True)

    shipping_country = models.ForeignKey(lib.models.Country, null=True, blank=True)
    shipping_zipcode = models.CharField(u'收件人邮编', max_length=100, default='', blank=True, null=True)
    shipping_phone = models.CharField(u'收件人电话', max_length=100, default='', blank=True, null=True)

    qty = models.IntegerField(default=0, blank=True, verbose_name=u"货品总数")
    sku_qty = models.IntegerField(default=0, blank=True, verbose_name=u"SKU总数")
    weight = models.FloatField(u'包裹重量', default=0.0)
    cost = models.FloatField(default=0, blank=True, null=True, verbose_name=u"成本")
    cost1 = models.FloatField(default=0, blank=True, null=True, verbose_name=u"成本1")

    sf_numbers = models.CharField(u"顺丰单号", max_length=30, default="", blank=True)
    skybill_code = models.CharField(u"顺丰渠道转单号", max_length=30, default="", blank=True)

    pick = models.ForeignKey(depot.models.Pick, null=True, blank=True, verbose_name=u"拣货单")
    pick_type = models.IntegerField(u'拣货单类型', choices=depot.models.Pick.PICK_TYPES, default=0)
    pick_status = models.IntegerField(u'分拣状态', choices=PICK_STATUS, default=0, blank=True)
    code = models.IntegerField(u'是否同一物理仓，一起拣货', choices=depot.models.Depot.CODE, default=0)
    position_score = models.IntegerField(default=0, blank=True, verbose_name=u'库位得分')
    pick_error_info = models.TextField(default='', blank=True, verbose_name=u'拣货单异常信息')

    option_log = models.TextField(default='', blank=True, verbose_name=u'操作记录')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新建时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")

    _status = None

    class Meta:
        verbose_name = u'包裹单'
        verbose_name_plural = u'包裹单'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def __unicode__(self):
        return "PACKAGE#%s" % self.id

    def __init__(self, *args, **kwargs):
        super(Package, self).__init__(*args, **kwargs)
        self._status = self.status
        self._shipping_id = self.shipping_id
        self._tracking_no = self.tracking_no

    def can_pick(self):
        can_pick = False
        packageitems = PackageItem.objects.filter(package=self).filter(deleted=False)
        for packageitem in packageitems:
            can_pick = True
            qty_locked = ItemLocked.objects.filter(package_item=packageitem, deleted=False).aggregate(Sum('qty'))['qty__sum']
            if not qty_locked:
                qty_locked = 0

            if packageitem.qty != qty_locked:
                can_pick = False
                break

        return can_pick

    def get_name(self):
        return self.shipping_firstname + ' ' + self.shipping_lastname

    def get_address(self):
        return self.shipping_address + ' ' + self.shipping_address1

    def get_weight(self):
        weight = 0
        for item_weight, qty in self.packageitem_set.filter(deleted=False).values_list('item__product__weight', 'qty'):
            weight += item_weight * qty
        return weight

    def get_qty(self):
        qty = self.packageitem_set.filter(deleted=False).aggregate(Sum('qty')).get('qty__sum') or 0
        return qty 

    def get_sku_qty(self):
        qty = self.packageitem_set.filter(deleted=False).values('item_id').count() or 0
        return qty 

    def get_pick_type(self):
        """根据package的ItemLocked的数量来判断pick_type"""
        item_count = ItemLocked.objects.filter(package_item__package_id=self.id).filter(deleted=False).count()
        item_qtys = self.packageitem_set.aggregate(Sum('qty')).get('qty__sum') or 0

        if item_count == 1 and item_qtys == 1:
            pick_type = 1
        elif item_count == 1 and item_qtys > 1:
            pick_type = 2
        elif item_count > 1:
            pick_type = 3
        else:
            pick_type = 0
        return pick_type

    def get_position_score(self):
        """获取package的库位得分"""
        positions = ItemLocked.objects.filter(package_item__package_id=self.id)\
                                      .values_list('depot_item__position', flat=True)
        # todo 南京和广州库位排序, 和库位规则可能不同, 需要各自定义
        positions = [i.split(',')[0] for i in positions if i]
        # 每个库位只计算一次, 所以使用set推导式
        if self.code == 1:  # 南京
            SCORE_STR = "ABCDEFGHIJKLMNOPGRSTUVWXYZ"
            diff_str = {i[1] for i in positions}
        elif self.code == 2: # 广州
            SCORE_STR = "EFBDCAGHIJKLMNOPGRSTUVWXYZ"
            diff_str = {i[2] for i in positions}

        # 计算每个不同库位得分之和
        return sum([2**SCORE_STR.index(i) for i in diff_str])

    def get_custom_amount(self):
        '''计算package的通关打印金额, 这个金额根据各个渠道需求进行设置'''
        # todo add custom_amount字段
        if hasattr(self, 'custom_amount') and self.custom_amount:
            return self.custom_amount

        custom_amount = 0
        #shop为choies
        shop_type = self.order.channel.type
        if shop_type == 0:
            items = self.packageitem_set.values_list('item__product__category__name', 'qty')
            for category, qty in items:
                # todo shoes的category确定
                if category.lower() == 'shoes':
                    custom_amount += 15 * qty
                # todo 首饰的category的确定
                elif category.lower() in ['anklets', 'body chains', 'bracelets & bangles', 'earrings', 'necklaces', 'rings']:
                    custom_amount += 0.5 * qty
                else:
                    custom_amount += 5 * qty
        # todo 速卖通和wholesale的shop确认
        elif shop_type in (2, 8):
            custom_amount = self.get_qty() * 2
        if custom_amount >= 20 or custom_amount == 0:
            return 20
        else:
            return custom_amount

    def set_to_logistics(self):
        '''给物流api准备好package和packageitem的数据
        物流api一般只传递一个packageitem, 数量传递这个包裹中准确的数量'''
        self.name = self.get_name()
        self.qty = self.get_qty()
        self.weight = self.weight or self.get_weight()
        self.address = self.get_address()
        self.custom_amount = self.get_custom_amount()
        if self.qty:
            self.price = round(float(self.custom_amount) / self.qty, 2)
        else:
            self.price = 0

        packageitem = self.packageitem_set.first()
        if packageitem:
            packageitem.name, packageitem.cn_name = packageitem.get_item_name()
        return packageitem

    def have_nails(self):
        '''判断是否含有指甲油(发货的时候, 如果含有指甲油, 则需要手工发货)'''
        package_item_categorys = self.packageitem_set.values_list('item__product__category__name', flat=True)
        if 'nails' in [i.lower for i in package_item_categorys]:
            return True
        else:
            return False

    def get_carrier(self):
        '''根据指定规则, 获取当前package的carrier label, 如果没有合适的, 则返回空字符串'''
        carrier = ''

        amount_shipping = round(self.order.amount_shipping / self.order.rate, 2)
        shipping_country = self.shipping_country.code
        weight = self.get_weight()
        tongguan = True if not self.order.cannot_tongguan() else False

        if self.note or self.order.note:
            pass

        # ky即smt的物流方式
        elif self.order.channel.type == 2:
            # 港澳台, 国内
            if shipping_country in ['HK','MO','TW',"CN"]:
                carrier = 'SF'
            else:
                if amount_shipping >= 10 or self.order.shipping_type == 1:
                    # 阿联酋、印度、阿曼、孟加拉国
                    if shipping_country in ['AE', 'IN', 'OM', 'BD']:
                        carrier = 'ARAMEX'
                    else:
                        carrier = 'EMS'
                elif amount_shipping < 10 or self.order.shipping == 0:
                    # 美国、美属维尔京群岛
                    if shipping_country in ['US']:
                        if tongguan:
                            carrier = 'EUB'
                        else:
                            carrier = 'DEUB'
                    elif shipping_country == 'CA':
                        # 因为ky即smt, 所以亚马逊的规则无效了, 这里删除
                        # if package.order.shop_id in [13,2] and tongguan:
                        #     carrier = 'EUB'
                        # elif package.order.shop_id in [13,2] and (not tongguan):
                        #     carrier = 'DEUB'
                        if tongguan:
                            carrier = 'NXB'
                        else:
                            carrier = 'DNXB'
                    elif shipping_country == 'RU':
                        # 根据package的order的amount来判断
                        order_amount = round(self.order.amount / self.order.rate, 2)
                        if order_amount < 10:
                            carrier = 'SFRU'
                        elif 10 <= order_amount < 100:
                            carrier = 'NXB'
                    elif tongguan:
                        carrier = 'NXB'
                    else:
                        carrier = 'DNXB'
        # 下面是除了smt之外的规则即ws
        elif self.have_nails:
            self.note += u'含有指甲油, 需要手动发货'
            self.save()
        else:
            hkpt_countries = [
                'IS','MC','VA','AL','MK','RS','KH','MM','CL','CR','PA','PY','PE','UY','KO','IC',
                'AF','AG','GS','AO','BB','BD','BF','BI','BJ','BO','BS','BT','BW','BZ','CI','CK',
                'CM','CO','CU','CV','CX','DJ','DZ','EC','EH','ER','ET','FJ','FO','GA','GD','GE',
                'GF','GH','GI','GM','GN','GQ','GT','GU','GW','GY','HN','HT','IQ','IR','JM','KE',
                'KM','KY','LI','LR','LS','MG','MH','ML','MQ','MR','MU','MV','MW','NF','KI','AD',
                'NI','NP','NR','NU','PG','PR','RW','SB','SD','SL','SM','SN','SO','SR','SV','TD',
                'TG','TL','TN','TO','TT','TV','UG','VE','VU','YE','ZM','ZW','IF','JI','EI','ZR',
                'AI','AS','AW','BM','BN','CC','CD','CF','CG','DO','FK','FM','GL','GP','HM','IO',
                'KN','LA','LC','LY','MP','MS','NC','PM','PN','PW','SJ','TC','TF','TK','TZ','UM',
                'VC','VG','VI','WF','WS','ME',]

            # 港澳台
            if shipping_country in ['HK', 'MO', 'TW']:
                carrier = 'SF'
            # 中国大陆
            elif shipping_country in ['CN']:
                carrier = 'SFZG'
            # 发快递(快递比较贵)
            elif amount_shipping >= 10 or self.order.shipping == 1:
                # 澳大利亚,巴布亚新几内亚,菲律宾,韩国,柬埔寨,马来西亚,蒙古,日本,泰国,新加坡,新西兰,印度尼西亚,越南,朝鲜
                if shipping_country in ['AU','PG','PH','KR','KH','MY','MN','JP','TH','SG','NZ','ID','VN','KP']:
                    carrier = 'EMS'
                # 俄罗斯 巴林 科威特 卡塔尔 约旦 黎巴嫩 沙特阿拉伯 埃及 伊朗 塞浦路斯 土耳其 以色列 斯里兰卡 巴基斯坦
                elif shipping_country in ['CY','RU','TR','IL','JO','QA','SA','BH','EG','IR','KW','LB','LK','PK']:
                    pass
                # 阿联酋、印度、阿曼、孟加拉国
                elif shipping_country in ['AE','IN','OM','BD']:
                    carrier = 'ARAMEX'
                # 爱尔兰,爱沙尼亚,奥地利,波兰,丹麦,芬兰,格恩西岛,加拿大,捷克,拉脱维亚,立陶宛,马耳他,墨西哥,挪威,葡萄牙,瑞典,泽西,瑞士,塞浦路斯,斯洛伐克,斯洛文尼亚,希腊,匈牙利
                elif shipping_country in ['IE','EE','AT','PL','DK','FI','GG','CZ','LV','LT','MT','NO','PT','SE','JE','CH','CY','SK','SI','GR','HU']:
                    carrier = 'DHL'
                # 英国,德国,法国,比利时,意大利,西班牙,卢森堡,荷兰
                elif shipping_country in ['GB','DE','FR','BE','IT','ES','LU','NL']:
                    carrier = 'DHL'
                # 美国
                elif shipping_country in ['US','CA','MX']:
                    carrier = 'DHL'
                else:
                    pass
            elif amount_shipping < 10 or self.order.shipping == 0:
                if shipping_country == 'US':
                    if self.order.shop_id != 7:
                        if not tongguan:
                            carrier = 'MU'
                        elif weight < 1:
                            carrier = 'SUB'
                        else:
                            carrier = 'MU'
                    else:
                        if weight < 1.85:
                            carrier = 'SUB'
                        else:
                            carrier = "DHL"
                elif shipping_country == 'CA':
                    if weight < 1.85:
                        carrier = 'DGM'
                    else:
                        carrier = 'DHL'
                #乌克兰,以色列
                elif shipping_country in ['UA','IL']:
                    carrier = 'KYD'
                # 巴西
                elif shipping_country in ['BR']:
                    carrier = 'SEB'
                # 英国,卢森堡,荷兰,拉脱维亚
                elif shipping_country in ['GB','LU','NL','LV']:
                    if weight > 0.6 and weight < 1.85:
                        carrier = 'MU'
                    elif tongguan and weight <= 0.6:
                        carrier = 'KYD'
                    elif not tongguan and weight <= 0.6:
                        carrier = "MU"
                    else:
                        carrier = 'DHL'
                # 芬兰,冰岛,葡萄牙,斯洛伐克
                elif shipping_country in ['FI','IS','PT','SK']:
                    carrier = 'NLR'
                # 捷克,立陶宛,斯洛文尼亚
                elif shipping_country in ['CZ','LT','SI']:
                    if weight < 1:
                        carrier = 'NLR'
                    elif weight >= 1 and weight <= 1.85:
                        carrier = 'MU'
                    else:
                        carrier = 'DHL'
                # 罗马尼亚
                elif shipping_country in ['RO',]:
                    if weight < 1.5:
                        carrier = 'NLR'
                    elif weight >= 1.5 and weight <= 1.85:
                        carrier = 'MU'
                    else:
                        'DHL'
                # 澳大利亚
                elif shipping_country == 'AU':
                    if weight < 1:
                        carrier = 'KYD'
                    else:
                        carrier = 'MU'
                # 匈牙利,瑞典,爱沙尼亚,爱尔兰
                elif shipping_country in ['HU','SE','EE','IE']:
                    if weight > 1 and weight < 1.85:
                        carrier = 'MU'
                    elif weight <= 1:
                        carrier = 'KYD'
                    else:
                        carrier = 'DHL'
                #印度尼西亚,文莱,新西兰,菲律宾
                elif shipping_country in ['ID','BN','NZ','PH']:
                    if weight < 1.85:
                        carrier = 'KYD'
                    else:
                        carrier = 'EMS'
                elif shipping_country == 'RU':
                    if weight < 1.85:
                        carrier = 'XRA'
                # 波斯尼亚和黑塞哥维那
                elif shipping_country in ['BA']:
                    carrier = 'HKPT'
                # 奥地利,波兰
                elif shipping_country in ['AT','PL']:
                    if weight < 1.85:
                        carrier = 'NLR'
                    else:
                        weight = 'DHL'
                # 瑞士,丹麦
                elif shipping_country in ['CH','DK']:
                    if weight < 1.85 and tongguan:
                        carrier = 'KYD'
                    elif weight < 1.85 and not tongguan:
                        carrier = 'KYD'
                    else:
                        carrier = 'DHL'
                # 德国
                elif shipping_country in ['DE']:
                    if weight < 1.85:
                        carrier = 'DGM'
                    else:
                        carrier = 'DHL'
                # 比利时,西班牙
                elif shipping_country in ['BE', 'ES']:
                    if weight < 1.85:
                        carrier = 'NLR'
                    else:
                        carrier = 'DHL'
                # 韩国
                elif shipping_country in ['KR']:
                    if weight < 1.85:
                        carrier = 'KYD'
                    else:
                        carrier = 'EMS'
                # 新加坡
                elif shipping_country in ['SG']:
                    if weight < 1.85 and tongguan:
                        carrier = 'KYD'
                    elif weight < 1.85 and not tongguan:
                        carrier = 'KYD'
                    else:
                        carrier = 'EMS'
                # 沙特阿拉伯,科威特,南非,越南,摩洛哥,黎巴嫩,巴林,阿塞拜疆,埃及,约旦,卡塔尔,尼日利亚,摩尔多瓦
                elif shipping_country in ['SA','KW','ZA','VN','MA','LB','BH','AZ','EG','JO','QA','NG','MD']:
                    if weight < 1.85:
                        carrier = 'HKPT'
                elif shipping_country in hkpt_countries:
                    carrier = 'HKPT'
                # 墨西哥
                elif shipping_country in ['MX']:
                    if weight < 1.85:
                        carrier = 'HKPT'
                    else:
                        carrier = 'DHL'
                elif shipping_country in ['IT']:
                    if weight < 1.85 and tongguan:
                        carrier = 'KYD'
                    elif weight < 1.85 and not tongguan:
                        carrier = 'KYD'
                    else:
                        carrier = 'DHL'
                elif shipping_country in ['FR']:
                    if weight < 1.85:
                        carrier = "DGM"
                    else:
                        carrier = 'DHL'
                #阿联酋,
                elif shipping_country in ['AE',]:
                    if weight < 1.85:
                        carrier = 'SGB'
                    else:
                        carrier = 'ARAMEX'
                else:
                    if tongguan:
                        carrier = 'KYD'
                    else:
                        carrier = 'KYD'
        return carrier

    def _delete(self):
        for packageitem in self.packageitem_set.all():
            packageitem.deleted = True
            packageitem.save()

    def save(self, *args, **kw):
        # package 变成取消状态
        PACKAGE_CANCEL = 4
        if self._status != PACKAGE_CANCEL and self.status == PACKAGE_CANCEL:
            self._delete()
        super(Package, self).save(*args, **kw)

    def delete(self, *args, **kwargs):
        self._delete()
        super(Package, self).delete(*args, **kwargs)

class PackageItem(models.Model):
    package = models.ForeignKey(Package, verbose_name='包裹单号')
    item = models.ForeignKey(product.models.Item, verbose_name='包裹货品')
    qty = models.IntegerField(default=0, verbose_name='数量')
    note = models.TextField(default='', blank=True, null=True, verbose_name='备注')
    deleted = models.BooleanField(default=False, verbose_name='是否已删除')

    created = models.DateTimeField(auto_now_add=True, verbose_name='新增时间')
    updated = models.DateTimeField(auto_now=True, verbose_name='修改时间')
    _qty = 0

    class Meta:
        verbose_name = u'包裹单货品'
        verbose_name_plural = u'包裹单货品'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def get_positions(self):
        """获得这个package_item的库位"""
        positions = list(ItemLocked.objects.filter(package_item=self.id).values_list('depot_item__position', flat=True))
        position_list = ','.join(positions).split(',')
        no_repeat_position = []
        for i in position_list:
            no_repeat_position.append(i)
        return ','.join(no_repeat_position)

    def get_total(self):
        """这个包裹的成本使用出库记录中的成本"""
        total = 0
        try:
            info = depot.models.DepotOutLog.objects.filter(item_id=self.item_id)\
                                                   .filter(content_object=self.package)\
                                                   .filter(deleted=False)\
                                                   .values_list('qty', 'cost')
            for qty, cost in info:
                total += qty * cost
        except:
            pass
        return total

    def __unicode__(self):
        return "PackageItem:%s" % self.id

    _item_id = 0
    _qty = 0
    _deleted = False

    def __init__(self, *args, **kwargs):
        super(PackageItem, self).__init__(*args, **kwargs)
        self._item_id = self.item_id
        self._qty = self.qty
        self._deleted = self.deleted

    def save(self, *args, **kw):
        # 当packageitem删除的时候, 使用_delete删除对应的itemwanted和itemlocked
        if self.deleted and not self._deleted and self.id:
            self._delete()

        # 需要先保存packageitem的数量, 然后后面调用package_get_items中用的qty才对
        super(PackageItem, self).save(*args, **kw)

        # 当packageitem的数量改变的时候, 调用package_get_items
        if self.qty != self._qty:
            from package_action import package_get_items
            package_get_items(self.package)

        if self._item_id != self.item_id or self._qty != self.qty:
            self.package.qty = self.package.get_qty()
            self.package.sku_qty = self.package.get_sku_qty()
            self.package.weight = self.package.get_weight()
            self.package.save()

    def _delete(self):
        # delete item wanted
        self.deleted = True
        for itemwanted in ItemWanted.objects.filter(package_item=self).filter(deleted=False):
            itemwanted.deleted = True
            itemwanted.save()
        # delete item locked

        for itemlocked in ItemLocked.objects.filter(package_item=self).filter(deleted=False):
            itemlocked.deleted = True
            itemlocked.save()

    def delete(self, *args, **kwargs):
        self._delete()
        super(PackageItem, self).delete(*args, **kwargs)


    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def get_item_name(self):
        en_name = self.item.product.category.name
        cn_name = self.item.product.category.cn_name
        return en_name, cn_name

class PackagePickError(models.Model):
    pick = models.ForeignKey(depot.models.Pick)  # 记录当时的pick单
    package = models.ForeignKey(Package)
    error_type = models.IntegerField(choices=Package.PICK_STATUS, default=4, verbose_name=u'异常类型')
    is_processed = models.BooleanField(default=False, verbose_name=u'是否处理')
    processor = models.ForeignKey(User, null=True, blank=True, verbose_name=u'处理人')
    process_time = models.DateTimeField(null=True, verbose_name=u'处理时间')
    error_info = models.TextField(default='', blank=True, verbose_name=u'异常相关信息')

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    def __unicode__(self):
        return "Package(%s):%s(%s)" % (self.package_id, self.get_error_type_display(), self.id)

class ItemLocked(models.Model):
    package_item = models.ForeignKey(PackageItem) #一个package_item可以对应多个ItemLocked，一个item锁不同仓库的库存
    depot_item = models.ForeignKey(depot.models.DepotItem)

    qty = models.PositiveIntegerField(default=1)
    note = models.TextField(default='', blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)
    deleted = models.BooleanField(default=False)

    _deleted = False

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def __unicode__(self):
        return "ItemLocked:%s" % self.id

    class Meta:
        verbose_name = u'包裹占用库存'
        verbose_name_plural = u'包裹占用库存'

    def _delete(self):
        self.depot_item.qty_locked = self.depot_item.qty_locked - self.qty if self.depot_item.qty_locked > self.qty else 0
        self.depot_item.save()

    def __init__(self, *args, **kwargs):
        super(ItemLocked, self).__init__(*args, **kwargs)
        self._deleted = self.deleted

    def save(self, *args, **kw):
        if not self.deleted:
            if not self.id:
                self.depot_item.qty_locked = self.depot_item.qty_locked + self.qty
                self.depot_item.save()
        else:
            if not self._deleted and self.id:
                self._delete()
        super(ItemLocked, self).save(*args, **kw)

    def delete(self, *args, **kwargs):
        print 'start delete'
        self._delete()
        super(ItemLocked, self).delete(*args, **kwargs)

class ItemWanted(models.Model):
    item = models.ForeignKey(product.models.Item, verbose_name=u"采购需求物品")
    depot = models.ForeignKey(depot.models.Depot, verbose_name=u"采购入库仓库")
    package_item = models.ForeignKey(PackageItem)
    purchaseorderitem = models.ForeignKey('supply.PurchaseOrderItem', null=True, blank=True)
    qty = models.PositiveIntegerField(default=1, verbose_name=u"采购需求数量")
    create_time = models.DateTimeField(auto_now_add=True, verbose_name=u"订单时间")

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    class Meta:
        verbose_name = u'采购需求'
        verbose_name_plural = u'采购需求'

    def get_admin_url(self):
        content_type = ContentType.objects.get_for_model(self.__class__)
        return reverse("admin:%s_%s_change" % (content_type.app_label, content_type.model), args=(self.id,))

    def _delete(self):
        self.deleted = True

    def delete(self, *args, **kwargs):
        print 'start delete'
        self._delete()
        super(ItemWanted, self).delete(*args, **kwargs)

class NxbCode(models.Model):
    code = models.CharField(max_length=50, unique=True)
    is_used = models.IntegerField(default=0, verbose_name=u'是否使用过')
    used_time = models.DateTimeField(blank=True, null=True, verbose_name=u'使用时间')
    package = models.ForeignKey(Package, null=True, blank=True)
    note = models.CharField(max_length=255, default='', blank=True, verbose_name='备注')

    created = models.DateTimeField(auto_now_add=True, verbose_name=u"新增时间")
    updated = models.DateTimeField(auto_now=True, verbose_name=u"修改时间")
    deleted = models.BooleanField(default=False, verbose_name=u"是否已删除")

    def __unicode__(self):
        return "%s: %s" % (self.id, self.code)

