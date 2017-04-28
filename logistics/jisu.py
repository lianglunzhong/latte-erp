# -*- coding: utf-8 -*-
import requests
import hashlib

class Jisu(object):
    '''获取订单号完善, 使用obj.order(package)
    急速就使用他们提供的单号即可'''

    base_url = 'http://121.41.92.144/cgi-bin/GInfo.dll'

    jisu_label = ['EMS', 'DHL', 'ARAMEX']

    # 客户id
    icid = 2383
    api_key = 'GZFRDZS20151020FUREN'
    timeout = 30

    error_dict = {
        "-1": u'客户不存在，没有为客户建立档案，或者客户ID不正确',
        "-2": u'运单号重复，< NUM >定义的运单号在系统中已经存在',
        "-3": u'GInfo系统未能读取初始化数据定义，不支持',
        "-4": u'GInfo系统版本错误，不是授权的快递专业版',
        "-6": u'没有解析到<MD5>标记数据',
        "-7": u'MD5签名校验失败，请注意密钥的统一！',
        "-9": u'数据库错误，GInfo平台问题',
        "-11": u'客户ID错误，没有定义默认客户ID或者<ICID>数据有问题',
        "-14": u'运单号数据错误< NUM >数据有问题(长度7-30 ASCII码字符)',
        "-15": u'快递类别(EMSKIND)错误,可以设置默认值(2.5)以避免此类错误',
    }

    # 订单信息传送接口
    def order(self, package):
        command = 'EmsApinv'

        packageitem = package.set_to_logistics()
        goods = u'''
            <GNAME>{packageitem.cn_name}</GNAME>
            <GQUANTITY>{package.qty}</GQUANTITY>
            <GPRICE>{package.price}</GPRICE>
            <GOODSA>{packageitem.name}</GOODSA>
        '''.format(package=package, packageitem=packageitem)

        # 内单号 = shipping_label + package_id
        ship_type = str(package.shipping.label).upper()
        package_data = {
            "package": package, 
            "ship_type": ship_type,
            "icid": self.icid,
            "num": '%s%d' % (ship_type, package.id),
            "goods": goods,
        }
        cdata = u'''
            <EMSKIND>{ship_type}</EMSKIND>
            <ICID>{icid}</ICID>
            <NUM>{num}</NUM>
            <TITEM>{package.qty}</TITEM>
            <WEIGHTT>{package.weight}</WEIGHTT>
            <GOODS> {goods} </GOODS>
            <RECEIVER>{package.name}</RECEIVER>
            <ADDRFROM>CN</ADDRFROM>
            <DES>{package.shipping_country.name}</DES>
            <RCOUNTRY>{package.shipping_country.name}</RCOUNTRY>
            <RPROVINCE>{package.shipping_state}</RPROVINCE>
            <RCITY>{package.shipping_city}</RCITY>
            <RADDR>{package.address}</RADDR>
            <RPOSTCODE>{package.shipping_zipcode}</RPOSTCODE>
            <RPHONE>{package.shipping_phone}</RPHONE>
            <MONEY>USD</MONEY>
            <MEMO></MEMO>'''.format(**package_data)

        md5_key = cdata.encode('utf8') + self.api_key
        md5_data = hashlib.md5(md5_key).hexdigest()
        cdata += '<MD5>%s</MD5>' % md5_data

        postdata = {
            'MfcISAPICommand': command,
            'cdata': cdata,
        }

        r = requests.post(self.base_url, postdata)
        return r.content


    # 订单追踪详细信息查询接口
    def get_track(self, cno):
        command = 'EmsApiTrack'
        if cno:
            get_url = self.base_url + '?MfcISAPICommand=%s&cno=%s' % (command, str(cno))
            r = requests.get(get_url, timeout=self.timeout)
            return r.content
        else:
            return ''

    # 已完成订单信息查询接口
    def get_track_state(self, cno_list):
        command = 'EmsTrackState'
        if cno_list:
            cno = ','.join([str(i) for i in cno_list])
            get_url = self.base_url + '?MfcISAPICommand=%s&cno=%s&ntype=10010' % (command, cno)
            r = requests.get(get_url, timeout=self.timeout)
            return r.content
        else:
            return ''

    # 转单号查询
    def get_query(self, cno_list):
        command = 'EmsApiQuery'
        if cno_list:
            cno = ','.join([str(i) for i in cno_list])
            md5_key = cno + self.api_key
            md5_data = hashlib.md5(md5_key).hexdigest()
            # postdata = {
            #     'MfcISAPICommand': command,
            #     'icid': self.icid,
            #     'cno': cno,
            #     'md5': md5_data,
            #     'ntype': 10000,
            # }
            # r = requests.post(self.base_url, postdata)
            get_url = self.base_url + '?MfcISAPICommand=%s&icid=%s&cno=%s&md5=%s&ntype=11000' % (command, self.icid, cno, md5_data)
            r = requests.get(get_url, timeout=self.timeout)
            return r.content
        else:
            return ''

    # 获取快递类别（快递产品、渠道）列表
    def get_emskind(self):
        command = 'ajxEmsQueryEmsKind'
        get_url = self.base_url + '?MfcISAPICommand=%s' % command
        r = requests.get(get_url)
        return r.json()

    # 运单号提取
    def get_no(self):
        command = 'EmsApiGetNo'
        get_url = self.base_url + '?MfcISAPICommand=%s&icid=%d&cemskind=%s&timestamp=%s&md5=%s' % (command, self.icid, )

