# coding: utf-8

# 独立执行的django脚本, 需要添加这四行
import sys, os, django
sys.path.append(os.getcwd())
os.environ['DJANGO_SETTINGS_MODULE'] = 'project.settings'
django.setup()

import time, datetime

from django.db import connection

from lib.models import Shipping


shipping_infos = [
    ("出口易- 中美专线", "CUE", "http://www.ec-firstclass.org/",),
    ("俄速递（专线快递）", "XRU", "http://www.xru.com/",),
    ("顺丰快递", "SF", "http://www.sf-express.com/cn/en/",),
    ("燕文快递", "YWS", "http://www.yw56.com.cn/english/index-en.asp",),
    ("飞特快递", "FGEX", "http://www.17track.net/index_en.shtml",),
    ("出口易-中邮小包", "CRI", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("泰嘉-香港小包", "HKPT", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("急速-DHL快递", "DHL", "http://track.js-exp.com/cgi-bin/GInfo.dll?DispInfo&w=js-exp&nid=3032",),
    ("急速-EMS快递", "EMS", "http://track.js-exp.com/cgi-bin/GInfo.dll?DispInfo&w=js-exp&nid=3032",),
    ("广东邮政-E邮宝小包", "EUB", "http://www.17track.net/en",),
    ("互联易-E特快", "ETK", "http://www.17track.net/en",),
    ("泰嘉-马来西亚小包", "MYB", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("顺丰-瑞典小包挂号", "SEB", "http://www.17track.net/en",),
    ("泰嘉-瑞士小包", "SWB", "http://www.17track.net/index_en.shtml",),
    ("货代-UPS快递", "UPS", "http://www.ups.com/content/cn/en/index.jsx",),
    ("泰嘉-新加坡小包", "SGB", "http://www.17track.net/en",),
    ("出口易-英国专线小包", "CET", "http://www.royalmail.com/",),
    ("FedEx-IP 礼服用", "FedEx", "http://www.fedex.com/us/track/",),
    ("顺丰-荷兰（欧洲）小包挂号", "NLR", "http://www.17track.net/en",),
    ("越邮宝挂号小包", "YUB", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("dhl小包", "DGM", "http://webtrack.dhlglobalmail.com/?trackingnumber&locale=en-US",),
    ("俄罗斯专线小包", "XRA", "http://www.17track.net/index_en.shtml",),
    ("东航美国线", "MU", "http://www.17track.net/en/",),
    ("俄罗斯平线", "CRU", "http://www.ec-firstclass.org/",),
    ("郑州小包", "KYD", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("巴西专线", "BMX", "http://www.17track.net/index_en.shtml",),
    ("TNT 快递", "TNT", "http://www.tnt.com/express/zh_cn/site/home.html",),
    ("ARAMEX快递", "ARAMEX", "http://track.js-exp.com/cgi-bin/GInfo.dll?DispInfo&w=js-exp&nid=3032",),
    ("南京中邮小包", "NXB", "http://www.17track.net/en/result/post-details.shtml?nums=",),
    ("全通DHL", "SDHL", "http://www.dhl.com/en.html",),
    ("顺丰欧洲专递", "FGJ", "http://www.17track.net/en/result/express-details-100012.shtml",),
    ("京广速运", "CRE", "http://www.szkke.com/",),
    ("广州E邮宝", "GUB", "http://www.17track.net/en",),
    ("百顺达美国专线", "CUB", "http://webtrack.dhlglobalmail.com/?locale=en-US",),
    ("顺丰中国", "SFZG", "https://i.sf-express.com/cn/sc/waybill/waybill_query.html",),
    ("广州EMS", "GZEMS", "http://www.17track.net/zh-cn/",),
    ("东航澳洲线", "MY", "http://www.eaexp.com/service/track.html",),
    ("马来西亚DHL", "MDHL", "http://www.dhl.com/en.html",),
    ("商盟E邮宝", "SUB", "http://www.17track.net/en",),
    ("互联易-香港E邮宝", "HKEUB", "http://www.17track.net/en",),
    ("FEDEX-IE经济型", "FEDEXIE", "http://www.fedex.com/us/track/",),
    ("NXB直邮", "DNXB", "http://www.17track.net/index_en.shtml",),
    ("EUB直邮", "DEUB", "http://www.17track.net/index_en.shtml",),
    ("俄罗斯顺丰国际", "SFRU", "http://www.17track.net/index_en.shtml",),
]

for name, label, link in shipping_infos:
    shipping = Shipping.objects.filter(label=label.upper()).first()
    if not shipping:
        Shipping.objects.create(name=name, label=label.upper(), link=link)
    else:
        shipping.name=name
        shipping.link=link
        shipping.save()
print "End"