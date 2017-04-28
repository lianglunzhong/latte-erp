# coding: utf-8
from lib.utils import get_now
from sf import Sfworld, Sfhome, Sfru
from eub import Eub
from chukouyi import Chukouyi
from logistics import ShippingList

def get_label_data(packages):
    """获取面单数据
    输入的packages应该: 属于同一物流方式, 且已获取运单号
    返回result
    result['datas']: 保存面单数据的list, 元素为dict
    result['template']: 指明使用的html模板文件
    result['msg']: 如果数据出错, 保存出错信息
    """
    result = {
        'datas': [],
        'template': '',
        'msg': '',
    }

    try:
        shipping_label = packages[0].shipping.label.upper()
    except Exception, e:
        result['msg'] += u'获取包裹的物流方式失败 %s | ' % e
        return result

    # 邮政小包
    if shipping_label in ShippingList.nxb:
        result = nxb_get_data(packages)
    # 东航
    elif shipping_label in ShippingList.donghang:
        result = donghang_get_data(packages)
    # EUB
    elif shipping_label in ShippingList.eub:
        result = eub_get_data(packages)
    # 急速
    elif shipping_label in ShippingList.jisu:
        result = jisu_get_data(packages)
    # 出口易
    elif shipping_label in ShippingList.chukouyi:
        result = chukouyi_get_data(packages)
    # 飞特
    elif shipping_label in ShippingList.feite:
        result = feite_get_data(packages)
    # 顺丰国际
    elif shipping_label in ShippingList.sfworld:
        result = sfworld_get_data(packages)
    # 顺丰国内
    elif shipping_label in ShippingList.sfhome:
        result = sfhome_get_data(packages)
    # 顺丰俄国
    elif shipping_label in ShippingList.sfru:
        result = sfru_get_data(packages)
    return result

def get_pdf_label(package):
    """目前eub和sf提供pdf面单"""
    link = ''
    label = package.shipping.label
    if label in ShippingList.eub:
        eub = Eub(label)
        link = eub.get_single_pdf(package.tracking_no)

    return link



def nxb_get_data(packages):
    result = {
        'datas': [],
        'template': 'nxb.html',
        'msg': '',
    }

    for package in packages:
        packageitem = package.set_to_logistics()

        data = {
            'package_id': package.id,
            'address': package.name + '<br>'\
                       + package.address + '<br>'\
                       + package.shipping_city + ','\
                       + package.shipping_state + ','\
                       + package.shipping_country.name,
            'zip': package.shipping_zipcode,
            'phone': package.shipping_phone,
            'tracking_code': package.tracking_no,
            'country_code': package.shipping_country.code,
            'country_cn': package.shipping_country.cn_name,
            'set': packageitem.name,
            'date': get_now(),
            'customs_amount': package.custom_amount,
        }
        result['datas'].append(data)
    return result

def donghang_get_data(packages):
    result = {
        'datas': [],
        'template': 'donghang.html',
        'msg': '',
    }

    for package in packages:
        packageitem = package.set_to_logistics()

        data = {
            'package_id': package.id,
            'ship_name': package.name,
            'ship_address': package.address,
            'ship_city': package.shipping_city,
            'ship_state': package.shipping_state,
            'ship_country': package.shipping_country.name,
            'zip': package.shipping_zipcode,
            'phone': package.shipping_phone,
            'tracking_code': package.tracking_no,
            'country_code': package.shipping_country.code,
            'set_name': package.name,
            'set_cn_name': package.cn_name,
            'qty': package.qty,
        }
        result['datas'].append(data)
    return result

