#coding:utf-8
import xmltodict
import requests
import re

import donghangconfig

class Donghang(object):
    '''简单的转化, 有时间是要重写的, 使用obj.order(package)'''

    """
        东航api
            获取面单数据方式：
                    第一步：获取运单号  fn->get_tracking_no
                    第二步：包裹信息和运单号绑定  fn->cancel_tracking_num_package_bidding
                    第三步：绑定成功则返回包裹和运单号相关信息  fn->get_single_plan_data(直接对外开放)
    """

    state_codes = {
            "ALABAMA": "AL",
            "ALASKA": "AK",
            "ARIZONA": "AZ",
            "ARKANSAS": "AR",
            "CALIFORNIA": "CA",
            "COLORADO": "CO",
            "CONNECTICUT": "CT",
            "DELAWARE": "DE",
            "FLORIDA": "FL",
            "GEORGIA": "GA",
            "HAWAII": "HI",
            "IDAHO": "ID",
            "ILLINOIS": "IL",
            "INDIANA": "IN",
            "IOWA": "IA",
            "KANSAS": "KS",
            "KENTUCKY": "KY",
            "LOUISIANA": "LA",
            "MAINE": "ME",
            "MARYLAND": "MD",
            "MASSACHUSETTS": "MA",
            "MICHIGAN": "MI",
            "MINNESOTA": "MN",
            "MISSISSIPPI": "MS",
            "MISSOURI": "MO",
            "MONTANA": "MT",
            "NEBRASKA": "NE",
            "NEVADA": "NV",
            "OHIO": "OH",
            "OKLAHOMA": "OK",
            "OREGON": "OR",
            "TENNESSEE":  "TN",
            "TEXAS": "TX",
            "UTAH": "UT",
            "VERMONT": "VT",
            "VIRGINIA": "VA",
            "WASHINGTON": "WA",
            "WISCONSIN": "WI",
            "WYOMING": "WY",
            "PENNSYLVANIA": "PA",
            "NEW JERSEY": "NJ",
            "NEW MEXICO": "NM",
            "NEW YORK": "NY",
            "NEW HAMPSHIRE": "NH",
            "NORTH CAROLINA": "NC",
            "NORTH DAKOTA": "ND",
            "RHODE ISLAND": "RL",
            "SOUTH CAROLINA": "SC",
            "SOUTH DAKOTA": "SD",
            "WEST VIRGINIA": "WV",
            "DISTRICT OF COLUMNIA": "DC",
    }


    def __init__(self):
        self.userid = "ZSKJGZ"
        self.userpassword = "ly186660"
        self.account = "ZSKJGZ"
        self.spider_header = {'User-Agent': "Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)"}
        self.xml = u'''<?xml version="1.0" encoding="utf-8" ?>
<xml>
<t_AgentBasicData_Inform>
  <AgentCode>{params[agentcode]}</AgentCode>
  <Boxid>{params[boxid]}</Boxid>
  <Weight>{params[weight]}</Weight>
  <h>{params[h]}</h>
  <w>{params[w]}</w>
  <l>{params[l]}</l>
  <Sender>{params[sender]}</Sender>
  <SenderPhone>{params[senderphone]}</SenderPhone>
  <SenderAddress>{params[senderaddress]}</SenderAddress>
  <SenderZip>{params[senderzip]}</SenderZip>
  <ShenFenId>{params[shenfenid]}</ShenFenId>
  <RecivePhone>{params[recivephone]}</RecivePhone>
  <ReciveEmail>{params[reciveemail]}</ReciveEmail>
  <ReciveName>{params[recivename]}</ReciveName>
  <ReciveAddress1>{params[reciveaddress1]}</ReciveAddress1>
  <ReciveAddress2></ReciveAddress2>
  <ReciveAddress3></ReciveAddress3>
  <City>{params[city]}</City>
  <State>{params[state]}</State>
  <Zip>{params[zipcode]}</Zip>
  <CountryCode>{params[countrycode]}</CountryCode>
  <comments>{params[comment]}</comments>
  <PackageValue>{params[packagevalue]}</PackageValue>
  <Type>{params[type]}</Type>
  <Servicetype></Servicetype>
</t_AgentBasicData_Inform>
<t_AgentOrder_inform>
  <Boxid>{params[boxid]}</Boxid>
  <OrderNumber>{params[package_id]}</OrderNumber>
  <Sku>{params[sku]}</Sku>
  <GoodsCname>{params[goodscname]}</GoodsCname>
  <GoodsEname>{params[goodsename]}</GoodsEname>
  <Qty>{params[qty]}</Qty>
  <Price>{params[price]}</Price>
  <Curr>{params[curr]}</Curr>
  <Unit>EA</Unit>
  <SendCountryCode>CHN</SendCountryCode>
  <GoodsUrl>{params[goodsurl]}</GoodsUrl>
  <Hscode></Hscode>
  <Component></Component>
</t_AgentOrder_inform>
</xml>
'''

    # 生成xml数据
    def generate_xml_data(self, package):
        package_id = package.id
        message = ""
        data = {}
        result = {}
        result['data'] = ''
        packageitem = package.set_to_logistics()
        if not packageitem:
            message += u"%s无法找到packageitem" % package_id
            result['message'] = message
            return result


        try:
            if package.shipping_country.code == 'US':
                state = package.shipping_state.upper()
                state_code = self.state_codes.get(state, state)
            else:
                state_code = package.shipping_state
        except:
            message += u"%s州名填写有误" % package_id
            result['message'] = message
            return result

        try:
            if package.shipping_country.code == 'AU':
                shipping_city = package.shipping_city.strip().upper()
                state_code = donghangconfig.city_code[shipping_city]
        except:
            message += u"%s城市名称填写有误" % package_id
            result['message'] = message
            return result

        data = {
            "agentcode": self.account,
            "weight": "",
            "h": "",
            "w": "",
            "l": "",
            "sender": u"韦胜彬",
            "senderphone": "",
            "senderaddress": u"广州市白云区 石槎路穗新创意园 A402",
            "senderzip": "",
            "shenfenid": "",
            "recivephone": package.shipping_phone,
            "reciveemail": "",
            "recivename": package.name,
            "reciveaddress1": u"%s" % package.address,
            "city": package.shipping_city,
            "state": state_code,
            "zipcode": package.shipping_zipcode,
            "countrycode": package.shipping_country.code,
            "comment": "",
            "packagevalue": package.custom_amount,
            "type": 1,
            "package_id": package_id,
            "sku": packageitem.item.sku,
            "goodscname": u"%s" % packageitem.cn_name,
            "goodsename": u"%s" % packageitem.name,
            "qty": package.qty,
            "price": package.price,
            "curr": "USD",
            "goodsurl": "",
        }
        result["data"] = data
        result["message"] = message
        return result

    # 获取面单数据
    def order(self, package):
        package_id = package.id
        post_xml_data = self.generate_xml_data(package)
        result = {}
        generate_status = False
        data = {}
        if post_xml_data["data"]:
            tracking_num = self.get_tracking_no()
            if tracking_num:
                bidding_info = self.tracking_num_package_bidding(post_xml_data["data"], tracking_num)
                if bidding_info['status']:
                    data["package_id"] = package_id
                    data["tracking_num"] = tracking_num
                    data["sender"] = post_xml_data["data"]["sender"]
                    data["senderaddress"] = post_xml_data["data"]["senderaddress"]
                    data["senderphone"] = post_xml_data["data"]["senderphone"]
                    data["recivename"] = post_xml_data["data"]["recivename"]
                    data["recivephone"] = post_xml_data["data"]["recivephone"]
                    data["reciveaddress1"] = post_xml_data["data"]["reciveaddress1"]
                    data["state"] = post_xml_data["data"]["state"]
                    data["city"] = post_xml_data["data"]["city"]
                    data["beginaddress"] = "CN"
                    data["endaddress"] = post_xml_data["data"]["countrycode"]
                    data["qty"] = post_xml_data["data"]["qty"]
                    data["goodsename"] = post_xml_data["data"]["goodsename"]
                    data["weight"] = post_xml_data["data"]["weight"]
                    generate_status = True
                    message = u"package_id=%s下单成功!" % package_id
                else:
                    message = u"package_id=%s下单失败, %s!" % (package_id, bidding_info['message'])
            else:
                message = u"package_id=%s获取运单号失败!" % package_id
        else:
            message = u"package_id=%s获取包裹信息失败!%s" % (package_id, post_xml_data["message"])
        result["data"] = data
        result["status"] = generate_status
        result["message"] = message
        return result

    # 撤销物流号与包裹信息绑定
    def cancel_tracking_num_package_bidding(self, package_id, tracking_num):
        post_xml_data = self.generate_xml_data(package_id)
        post_xml_data["boxid"] = tracking_num
        xml = self.xml.format(params=post_xml_data)
        url = "http://interface.eaemall.com:1610/agentrecivedata/agentdata.asmx/CancelClientData"
        post_data = {"Userid": self.userid, "UserPassword": self.userpassword, "Account": self.account, "str": xml}
        getdict = self.get_xml_to_dict(url, post_data)
        status = getdict["xml"]["result"]
        if status == "t":
            return True
        else:
            return False

    # 物流号与包裹信息绑定
    def tracking_num_package_bidding(self, post_xml_data, tracking_num):
        res = {}
        url = "http://interface.eaemall.com:1610/agentrecivedata/agentdata.asmx/ReciveClientData"
        post_xml_data["boxid"] = tracking_num
        xml = self.xml.format(params=post_xml_data)
        post_data = {"Userid": self.userid, "UserPassword": self.userpassword, "Account": self.account, "str": xml}
        getdict = self.get_xml_to_dict(url, post_data)
        status = getdict["xml"]["result"]
        if status == "t":
            res['status'] = True
        else:
            res['status'] = False
            res['message'] = getdict["xml"]["message"]
        return res

    # 获取运输货物运单号
    def get_tracking_no(self):
        url = "http://interface.eaemall.com:1610/agentrecivedata/agentdata.asmx/GetEaeAwbno"
        post_data = {"Userid": self.userid, "UserPassword": self.userpassword}
        getdict = self.get_xml_to_dict(url, post_data)
        if getdict["xml"]["result"] == "t":
            tracking_num = getdict["xml"]["boxid"]
        else:
            tracking_num = ""
        return tracking_num

    # 获取物流末端配送号码 返回dict
    def get_terminal_track_no(self, tracking_no):
        url = "http://interface.eaemall.com:1610/agentrecivedata/agentdata.asmx/GetTrackingNum"
        post_data = {"boxid": tracking_no}
        getdict = self.get_xml_to_dict(url, post_data)
        return getdict

    # 获取实时物流信息
    def track_order(self, tracking_no):
        url = "http://interface.eaemall.com:1610/eaewebservice/web.asmx/TrackNum"
        post_data = {"Userid": "EAE", "userpassword": "EAEXP2014", "Num": tracking_no}
        getdict = self.get_xml_to_dict(url, post_data)
        getdict = self.change_tracking_dict_more_beauty(getdict)
        return getdict

    # 请求url并返回dict
    def get_xml_to_dict(self, url, post_data):
        gethtml = requests.post(url, data=post_data, headers=self.spider_header)
        # print gethtml.content.decode("utf-8", "ignore").encode("gbk", "ignore")
        haveparsexml = self.parsexml(gethtml.text)
        getdict = self.xmltodict(haveparsexml)
        return getdict

    # 过滤xml
    def parsexml(self, xml):
        outputxml = re.sub('<\?xml.*?&lt;\?xml', "&lt;?xml", xml, flags=re.S)
        outputxml = re.sub("&lt;", "<", outputxml, flags=re.S)
        outputxml = re.sub("&gt;", ">", outputxml, flags=re.S)
        outputxml = re.sub("</string>", "", outputxml, flags=re.S)
        return outputxml

    # 将xml转成dict
    def xmltodict(self, xml):
        getdict = xmltodict.parse(xml)
        return getdict

    # change物流信息elegance dict
    def change_tracking_dict_more_beauty(self, getdict):
        data = []
        for temp_time, temp_context, temp_sto in zip(getdict["xml"]["time"], getdict["xml"]["context"], getdict["xml"]["sto"]):
            temp_data = {"time": temp_time, "context": temp_context, "sto": temp_sto}
            data.append(temp_data)
        return data


