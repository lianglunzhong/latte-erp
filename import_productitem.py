# -*- coding: utf-8 -*-
import datetime
from django.utils import timezone
import sys, os
reload(sys)
sys.setdefaultencoding('utf-8')
import csv
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'

import django
django.setup()


from product.models import *
from order.models import *

# 根据产品和产品属性生成属性产品
products = Product.objects.all().order_by('id')
# products = Product.objects.filter(id=5393)
for p in products:
    # print 'cate',p.category_id,p.description
    category = Category.objects.get(pk=p.category_id)
    # 更新产品sku编码
    # p.sku = str(category.code)+str(p.id)
    # p.sku = u"%s%06d" % (category.code, p.id)
    # p.save()


    # for attribute in category.attributes.all().exclude(id=11):
    #     # print 'attr_id',attribute.id
    #     product_attribute, is_created = ProductAttribute.objects.get_or_create(attribute_id=attribute.id,product_id=p.id)
    product_attributes = ProductAttribute.objects.filter(product_id=p.id).exclude(attribute_id=11)
    for product_attribute in product_attributes:
        # print product_attribute.attribute_id
        options = p.description.split('#')
        for opx in options:
            op = opx.replace('SIZE:', '').replace(' ', '').strip().upper()

            if "ONE" in op:
                op = 'ONESIZE'
            elif not op:
                op = 'ONESIZE'
                print 'not op', opx
            elif op in ('????', "均码",'???','error'):
                op = 'ONESIZE'
                print 'is ?', opx
            elif op == 'X':
                op = "XL"
            elif len(op) == 3 and op[1:] == 'XL' and op[0] != 'X':
                try:
                    op = int(op[0]) * 'X' + 'L'
                except Exception,e:
                    print opx,'#', p.id,'#', p.sku,'#', p.choies_sku

            # print 'op',op
            try:
                option = Option.objects.get(name=op,attribute_id=product_attribute.attribute_id)
                product_attribute.options.add(option)
                # # item_str = str(p.id) +'-0-'+str(option.id)
                # item_str = str(p.id) +'-'+str(option.id)
                # # item_sku = u"%s-0-%s"% (p.sku,option.name)
                # item_sku = u"%s%s"% (p.sku,option.code)
                # item, is_created = Item.objects.get_or_create(product_id=p.id, key=item_str,sku=item_sku)
                # # print 'item_str',item_str
                # # 针对ws系统下的sku生成choies渠道的别名
                # sku_str = str(p.choies_sku)+'-'+str(option.name)
                # # print 'sku_str',sku_str,'item_id',item.id
                # Alias.objects.get_or_create(sku=sku_str,channel_id=1,item_id=item.id)
            except Exception,e:
                print opx,'#', p.id,'#', p.sku,'#', p.choies_sku,'# save no',e

exit()



# 获取产品表中现所有的分类及分类属性选项
products = Product.objects.filter(id__gte=306).values('category_id','description').distinct()
temp = {}
i=0

for p in products:
    # print p
    i= i+1
    # print p.category_id,p.description

    if temp.has_key(p['category_id']):
        temp[p['category_id']] = temp[p['category_id']] + '#'+p['description']
    else:
        temp[p['category_id']] = p['description']

fieldnames = ['分类id', '属性选项']
dict_writer = csv.writer(open('category_data.csv','wb'))
dict_writer.writerow(fieldnames)

for key,value in temp.iteritems():
    temp[key] = value.split('#')
    temp[key] = list(set(temp[key]))
    cate = Category.objects.filter(id=key,id__gte=354).values('name')
    print cate[0]['name']
    temp2 = [key, cate[0]['name'], '#'.join(str(e) for e in temp[key])]
    dict_writer.writerow(temp2)
print temp
exit()