def eub_get_data(packages):
    result = {
        'datas': [],
        'template': 'eub.html',
        'msg': '',
    }

    for package in packages:
        packageitem = package.set_to_logistics()

        if package.shipping_country.code == 'US':
            country_name = 'UNITED STATES OF AMERICA'
        else:
            result['msg'] += u' | package: ' + str(package_id) + u'不发美国之外的国家'
            result['datas'].append({})
            continue

        if package.shipping_country.code == "US":
            pick_code = Eub.get_pick_code(package.shipping_zipcode)
        else:
            pick_code = 4

        data = {
            'package_id': package.id,
            'ship_name': package.name,
            'ship_address': package.address,
            'ship_city': package.shipping_city,
            'ship_state': package.shipping_state,
            'ship_country': country_name,
            'zip': package.shipping_zipcode,
            'phone': package.shipping_phone,
            'tracking_code': package.tracking_no,
            'country_code': package.shipping_country.code,
            'set_name': packageitem.name,
            'set_cn_name': packageitem.cn_name,
            'date': get_now(),
            'qty': package.qty,
            'customs_amount': package.custom_amount,
            'pick_code': pick_code,
        }
        result['datas'].append(data)
    return result

def jisu_get_data(packages):
    result = {
        'datas': [],
        'template': 'jisu.html',
        'msg': '',
    }
    try:
        ship_type = packages[0].shipping.label.upper()
    except Exception, e:
        result['msg'] += u'JISU获取包裹物流方式失败 %s | ' % e
        return result

    for package in packages:
        packageitem = package.set_to_logistics()

        data = {
            'ship_type': ship_type,
            'package_id': package.id,
            'ship_name': package.name,
            'ship_address': package.address,
            'ship_city': package.shipping_city,
            'ship_state': package.shipping_state,
            'ship_country': package.shipping_country.name,
            'zip': package.shipping_zipcode,
            'phone': package.shipping_phone,
            'tracking_code': package.tracking_no,
            'country_code': package.shipping_country.code,
            'set_name': packageitem.name,
            'set_cn_name': packageitem.cn_name,
            'qty': package.qty,
        }
        result['datas'].append(data)
    return result

def chukouyi_get_data(packages):
    result = {
        'datas': [],
        'template': 'chukouyi.html',
        'msg': '',
    }
    try:
        ship_type = packages[0].shipping.label.upper()
    except Exception, e:
        result['msg'] += u'出口易获取包裹物流方式失败 %s | ' % e
        return result

    for package in packages:
        packageitem = package.set_to_logistics()

        attice_number = Chukouyi.get_attice_number(package.shipping_country.code)
        if not attice_number:
            result['msg'] += u' | package: %s 找不到对应的格口号' % package.id
            result['datas'].append({})
            continue

        data = {
            'package_id': package.id,
            'weight': 0.3,
            'amount_shipping': package.custom_amount,
            "sender": u'韦胜彬',
            # todo 在html上使用过滤器
            "sendetime": get_now(),
            "recivename": package.name,
            "reciveaddress": package.address,
            "city": package.shipping_city,
            "state": package.shipping_state,
            "country_code": package.shipping_country.code,
            "country_name": package.shipping_country.name,
            "country_cnname": package.shipping_country.cn_name,
            "zipcode": package.shipping_zipcode,
            "recivephone": package.shipping_phone,
            "tracking_code": package.tracking_no,
            "attice_number": attice_number,
            "chukouyi_flag": 'AAU',
            "ship_label": ship_type,
            "set_name": packageitem.name,
            "itemSign": package.tracking_no
        }
        result['datas'].append(data)
    return result

def feite(packages):
    result = {
        'datas': [],
        'template': 'feite.html',
        'msg': '',
    }

    for package in packages:
        packageitem = package.set_to_logistics()

        data = {
            'package_id': package.id,
            "receiverName": package.name,
            "address1": package.address,
            "city": package.shipping_city,
            "state": package.shipping_state,
            "phone": package.shipping_phone,
            "tracking_code": package.tracking_no,
            "sku": packageitem.item.sku,
        }
        result['datas'].append(data)
    return result

