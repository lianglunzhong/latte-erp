# coding: utf-8
import datetime
import hashlib

import requests
import xmltodict

from lib.utils import get_now, pp

class Eub(object):
    '''eub, sub, gub的区别就是账号不一样, 这里使用不同的label进行实例化的时候, 即不同的账号api'''
    # eub
    chenyiwei = {}
    chenyiwei['sender'] = u'''
    <name>chen yiwei</name>
    <postcode>210058</postcode>
    <phone></phone>
    <mobile>13218887792</mobile>
    <country>CN</country>
    <province>320000</province>
    <city>320100</city>
    <county>320113</county>
    <company>Nanjing Kuaiyue E-commence Co.LTD</company>
    <street>No 75 Longtan Logistics Base A No 1 Shugang Road Longtan Street Nanjing Economic Development Zone</street>
    <email>chen.yiwei@wxzeshang.com</email>
    '''
    chenyiwei['collect'] = u'''
    <name>陈义伟</name>
    <postcode>210058</postcode>
    <phone></phone>
    <mobile>13218887792</mobile>
    <country>CN</country>
    <province>320000</province>
    <city>320100</city>
    <county>320113</county>
    <company>南京快悦电子商务有限公司</company>
    <street>经济技术开发区龙潭街道疏港路1号龙潭物流基地A-75号</street>
    <email>chen.yiwei@wxzeshang.com</email>
    '''
    chenyiwei['head'] = {
        'version' : 'international_eub_us_1.1',
        'authenticate' : "njky2015_534c1dd191c733769723046d55a9f4f2",
    }

    # gub
    weishengbin = {}
    weishengbin['sender'] = u'''
    <name>wei shengbin</name>
    <postcode>510430</postcode>
    <phone></phone>
    <mobile></mobile>
    <country>CN</country>
    <province>440000</province>
    <city>440100</city>
    <county>440111</county>
    <company>Guangzhou Furen E-commerce Co.LTD</company>
    <street>Room A402 Suixin Creative Park Shicha Road  Baiyun District Guangzhou</street>
    <email>wei.shengbing@wxzeshang.com</email>
    '''
    weishengbin['collect'] = u'''
    <name>韦胜彬</name>
    <postcode>510430</postcode>
    <phone></phone>
    <mobile></mobile>
    <country>CN</country>
    <province>440000</province>
    <city>440100</city>
    <county>440111</county>
    <company>广州辅仁电子商务有限公司</company>
    <street>广州市白云区 石槎路穗新创意园 A402</street>
    <email>wei.shengbing@wxzeshang.com</email>
    '''
    weishengbin['head'] = {
        'version' : 'international_eub_us_1.1',
        'authenticate' : "wxzeshang_0817b228eb923e30bcb85e1a119cf22b",
    }

    # sub
    wenfenghe = {}
    wenfenghe['sender'] = u'''
    <name>WENFENG HE</name>
    <postcode>510000</postcode>
    <phone>18620185120</phone>
    <mobile>18620185120</mobile>
    <country>CN</country>
    <province>440000</province>
    <city>440100</city>
    <county>440111</county>
    <company>BONA</company>
    <street>{SGJ-ZL} 4#,NO.39 WEST YUNCHENG ROAD,GUANGZHOUSHI,GUANGDO NG BAIYUNQU GUANGZHOUSHI GUANGDONG</street>
    <email>523273144@qq.com</email>
    '''
    wenfenghe['collect'] = u'''
    <name>WENFENG HE</name>
    <postcode>510000</postcode>
    <phone>18620185120</phone>
    <mobile>18620185120</mobile>
    <country>CN</country>
    <province>440000</province>
    <city>440100</city>
    <county>440111</county>
    <company>BONA</company>
    <street>中国广东省广州市白云区 云城西路</street>
    <email>523273144@qq.com</email>
    '''
    wenfenghe['head'] = {
        'version' : 'international_eub_us_1.1',
        'authenticate' : "gzhay_81963d8d6ccb3741a18990b4a7039064",
    }


    account_list = {
        'eub': chenyiwei,
        'deub': chenyiwei,
        'gub': weishengbin,
        'sub': wenfenghe,
    }

    def __init__(self, name):
        account = self.account_list[name.lower()]
        self.head = account['head']
        self.sender = account['sender']
        self.collect = account['collect']
        self.base_url = 'http://shipping2.ems.com.cn'

    def get_order_data(self, package):
        packageitem  = package.set_to_logistics()
        
        receiver = u'''
        <name>{package.name}</name>
        <postcode>{package.shipping_zipcode}</postcode>
        <phone>{package.shipping_phone}</phone>
        <mobile></mobile>
        <country>{package.shipping_country.code}</country>
        <province>{package.shipping_state}</province>
        <city>{package.shipping_city}</city>
        <county></county>
        <street>{package.address}</street>
        '''.format(package=package)

        item_list = u'''
        <item>
        <count>{package.qty}</count>
        <origin>CN</origin>
        <cnname>{packageitem.cn_name}</cnname>
        <unit>11</unit>
        <weight>{package.weight}</weight>
        <delcarevalue>{package.custom_amount}</delcarevalue>
        <enname>{packageitem.name}</enname>
        <description></description>
        </item>
        '''.format(package=package, packageitem=packageitem)
        
        package_data = {
            "account": self,
            "package": package,
            "receiver": receiver,
            "items": item_list,
            "startdate": get_now(utc=True).isoformat()[:-6],
            "enddate": (get_now(utc=True) + datetime.timedelta(days=10)).isoformat()[:-6],
        }

        data = u'''<?xml version="1.0" encoding="UTF-8"?>
        <orders xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
          <order>
            <orderid>{package.id:1>4}</orderid>
            <operationtype>0</operationtype>
            <producttype>0</producttype>
            <customercode>njky2015</customercode>
            <vipcode></vipcode>
            <clcttype>1</clcttype>
            <pod>false</pod>
            <untread>Abandoned</untread>
            <volweight>0</volweight>
            <startdate>{startdate}</startdate>
            <enddate>{enddate}</enddate>
            <printcode>01</printcode>
            <sender>{account.sender}</sender>
            <receiver>{receiver}</receiver>
            <collect>{account.collect}</collect>
            <items>{items}</items>
            <remark></remark>
          </order>
        </orders>'''.format(**package_data)

        # 去掉xml文件中的-'&, 并用utf8格式进行编码
        data = data.replace("'", " ").replace("&", " ").encode('utf-8')
        return data

    # 上传订单, 获得运单号
    def order(self, package):
        # 运单信息接收 POST
        api_name = '/partner/api/public/p/order'
        url = self.base_url + api_name
        data = self.get_order_data(package)
        r = requests.post(url, data=data, headers=self.head, timeout=5)
        return xmltodict.parse(r.content)

    # 获取单个pdf--当面单错位的时候使用
    def get_single_pdf(self, mail_num):
        mm = hashlib.md5()
        mm.update(self.head['authenticate']+mail_num)
        md5auth = mm.hexdigest()
        return "http://labels.ems.com.cn/partner/api/public/p/static/label/download/{md5auth}/{mail_num}.pdf"\
                .format(md5auth=md5auth, mail_num=mail_num)

    # 根据美国的邮编, 获取对应的pick_code
    @staticmethod
    def get_pick_code(number):
        code = int(number[:3])
        if 0<code<69 or 74<code<78 or 80<code<87 or 90<code<99 or 105<code<109 or code==115 or 117<code<299:
            cha = "1F"
        elif code==103 or 110<code<114 or code==116:
            cha = "1P"
        elif 70<code<73 or code==79 or 88<code<89:
            cha = "1Q"
        elif 100<code<102 or code==104:
            cha = "1R"
        elif 400<code<433 or 437<code<439 or 450<code<459 or 470<code<471 or 475<code<477 or code==480 or 483<code<485 or 490<code<491 or 493<code<497 or 500<code<529 or code==533 or code==536 or code==540 or 546<code<548 or 550<code<609 or code==612 or 617<code<619 or code==621 or code==624 or code==632 or code==635 or 640<code<699 or 740<code<758 or 760<code<772 or 785<code<787 or 789<code<799:
            cha = "3F"
        elif 460<code<469 or 472<code<474 or 478<code<479:
            cha = "3P"
        elif 498<code<499 or 530<code<532 or 534<code<535 or 537<code<539 or 541<code<545 or code==549 or 610<code<611:
            cha = "3Q"
        elif code==759 or 773<code<778:
            cha = "3R"
        elif 613<code<616 or code==620 or 622<code<623 or 625<code<631 or 633<code<634 or 636<code<639:
            cha = "3U"
        elif 434<code<436 or 481<code<482 or 486<code<489 or code==492:
            cha = "3C"
        elif 779<code<784 or code==788:
            cha = "3D"
        elif 440<code<449:
            cha = "3H"
        elif 813<code<849 or code==854 or 856<code<858 or 861<code<862 or 864<code<899 or 906 or 909<code<918 or 926<code<939:
            cha = "4F"
        elif 900<code<905 or 907<code<908:
            cha = "4P"
        elif 850<code<853 or code==855 or 859<code<860 or code==863:
            cha = "4Q"
        elif 919<code<921:
            cha = "4R"
        elif 922<code<925:
            cha = "4U"
        elif code==942 or 950<code<953 or 956<code<979 or 986<code<999:
            cha = "2F"
        elif 980<code<985:
            cha = "2P"
        elif 800<code<812:
            cha = "2Q"
        elif 945<code<948:
            cha = "2R"
        elif 940<code<941 or 943<code<944 or code==949 or 954<code<955:
            cha = "2U"
        elif 300<code<320 or 322<code<326 or 334<code<339 or 341<code<346 or 348<code<399 or 700<code<739:
            cha = "5F"
        elif 330<code<333 or code==340:
            cha = "5P"
        elif code==321 or 327<code<329 or code==34:
            cha = "5Q"
        return cha


