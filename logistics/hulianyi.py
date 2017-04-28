#-*- coding: utf-8 -*-
from suds.client import Client

class Hulianyi(object):
    '''简单的转化, 有时间是要重写的, 使用obj.order(package)'''


    gettrancexml = u'''<getTransportWayList>
<userToken>{data[token]}</userToken>
</getTransportWayList>
    '''

    deleteOrder_xml = u'''<deleteOrder>
<userToken>{data[token]}</userToken>
<orderId>{data[orderId]}</orderId>
</deleteOrder>
    '''
    
    shipping_labels = {
        "MYB": "MY",
        "KYD": "RSGHPS",
        "HKPT": "HKPOSTTH",
        "DGM": "RDXBGHH",
        "XRA": "CNPOSTRUXB",
        "SGB": "XJPPOSTGH",
    }

    # 初始化
    def __init__(self):
        # self.token = "aa43e662e6ce42899657945348b2f38f" # TEST
        self.token = "f2bad3fefdc444d48b0324b47f68205c"
        self.url = "http://kd.szice.net:8086/xms/services/order?wsdl"

    def _get_package_info(self, package):
        package_id = package.id
        result = {}
        data = {}
        result["status"] = 0
        message = ""

        packageitem = package.set_to_logistics()
        if not packageitem:
            message += u"不存在packageitem"
            result["message"] = message
            return result
        try:
            shipping_label = package.shipping.label.upper()
            shipping_lable = self.shipping_labels[shipping_label]
        except:
            message += u"不存在此物流方式"
            result["message"] = message
            return result
        
        if not package.price:
            message += u"不存在此order"
            result["message"] = message
            return result

        data["package_id"] = package_id
        data["trackingNo"] = ""
        data["cargoCode"] = "W"
        data["transportWayCode"] = shipping_lable
        # data["transportWayCode"] = "RDXBGHH"
        data["goodsCategory"] = "O"
        data["goodsDescription"] = ""
        data["insured"] = "N"
        data["pieces"] = package.qty
        data["weight"] = 0.3
        data["originCountryCode"] = "CN"
        data["destinationCountryCode"] = package.shipping_country.code
        data["consigneeCompanyName"] = ""
        data["consigneeName"] = package.name
        data["consigneeTelephone"] = package.shipping_phone
        data["consigneeMobile"] = package.shipping_phone
        data["street"] = package.address
        data["city"] = package.shipping_city
        data["province"] = package.shipping_state
        data["consigneePostcode"] = package.shipping_zipcode
        data["shipperAddress"] = u"广州市白云区 石槎路穗新创意园 A402"
        data["shipperCompanyName"] = u"广州辅仁电子商务有限公司"
        data["shipperName"] = u"韦胜彬"
        data["shipperPostcode"] = ""
        data["shipperTelephone"] = ""
        data["shipperMobile"] = ""
        data["memo"] = ""
        data["declareItem_name"] = packageitem.name
        data["declareItem_cnName"] = packageitem.cn_name
        data["declareItem_pieces"] = package.qty
        data["declareItem_netWeight"] = round(0.3 / package.qty, 2)
        data["declareItem_unitPrice"] = package.price
        data["declareItem_productMemo"] = ""
        data["declareItem_customsNo"] = ""
        
        status = 1
        result["data"] = data
        result["status"] = status
        result["message"] = message

        return result

    # 下订单
    def order(self, package):
        package_id = package.id
        post_data = self._get_package_info(package)
        result = {'success': False, 'tracking_no': '', 'msg':'', }
        if post_data["status"]:
            client = Client(self.url)
            servicereq = client.factory.create('createOrderRequest')
            servicereq.orderNo = post_data["data"]["package_id"]
            servicereq.trackingNo = post_data["data"]["trackingNo"]
            servicereq.cargoCode = post_data["data"]["cargoCode"]
            servicereq.transportWayCode = post_data["data"]["transportWayCode"]
            servicereq.goodsCategory = post_data["data"]["goodsCategory"]
            servicereq.goodsDescription = post_data["data"]["goodsDescription"]
            servicereq.insured = post_data["data"]["insured"]
            servicereq.pieces = post_data["data"]["pieces"]
            servicereq.weight = post_data["data"]["weight"]
            servicereq.originCountryCode = post_data["data"]["originCountryCode"]
            servicereq.destinationCountryCode = post_data["data"]["destinationCountryCode"]
            servicereq.consigneeCompanyName = post_data["data"]["consigneeCompanyName"]
            servicereq.consigneeName = post_data["data"]["consigneeName"]
            servicereq.consigneeTelephone = post_data["data"]["consigneeTelephone"]
            servicereq.consigneeMobile = post_data["data"]["consigneeMobile"]
            servicereq.street = post_data["data"]["street"]
            servicereq.city = post_data["data"]["city"]
            servicereq.province = post_data["data"]["province"]
            servicereq.consigneePostcode = post_data["data"]["consigneePostcode"]
            servicereq.shipperAddress = post_data["data"]["shipperAddress"]
            servicereq.shipperCompanyName = post_data["data"]["shipperCompanyName"]
            servicereq.shipperName = post_data["data"]["shipperName"]
            servicereq.shipperPostcode = post_data["data"]["shipperPostcode"]
            servicereq.shipperTelephone = post_data["data"]["shipperTelephone"]
            servicereq.shipperMobile = post_data["data"]["shipperMobile"]
            servicereq.memo = post_data["data"]["memo"]
            servicereq.declareItems = [
                {
                    "name": post_data["data"]["declareItem_name"],
                    "cnName": post_data["data"]["declareItem_cnName"],
                    "pieces": post_data["data"]["declareItem_pieces"],
                    "netWeight": post_data["data"]["declareItem_netWeight"],
                    "unitPrice": post_data["data"]["declareItem_unitPrice"],
                    "productMemo": post_data["data"]["declareItem_productMemo"],
                    "customsNo": post_data["data"]["declareItem_customsNo"]
                }
            ]
            data = client.service.createAndAuditOrder(self.token, servicereq)
            if data["success"] == True and data["trackingNo"] != 'None':
                result["success"] = True
                result["order_id"] = data["id"]
                result["tracking_no"] = data["trackingNo"]
            else:
                result["msg"] += data["error"]["errorInfo"]
        result["msg"] += post_data["message"]
        return result

    # 传错误的订单重新下单 orderNo前面+X
    def re_order(self, package_id):
        post_data = self._get_package_info(package_id)
        result = {}
        if post_data["status"]:
            client = Client(self.url)
            servicereq = client.factory.create('createOrderRequest')
            servicereq.orderNo = 'X' + str(post_data["data"]["package_id"])
            servicereq.trackingNo = post_data["data"]["trackingNo"]
            servicereq.cargoCode = post_data["data"]["cargoCode"]
            servicereq.transportWayCode = post_data["data"]["transportWayCode"]
            servicereq.goodsCategory = post_data["data"]["goodsCategory"]
            servicereq.goodsDescription = post_data["data"]["goodsDescription"]
            servicereq.insured = post_data["data"]["insured"]
            servicereq.pieces = post_data["data"]["pieces"]
            servicereq.weight = post_data["data"]["weight"]
            servicereq.originCountryCode = post_data["data"]["originCountryCode"]
            servicereq.destinationCountryCode = post_data["data"]["destinationCountryCode"]
            servicereq.consigneeCompanyName = post_data["data"]["consigneeCompanyName"]
            servicereq.consigneeName = post_data["data"]["consigneeName"]
            servicereq.consigneeTelephone = post_data["data"]["consigneeTelephone"]
            servicereq.consigneeMobile = post_data["data"]["consigneeMobile"]
            servicereq.street = post_data["data"]["street"]
            servicereq.city = post_data["data"]["city"]
            servicereq.province = post_data["data"]["province"]
            servicereq.consigneePostcode = post_data["data"]["consigneePostcode"]
            servicereq.shipperAddress = post_data["data"]["shipperAddress"]
            servicereq.shipperCompanyName = post_data["data"]["shipperCompanyName"]
            servicereq.shipperName = post_data["data"]["shipperName"]
            servicereq.shipperPostcode = post_data["data"]["shipperPostcode"]
            servicereq.shipperTelephone = post_data["data"]["shipperTelephone"]
            servicereq.shipperMobile = post_data["data"]["shipperMobile"]
            servicereq.memo = post_data["data"]["memo"]
            servicereq.declareItems = [
                {
                    "name": post_data["data"]["declareItem_name"],
                    "cnName": post_data["data"]["declareItem_cnName"],
                    "pieces": post_data["data"]["declareItem_pieces"],
                    "netWeight": post_data["data"]["declareItem_netWeight"],
                    "unitPrice": post_data["data"]["declareItem_unitPrice"],
                    "productMemo": post_data["data"]["declareItem_productMemo"],
                    "customsNo": post_data["data"]["declareItem_customsNo"]
                }
            ]
            data = client.service.createAndAuditOrder(self.token, servicereq)
            if data["success"] == True:
                result["orderid"] = data["id"]
                result["trackingNo"] = data["trackingNo"]
                result["package_id"] = package_id
                result["success"] = data["success"]
                result["message"] = ""
            else:
                result["orderid"] = ""
                result["trackingNo"] = ""
                result["package_id"] = package_id
                result["success"] = False
                result["message"] = data["error"]["errorInfo"]
            result["message"] += post_data["message"]
            return result

    # 得到label地址
    """
        返回值：
            url:有值->成功
            url:控制->失败
    """
    def label(self, package_id):
        url = "http://kd.szice.net:8086/xms/client/order_online!print.action?" \
              "userToken=%s&orderNo=%s&autoPrint=1&" \
              "printSelect=3&pageSizeCode=6" % (self.token, package_id)
        return url

     # 传错误的订单重新获取标签
    def re_label(self, package_id):
        package_id = 'X' + str(package_id)
        url = "http://kd.szice.net:8086/xms/client/order_online!print.action?" \
              "userToken=%s&orderNo=%s&autoPrint=1&" \
              "printSelect=3&pageSizeCode=6" % (self.token, package_id)
        return url

    # 删除订单
    def deleteOrder(self):
        xml = self.deleteOrder_xml.format(data={"token": self.token, "orderId": int(2017917082)})
        client = Client(self.url)
        result = client.service.deleteOrder(self.token, xml)
        print result

    # 查询订单信息(兼路由功能)
    def search(self, package_id):
        client = Client(self.url)
        servicereq = client.factory.create('lookupOrderRequest')
        servicereq.orderId = ""
        servicereq.orderNo = package_id
        servicereq.trackingNo = ""
        result = client.service.lookupOrder(self.token, servicereq)
        return result

    # 获取所有物流方式
    def get_transportWayList(self):
        xml = self.gettrancexml.format(data={"token": self.token})
        client = Client(self.url)
        result = client.service.getTransportWayList(self.token, xml)
        print result