def sfworld_get_data(packages):
    result = {
        'datas': [],
        'template': '',
        'msg': '',
    }
    try:
        result['template'] = 'sfworld_%s.html' % packages[0].shipping.label.lower()
    except Exception, e:
        result['msg'] += u'顺丰国际获取包裹物流方式失败 %s | ' % e
        return result

    for package in packages:
        packageitem = package.set_to_logistics()
        pick_code = Sfworld.get_pick_code(package)

        data = {
            'package_id': package.id,
            'ship_name': package.name,
            'ship_address': package.address,
            'ship_city': package.shipping_city,
            'ship_state': package.shipping_state,
            'zip': package.shipping_zipcode,
            'ship_country': package.shipping_country.code,
            'country_name': package.shipping_country.name,
            'phone': package.shipping_phone,
            'tracking_no': package.tracking_no,
            'sf_numbers': package.sf_numbers,
            'skybill_code': package.skybill_code,
            'country_code': package.shipping_country.code,
            'set_name': packageitem.name,
            'set_cn_name': package_cn_name,
            'date': get_now(),
            'customer_code' : Sfworld.clientCode,
            'qty': package.qty,
            'customs_amount': package.custom_amount,
            'product_amount': package.price,
            'pick_code': pick_code,
        }
        result['datas'].append(data)
    return result

def sfhome_get_data(packages):
    result = {
        'datas': [],
        'template': 'sfhome.html',
        'msg': '',
    }
    sf = Sfhome()
    for package in packages:
        packageitem = package.set_to_logistics()

        # todo 这个destcode需要使用api查询
        destcode = sf.search(package.id)["destcode"]        

        # todo 展示的tracking_no是3位字母之间一个空格
        sub_tracking_no = " ".join([package.tracking_no[i:i+3] for i in range(0, len(package.tracking_no), 3)])

        data = {
            "server_type": "标准快递",
            "destcode": destcode,
            "des_country": package.shipping_country.code,
            "des_city": package.shipping_city,
            "des_state": package.shipping_state,
            "des_address": package.address,
            "des_ship_name": package.name,
            "des_phone": package.shipping_phone,
            "tracking_no": package.tracking_no,
            "sub_tracking_no": sub_tracking_no,
            "actual_weight": 0.3,
            "billing_weight": "",
            "source_state": "广州省",
            "source_city": "广州市",
            "source_district": "白云区",
            "source_address": "石槎路穗新创意园 A402",
            "source_name": "韦胜彬",

            "source_phone": 13218887792,
            "source_code": "020",
            # todo 在html上使用过滤器
            "ship_data": get_now(),
            "ship_ordernum": str(package.id),
            "ship_good_name": packageitem.cn_name,
            "total_value": total_value,
        }
        result['datas'].append(data)
    return result


def sfru_get_data(packages):
    result = {
        'datas': [],
        'template': 'sfru.html',
        'msg': '',
    }

    for package in packages:
        packageitem = package.set_to_logistics()

        pick_code = Sfru.get_pick_code(package.shipping_country.code)
        if not pick_code:
            result['msg'] += u' | package %s 没有拣货码' % package.id
            result['datas'].append({})
            continue


        datas = {
            'package_id': package.id,
            'ship_name': package.name,
            'ship_address': package.address,
            'ship_city': package.shipping_city,
            'ship_state': package.shipping_state,
            'zip': package.shipping_zipcode,
            'ship_country': package.shipping_country.code,
            'phone': package.shipping_phone,
            'tracking_no': package.tracking_no,
            'sf_numbers': package.sf_numbers,
            'country_code': package.shipping_country,
            'set_name': packageitem.name,
            'set_cn_name': packageitem.cn_name,
            'date': get_now(),
            'qty': package.qty,
            'customs_amount': package.custom_amount,
            'product_amount': package.price,
            'actual_weight': 0.3,
            'product_weight': round(0.3 / package.qty, 2),
            'pick_code': pick_code,
        }
        result['datas'].append(datas)
    return result