###############下面的api暂时没用, 后面会用requests进行重写#################
    #运单信息接收 POST
    receive_url = '/partner/api/public/p/order'

    #运单信息验证 POST
    verify_url = '/partner/api/public/p/validate'

    #运单信息取消 DELETE /partner/api/public/p/order/{mail_num}
    delete_url = '/partner/api/public/p/order'

    #运单信息查询 GET /partner/api/public/p/order/{mail_num}
    check_url = '/partner/api/public/p/order'

    #实时跟踪信息查询 GET /partner/api/public/p/track/query/{cn|en}/{mail_num}
    track_url = '/partner/api/public/p/track/query'

    #国际E邮宝费率计算 POST
    cost_url = '/partner/api/public/p/rate/epacket'

    #国内地址行政区划查询 GET
    province_url = '/partner/api/public/p/area/cn/province/list'
    city_url = '/partner/api/public/p/area/cn/city/list'  #/partner/api/public/p/area/cn/city/list/{省号}
    county_url = '/partner/api/public/p/area/cn/county/list' #/partner/api/public/p/area/cn/county/list/{城市号}

    #批量获取标签 POST
    label_url1 = '/partner/api/public/p/print/batch'

    #批量获取标签(增强版) POST
    label_url2 = '/partner/api/public/p/print/downloadLabels'


    # head = {
    #     'version' : 'international_eub_us_1.1',
    #     'authenticate' : "njky2015_534c1dd191c733769723046d55a9f4f2",
    # }

    def get_url(self, url):
        return self.base_url + url

    # 运单信息验证
    def verify_order(self, package, return_type=0):
        data = self.get_order_data(package)
        req = urllib2.Request(self.get_url(self.verify_url), data, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 运单信息查询
    def check_order(self, mail_num, return_type=0):
        req = urllib2.Request(self.get_url(self.check_url) + '/' + mail_num, None, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 运单信息取消
    def delete_order(self, mail_num, return_type=0):
        opener = urllib2.build_opener(urllib2.HTTPHandler)
        request = urllib2.Request(self.get_url(self.delete_url) + '/' + mail_num, None, self.head)
        request.get_method = lambda: 'DELETE'
        response = opener.open(request)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 实时跟踪信息查询
    def track_order(self, mail_num, return_type=0):
        real_url = self.get_url(self.track_url) + '/cn/' + mail_num
        req = urllib2.Request(real_url, None, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 国际E邮宝费率计算, 返回币种为人民币 weight单位: 克, prov:省份代码
    def get_cost(self, weight, recv_country, send_country, prov, return_type=0):
        data = '<?xml version="1.0" encoding="UTF-8"?>\
    <rate>\
    <operationtype>0</operationtype>\
    <weight>' + str(weight) + '</weight>\
    <recvcountry>' + str(recv_country) + '</recvcountry>\
    <sendcountry>' + str(send_country) + '</sendcountry>\
    <sdprov>' + str(prov) + '</sdprov>\
    </rate>'
        req = urllib2.Request(self.get_url(self.cost_url), data, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 获取省份，城市，区域代码
    def get_area_code(self, area, code=None, return_type=0):
        if area == 'province':
            real_url = self.get_url(self.province_url)
        elif area == 'city':
            real_url = self.get_url(self.city_url) + '/' + str(code)
        elif area == 'county':
            real_url = self.get_url(self.county_url) + '/' + str(code)
        req = urllib2.Request(real_url, None, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)

    # 批量获取标签
    def get_label(self, mail_nums, return_type=0):
        mail_list = ''
        for mail in mail_nums:
            mail_list += '<order><mailnum>' + mail + '</mailnum></order>'
        data = '<?xml version="1.0" encoding="UTF-8"?>\
        <orders xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">\
        ' + mail_list + '</orders>'
        req = urllib2.Request(self.get_url(self.label_url1), data, self.head)
        response = urllib2.urlopen(req)
        return_data = response.read()
        if return_type == 0:
            return return_data
        else:
            return xmltodict.parse(return_data)


