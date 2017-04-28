# coding:utf-8
import base64
import requests
from lxml import etree
from hashlib import md5

class Feite(object):
    '''简单的转化, 有时间是要重写的, 使用instance.order(package)下单'''

    """
        注意事项：
            1,重复下单，并不会更新新的运单号，只会update原来包裹的信息
    """

    def __init__(self):

        # 常规设置
        self.encoding = "utf-8"
        self.HTTP_HEADERS = {'Content-Type': 'text/xml', 'charset': self.encoding}
        self.url = "http://flytexpress.com/WebSvc/OrderProcessSvc.asmx"

        # 初始化命名空间
        self.NSMAP_SOAP = "http://schemas.xmlsoap.org/soap/envelope/"
        self.NSMAP_XSI = "http://www.w3.org/2001/XMLSchema-instance"
        self.NSMAP_XSD = "http://www.w3.org/2001/XMLSchema"
        self.NSMAP = {"xsi": self.NSMAP_XSI, "xsd": self.NSMAP_XSD, "soap": self.NSMAP_SOAP}
        self.FT_NAMESPACE = "http://tempuri.org/"

        # 设置xml根和body节点(添加命名空间)
        self.xml_root = etree.Element("{%s}Envelope" % self.NSMAP_SOAP, nsmap=self.NSMAP,)
        self.xml_body = etree.SubElement(self.xml_root, "{%s}Body" % self.NSMAP_SOAP)
        self.req_xml = ""

        # 测试账号
        # self.user_id = "10002"
        # self.user_pwd = "888888"

        # 正式账号
        self.user_id = "19253"
        self.user_pwd = "186660"
        self.FT_SIGN_FLAG = "scb.logistics.choice"  # 平台签入标识，问他们开发要过来的

    # get xml need data
    def _getpackageinfo(self, package):
        package_id = package.id
        result = {}
        message = ""
        status = 0
        data = {}

        packageitem = package.set_to_logistics()
        if not packageitem:
            message += u"%s->不存在packageitem" % package_id
            result["message"] = message
            result["status"] = status
            result["data"] = data
            return result

        if not package.price:
            message += u"%s->计算产品单价出错" % package_id
            result["message"] = message
            result["status"] = status
            result["data"] = data
            return result

        data["CustomerId"] = self.user_id
        data["Sign"] = "%s##%s##%s" % (self.user_id, md5(self.user_pwd).hexdigest(), 1)
        data["SignFlag"] = self.FT_SIGN_FLAG
        data["Country"] = package.shipping_country.code
        data["PostType"] = "CNUPSBLUE"  # 目前我公司飞特采用的是蓝单特惠
        data["ReceiverName"] = package.name
        data["Address1"] = package.address
        data["Address2"] = ""
        data["State"] = package.shipping_state  # 不为空就行
        data["City"] = package.shipping_city
        data["Zip"] = package.shipping_zipcode
        data["Phone"] = package.shipping_phone
        data["Remark"] = str(package.id)  # 这里的备注填写什么
        data["Usps3DaysIsReg"] = "0"  # USPS3Days是否挂号或签名 0:否,1:是,2:签名,若没有，填0(否)
        data["CustomerOrderNo"] = str(package.id)  # 客户订单编号
        data["PackageInfo_PkgEnName"] = packageitem.name
        data["PackageInfo_PkgCnName"] = packageitem.cn_name  # 如果为空就默认为衣服
        data["PackageInfo_Num"] = package.qty
        data["PackageInfo_CurrencyType"] = "USD"
        data["PackageInfo_UnitPrice"] = str(package.price)
        data["PackageInfo_RealPrice"] = str(package.price)
        data["PackageInfo_ItemId"] = packageitem.item.sku
        data["PackageInfo_Freight"] = '0'

        status = 1
        result["message"] = message
        result["status"] = status
        result["data"] = data
        return result

    # 拼接xml信息
    def _get_req_xml(self, data):
        xml_root = etree.Element("OrderUp")
        etree.SubElement(xml_root, "CustomerId").text = data["CustomerId"]
        etree.SubElement(xml_root, "Sign").text = data["Sign"]
        etree.SubElement(xml_root, "SignFlag").text = data["SignFlag"]
        xml_orders = etree.SubElement(xml_root, "OrderList")
        xml_order = etree.SubElement(xml_orders, "OrderInfo")

        etree.SubElement(xml_order, "Country").text = data["Country"]
        etree.SubElement(xml_order, "PostType").text = data["PostType"]
        etree.SubElement(xml_order, "ReceiverName").text = data["ReceiverName"]
        etree.SubElement(xml_order, "Address1").text = data["Address1"]
        etree.SubElement(xml_order, "Address2").text = data["Address2"]
        etree.SubElement(xml_order, "State").text = data["State"]
        etree.SubElement(xml_order, "City").text = data["City"]
        etree.SubElement(xml_order, "Zip").text = data["Zip"]
        etree.SubElement(xml_order, "Phone").text = data["Phone"]
        etree.SubElement(xml_order, "Remark").text = data["Remark"]
        etree.SubElement(xml_order, "Usps3DaysIsReg").text = data["Usps3DaysIsReg"]
        etree.SubElement(xml_order, "CustomerOrderNo").text = data["CustomerOrderNo"]

        packages = etree.SubElement(xml_order, "PackageList")
        package = etree.SubElement(packages, "PackageInfo")

        etree.SubElement(package, "PkgEnName").text = data["PackageInfo_PkgEnName"]
        etree.SubElement(package, "PkgCnName").text = u"%s" % data["PackageInfo_PkgCnName"]
        etree.SubElement(package, "Num").text = str(data["PackageInfo_Num"])
        etree.SubElement(package, "CurrencyType").text = data["PackageInfo_CurrencyType"]
        etree.SubElement(package, "UnitPrice").text = data["PackageInfo_UnitPrice"]
        etree.SubElement(package, "RealPrice").text = data["PackageInfo_RealPrice"]
        etree.SubElement(package, "ItemId").text = data["PackageInfo_ItemId"]
        etree.SubElement(package, "Freight").text = data["PackageInfo_Freight"]

        xml_str = etree.tostring(xml_root, pretty_print=True, xml_declaration=True, encoding=self.encoding)
        self.req_xml_content = "%s" % base64.b64encode(xml_str)  # xml加密
        return self.req_xml_content

    # 设置上传订单命名空间
    def _set_upload_xml_wapper(self,):
        self.xml_body = etree.SubElement(self.xml_body, "Upload", nsmap={None: self.FT_NAMESPACE})
        self.xml_request = etree.SubElement(self.xml_body, "request")

    # 设置查询订单命名空间
    def _set_search_xml_wapper(self,):
        self.xml_query_trace_id = etree.SubElement(self.xml_body, "QueryTraceId", nsmap={None: self.FT_NAMESPACE})
        self.xml_request = etree.SubElement(self.xml_query_trace_id, "request")

    # cdata post_data to string
    def _cdata(self):
        self.xml_request.text = etree.CDATA(self.req_xml_content)
        result = etree.tostring(self.xml_root, pretty_print=True, xml_declaration=True, encoding=self.encoding)
        return result

    # 发送request 请求
    def _send_http_xml(self, data):
        req = requests.post(url=self.url, data=data, headers=self.HTTP_HEADERS)
        return req.content

    # 下单操作
    def order(self, package):
        result = {'success': False, 'tracking_no': '', 'msg':'', }
        xml_need_data = self._getpackageinfo(package)
        if xml_need_data["status"]:
            self._set_upload_xml_wapper()
            self._get_req_xml(xml_need_data["data"])
            data = self._cdata()
            req_content = self._send_http_xml(data)
            ft_rps = etree.fromstring(req_content).xpath('//ns:UploadResult', namespaces={'ns': self.FT_NAMESPACE})
            format_data = etree.fromstring(ft_rps[0].text.encode(self.encoding, 'ignore'))
            flag = format_data.xpath("Flag")[0].text
            if flag == "1":
                result['success'] = True
                result['tracking_no'] = format_data.xpath("//OrderId")[0].text
            else:
                result['msg'] += format_data.xpath("FailList//Reason")[0].text
        else:
            result['msg'] += xml_need_data["message"]
        return result

    # 设置订单号 设置发送信息
    def _set_order_id(self, order_id):
        self.req_xml_content = order_id

    # 查询订单
    def search(self, order_id):
        self._set_search_xml_wapper()
        self._set_order_id(order_id)
        data = self._cdata()
        req_content = self._send_http_xml(data)
        ft_rps = etree.fromstring(req_content).xpath('//ns:QueryTraceIdResult', namespaces={'ns': self.FT_NAMESPACE})
        data = etree.fromstring(ft_rps[0].text.encode(self.encoding, 'ignore'))

        flag = data.xpath("Flag")[0].text
        result = {}
        order_id = ""
        message = ""
        status = 1
        if flag == "1":
            try:
                order_id = data.xpath("//OrderId")[0].text
            except:
                message += u"%s查无此单" % order_id
                status = 0
        else:
            message += u"%s查询失败,请重新查询" % order_id
            status = 0

        result["status"] = status
        result["order_id"] = order_id
        result["message"] = message

        return result


