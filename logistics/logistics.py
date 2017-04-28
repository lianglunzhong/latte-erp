# coding: utf-8
import xmltodict

from chukouyi import Chukouyi
from donghang import Donghang
from eub import Eub
from feite import Feite
from hulianyi import Hulianyi
from jisu import Jisu
from sf import Sfworld, Sfhome, Sfru

from shipping.models import NxbCode
from lib.utils import get_now, set_timeout

class ShippingList(object):
    """保存所有api的大类和内容名称"""
    hulianyi  = ["MYB", "KYD", "HKPT", "DGM", "XRA", "SGB"]
    donghang  = ["MU", ]
    jisu      = ['EMS', 'DHL', 'ARAMEX']
    sfworld   = ["NLR", "SEB"]
    # sfhome = ["SF", ],   #sf暂停api, 为了不影响原逻辑, 改为空字符串即可 0315
    sfhome    = []
    sfru      = ["SFRU", ]
    eub       = ["EUB", "DEUB", "GUB", "SUB"]
    nxb       = ["NXB", "DNXB"]
    chukouyi  = ['CUE', 'CRI']
    feite     = ['UPS', ]

    have_api_shipping = hulianyi + donghang + jisu + sfworld + sfhome + sfru + eub + nxb + chukouyi + feite

    all_list = {
        'hulianyi'  : hulianyi,
        'donghang'  : donghang, 
        'jisu'      : jisu, 
        'sfworld'   : sfworld,
        'sfhome'    : sfhome,
        'sfru'      : sfru,
        'eub'       : eub, 
        'nxb'       : nxb, 
        'chukouyi'  : chukouyi,
        'feite'     : feite,
    }

def verify_can_shipping(package):
    """判断package是否能进行物流商下单"""
    result = {
        'success': False,
        'msg':'',
    }

    if not package.get_qty():
        result['msg'] += u'packageitem数量为0 | \n'

    if not package.shipping:
        result['msg'] += u'还未分配物流方式 | '

    if package.shipping and package.shipping.label not in ShippingList.have_api_shipping:
        result['msg'] += u'%s 没有api | ' % package.shipping.label

    if not result['msg']:
        result['success'] = True
    return result


def logistics_tracking_no(package):
    """根据package的shipping, 获取这个package的运单号
    返回数据为字典格式
    如果成功, 则数据为 {'success': True, 'tracking_no': '123456567', 'msg': ''}
    如果失败, 则数据为 {'success': False, 'tracking_no':'', 'msg': 'The reason of failure'}
    """
    label = package.shipping and package.shipping.label

    #邮政小包
    if label in ShippingList.nxb:
        result = nxb_distribute(package)
    #E邮宝
    elif label in ShippingList.eub:
        result = eub_distribute(package)
    #东航
    elif label in ShippingList.donghang:
        result = donghang_distribute(package)
    #顺丰国际
    elif label in ShippingList.sfworld:
        result = sfworld_distribute(package)
    #顺丰国内
    elif label in ShippingList.sfhome:
        result = sfhome_distribute(package)
    #顺丰俄国
    elif label in ShippingList.sfru:
        result = sfru_distribute(package)
    #互联易
    elif label in ShippingList.hulianyi:
        result = hulianyi_distribute(package)
    # 急速
    elif label in ShippingList.jisu:
        result = jisu_distribute(package)
    # 出口易 todo 这个api好像不用了, 如果要用的话, 可能需要再调试, 遗留问题很大
    elif label in ShippingList.chukouyi:
        result = chukouyi_distribute(package)
    # 飞特
    elif label in ShippingList.feite:
        result = feite_distribute(package)

    return result


def nxb_distribute(package):
    result = {'success': False, 'tracking_no': '', 'msg':'', }

    nxb_code = NxbCode.objects.filter(is_used=0).first()
    if not nxb_code:
        result['msg'] += u'nxb的运单号已经用完'
    else:
        nxb_code.is_used = 1
        nxb_code.used_time = get_now()
        nxb_code.package_id = package.id
        nxb_code.save()

        result['success'] = True
        result['tracking_no'] = nxb_code.code
    
    return result

def eub_distribute(package):
    result = {'success': False, 'tracking_no': '', 'msg':'', }
    # eub的api可能会卡主, 因此设置timeout=5执行时间, 最大尝试次数为3
    for i in range(3):
        try:
            eub = Eub(package.shipping.label)
            tracking_data = eub.order(package)
            break
        except Exception, e:
            print "EUB try numbers:%s timeout. %s %s %s" % (i+1, package.id, get_now(), str(e))
            tracking_data = ''

    if 'order' in tracking_data:
        result['success'] = True
        result['tracking_no'] = tracking_data['order']['mailnum']
    elif tracking_data.get('response', {}).get('status', '') == 'error':
        result['msg'] += tracking_data['response']['description']
    else:
        result['msg'] += u'获取订单号失败'

    return result


def donghang_distribute(package):
    result = {'success': False, 'tracking_no': '', 'msg':'', }
    donghang = Donghang()
    r = donghang.order(package)
    if not r['status']:
        result['msg'] = r['message']
    else:
        result['success'] = True
        result['tracking_no'] = r['data']['tracking_num']
    return result

def sfworld_distribute(package):
    """sfworld比较特殊, 包含3个tracking_no相关的信息, 两个是用来发货的, 需要建立字段保存"""
    sf = Sfworld()
    result = sf.order(package)
    if result['success']:
        package.sf_numbers = result['sf_numbers']
        package.skybill_code = result['skybill_code']
        package.save()

    return result

def sfhome_distribute(package):
    sf = Sfhome()
    result = sf.order(package)
    return result

def sfru_distribute(package):
    """sfru包含了两个tracking_no相关的信息"""
    sf = Sfru()
    result = sf.order(package)
    if result['success']:
        package.sf_numbers = result['sf_numbers']
        package.save()
    return result

def hulianyi_distribute(package):
    hulianyi = HulianyiApi()
    result = hulianyi.order(package)
    return result

def jisu_distribute(package):
    result = {'success': False, 'tracking_no': '', 'msg':'', }
    jisu = Jisu()
    r = jisu.order(package)
    r_list = r.split('\r\n')
    if int(r_list[0]) > 0:
        result['success'] = True
        result['tracking_no'] = r_list[-1]
    else:
        result['msg'] = Jisu.error_message.get(r_list[0]) or u'急速获取单号失败'
    return result

# 出口易应该暂时不用了
def chukouyi_distribute(package):
    chukouyi = Chukouyi()
    result = chukouyi.order(package)    
    return result

def feite_distribute(package):
    feite = Feite()
    result = feite.order(package)
    return result