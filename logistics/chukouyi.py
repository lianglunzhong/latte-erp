# coding:utf-8

from suds.client import Client

class Chukouyi(object):
    '''简单的转化, 有时间是要重写的, 使用obj.order(package)'''

    def __init__(self):
        # test
        # self.Token = "887E99B5F89BB18BEA12B204B620D236"
        # self.UserKey = "wr5qjqh4gj"
        # self.GuestId = "guest"
        # self.Url = "http://demo.chukou1.cn/client/ws/v2.1/ck1.asmx?WSDL"

        # formal
        self.Token = "2691325A81659A0349B42DF1BAAC8298"
        self.UserKey = "45ihxuvisr"
        self.GuestId = "aegean@vip.sohu.net"
        self.Url = "http://yewu.chukou1.cn/client/ws/v2.1/ck1.asmx?WSDL"  # 正式环境V2接入点
        self.Url_v3 = "http://api.chukou1.cn/v3/system/tracking/get-tracking"  # 正式环境V3接入点

    # 快递类型
    def list_all_direct_express_service(self):
        url = "http://demo.chukou1.cn/v3/direct-express/misc/list-all-service"
        params = {"token": self.Token, "user_key": self.UserKey}
        getHtml = requests.get(url, params=params, timeout=30)
        getJson = getHtml.json()
        # 出口易我们采用(CRI, CUE)

    # 验证用户  没什么用
    def verifyUser(self):
        result = {}
        client = Client(self.Url)
        servicereq = client.factory.create('VerifyUserRequest')
        servicereq.Token = self.Token
        servicereq.UserKey = self.UserKey
        servicereq.UserID = self.GuestId
        data = client.service.VerifyUser(servicereq)
        if data.Ack == "Success":
            result["status"] = 1
        else:
            result["status"] = 0
        result["message"] = data.Message
        return result

    # 获取erp包裹信息
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


        productList_Weight = 300/package.qty
        if not package.price:
            message += u"%s->获取单价出错" % package_id
            result["message"] = message
            result["status"] = status
            result["data"] = data
            return result

        data["shipping"] = package.shipping.label
        data["Custom"] = package.id
        data["RefNo"] = package.id
        data["CheckRepeatRefNo"] = False  # False
        data["ShipToAddress_City"] = package.shipping_city
        data["ShipToAddress_Contact"] = package.name
        data["ShipToAddress_Country"] = package.shipping_country.code
        data["ShipToAddress_Email"] = package.email
        data["ShipToAddress_Phone"] = package.shipping_phone
        data["ShipToAddress_PostCode"] = package.shipping_zipcode
        data["ShipToAddress_Province"] = package.shipping_state
        data["ShipToAddress_Street1"] = package.address
        data["ShipToAddress_Street2"] = ""
        data["Packing_Length"] = "0"
        data["Packing_Width"] = "0"
        data["Packing_Height"] = "0"
        data["Weight"] = "0.3"
        data["Status"] = "Initial"
        data["TrackCode"] = ""
        data["Remark"] = package.id
        data["ProductList_CustomsTitleEN"] = package.name + packageitem.goodsename
        data["ProductList_DeclareValue"] = package.price
        data["ProductList_Quantity"] = package.qty
        data["ProductList_Weight"] = productList_Weight
        data["SendedStatus"] = "Initial"

        status = 1
        result["message"] = message
        result["status"] = status
        result["data"] = data

        return result

    # 下单发送
    def _ExpressAddPackageNew(self, packageinfo):

        result = {}
        result["status"] = 0
        result["data"] = {}
        result["data"]["message"] = packageinfo["message"]
        if packageinfo["status"]:
            client = Client(self.Url)
            servicereq = client.factory.create('ExpressAddPackageNewRequest')
            servicereq.Token = self.Token
            servicereq.UserKey = self.UserKey
            servicereq.OrderSign = ""
            servicereq.ExpressType = "UNKNOWN"
            servicereq.ExpressTypeNew = packageinfo["data"]["shipping"]
            servicereq.IsTracking = True
            servicereq.PickupType = 0
            servicereq.PackageDetail = {
                'Custom': packageinfo["data"]["Custom"],
                'CheckRepeatRefNo': packageinfo["data"]["CheckRepeatRefNo"],
                "RefNo": packageinfo["data"]["RefNo"],
                "ShipToAddress": {
                    'City': packageinfo["data"]["ShipToAddress_City"],
                    'Contact': packageinfo["data"]["ShipToAddress_Contact"],
                    'Country': packageinfo["data"]["ShipToAddress_Country"],
                    'Email': packageinfo["data"]["ShipToAddress_Email"],
                    'Phone': packageinfo["data"]["ShipToAddress_Phone"],
                    'PostCode': packageinfo["data"]["ShipToAddress_PostCode"],
                    'Province': packageinfo["data"]["ShipToAddress_Province"],
                    'Street1': packageinfo["data"]["ShipToAddress_Street1"],
                    'Street2': packageinfo["data"]["ShipToAddress_Street2"]
                },
                "Packing": {
                    "Length": packageinfo["data"]["Packing_Length"],
                    "Width": packageinfo["data"]["Packing_Length"],
                    "Height": packageinfo["data"]["Packing_Length"],
                },
                "Weight": packageinfo["data"]["Weight"],
                'Status': packageinfo["data"]["Status"],
                "TrackCode": packageinfo["data"]["TrackCode"],
                "Remark": packageinfo["data"]["Remark"],
                'ProductList': {
                    "ExpressProduct": [
                        {
                            "CustomsTitleEN": packageinfo["data"]["ProductList_CustomsTitleEN"],
                            "DeclareValue": packageinfo["data"]["ProductList_DeclareValue"],
                            "Quantity": packageinfo["data"]["ProductList_Quantity"],
                            "Weight": packageinfo["data"]["ProductList_Weight"],
                        }
                    ]
                },
                "SendedStatus": packageinfo["data"]["SendedStatus"],
            }
            expressAddPackageNew_Return = client.service.ExpressAddPackageNew(servicereq)
            result["data"]["message"] += expressAddPackageNew_Return["Message"]
            if expressAddPackageNew_Return["Ack"] == "Success":
                result["status"] = 1
                result["data"]["trackCode"] = expressAddPackageNew_Return["TrackCode"]  # 货物跟踪编号
                result["data"]["custom"] = expressAddPackageNew_Return["Custom"]  # 客户备注
                result["data"]["itemSign"] = expressAddPackageNew_Return["ItemSign"]  # 处理号
                result["data"]["orderSign"] = expressAddPackageNew_Return["OrderSign"]  # 订单号
        return result

    # 下单
    def order(self, package):
        result = {'success': False, 'tracking_no': '', 'msg':'', }

        packageinfo = self._getpackageinfo(package)
        ExpressAddPackageNew_Return = self._ExpressAddPackageNew(packageinfo)
        result["msg"] += ExpressAddPackageNew_Return["data"]["message"]

        if ExpressAddPackageNew_Return["status"]:
            ExpressCompleteOrder_Return = self._ExpressCompleteOrder(ExpressAddPackageNew_Return["data"]["orderSign"])
            result["msg"] += ExpressCompleteOrder_Return["message"]

            # 这里由于出口易不能即时获得包裹运单号，在这里search直到找到
            tracking_no = {}
            for x in xrange(100):
                tracking_no = self.search(package_id)
                break
            tracking_no_str = tracking_no.get("trackCode", "") or ""

            if ExpressCompleteOrder_Return["status"]:
                result["success"] = True
                result["tracking_no"] = tracking_no_str  # 这里由于出口易物流号本身也是从其他系统拿的，有时间差，所以就吧包裹处理号作为物流号进行跟踪
                result["custom"] = ExpressAddPackageNew_Return["data"]["custom"]  # 客户备注
                result["itemSign"] = ExpressAddPackageNew_Return["data"]["itemSign"]  # 包裹处理号
                result["orderSign"] = ExpressAddPackageNew_Return["data"]["orderSign"]  # 订单号
        return result

    # 订单提交审批或者删除
    def _ExpressCompleteOrder(self, order_sign):
        result = {}
        client = Client(self.Url)
        servicereq = client.factory.create('ExpressCompleteOrderRequest')
        servicereq.Token = self.Token
        servicereq.UserKey = self.UserKey
        servicereq.ActionType = "Submit"  # Submit or Cancel
        servicereq.OrderSign = order_sign
        data = client.service.ExpressCompleteOrder(servicereq)
        if data["Ack"] == "Success":
            result["status"] = 1
        else:
            result["status"] = 0
        result["message"] = data["Message"]
        return result

    # 获取物流号兼查询包裹信息
    def search(self, package_id):
        client = Client(self.Url)
        servicereq = client.factory.create('ExpressGetPackageRequest')
        servicereq.Token = self.Token
        servicereq.UserKey = self.UserKey
        servicereq.ItemSign = ""
        servicereq.Custom = ""
        servicereq.RefNo = package_id
        data = client.service.ExpressGetPackage(servicereq)
        result = {}
        if data["Ack"] == "Success":
            result["status"] = 1
            result["trackCode"] = data["PackageDetail"]["TrackCode"]
            result["ItemSign"] = data["PackageDetail"]["ItemSign"]
        else:
            result["status"] = 0
            result["trackCode"] = ""
            result["ItemSign"] = ""
        return result

    # 轨迹查询接口
    def get_tracking_by_track_no(self, trackCode):
        url = self.Url_v3
        postData = {
            "token": self.Token,
            "user_key": self.UserKey,
            "Track_no": trackCode,  # 包裹处理号或者跟踪号
        }
        response = requests.get(url, params=postData, timeout=30)
        return response.json()

    def get_tracking_by_package_sn(self, trackCode):
        url = self.Url_v3
        postData = {
            "token": self.Token,
            "user_key": self.UserKey,
            "Package_sn": trackCode,  # 包裹处理号或者跟踪号
        }
        response = requests.get(url, params=postData, timeout=30)
        return response.json()

    # 打印面单
    def print_label(self):
        url = "http://demo.chukou1.cn/v3/direct-express/package/print-label"
        postData = {
            "token": self.Token,
            "user_key": self.UserKey,
            "package_sn": "CRI151125TST000002",  # 包裹处理号或者跟踪号
            "format": "classic_label",
            "content": "address_costoms",
        }
        response = requests.post(url, postData)
        return response.content

    # 使用出口易 需确定国家对应格口号是否存在
    # 根据shipping_country获取出口易格口号
    @staticmethod
    def get_attice_number(countryCode):
        define_data = {'BD': '1', 'BE': '41', 'BF': '1', 'BG': '29', 'BA': '1', 'BB': '60', 'BM': '60', 'BN': '24', 'BO': '1',
         'BI': '1', 'BJ': '1', 'BT': '48', 'JM': '1', 'BW': '1', 'BR': '3 ', 'BS': '60', 'BY': '25', 'BZ': '60', 'RU': '68',
         'RW': '1', 'RS': '1', 'LT': '1', 'TM': '54', 'TJ': '54', 'RO': '1', 'TK': '12', 'GW': '1', 'GU': '16', 'GT': '66',
         'GR': '37', 'GQ': '1', 'GP': '5', 'JP': '10', 'GY': '1', 'GF': '5', 'GE': '1', 'GD': '60', 'GB': '4', 'GM': '1',
         'GL': '34', 'GI': '60', 'GH': '1', 'OM': '55', 'TN': '1', 'IL': '19', 'JO': '58', 'HT': '1', 'HU': '39', 'HN': '66',
         'AD': '5', 'PR': '17', 'PW': '16', 'PT': '40', 'PY': '33', 'PA': '1', 'PF': '14', 'PG': '1', 'PE': '1', 'PK': '57',
         'PH': '49', 'PL': '23', 'PM': '15', 'ZM': '1', 'EH': '1', 'EE': '28', 'EG': '1', 'ZA': '45', 'EC': '1', 'IT': '7',
         'AO': '60', 'ET': '1', 'ZW': '1', 'KY': '60', 'ES': '22', 'ER': '5', 'ME': '1', 'MD': '1', 'MG': '1', 'MA': '1',
         'MC': '5', 'UZ': '54', 'ML': '1', 'MN': '1', 'US': '17', 'MU': '46', 'MT': '1', 'MW': '45', 'MV': '24', 'MQ': '5',
         'MR': '1', 'UG': '1', 'MY': '53', 'MX': '43', 'MZ': '1', 'FR': '5', 'FI': '38', 'FJ': '52', 'FO': '34', 'NI': '66',
         'NL': '0', 'NO': '18', 'SO': '1', 'NC': '14', 'NE': '1', 'NG': '1', 'NZ': '12', 'NP': '1', 'NR': '14', 'NU': '12',
         'CK': '12', 'CH': '8', 'CO': '1', 'CM': '1', 'CL': '33', 'XC': '63', 'CA': '15', 'XF': '63', 'NA': '62', 'CZ': '36',
         'CY': '1', 'CX': '14', 'CR': '1', 'CU': '1', 'SZ': '60', 'KG': '54', 'KE': '1', 'SR': '1', 'KI': '14', 'KH': '1',
         'SV': '66', 'KM': '5', 'ST': '1', 'SK': '35', 'SI': '1', 'KW': '1', 'SN': '1', 'SM': '7', 'SL': '1', 'SC': '70',
         'KZ': '54', 'SA': '44', 'SG': '24', 'SE': '20', 'SD': '1', 'DO': '1', 'DM': '1', 'DJ': '1', 'DK': '34', 'DE': '6',
         'YE': '1', 'AT': '31', 'DZ': '1', 'MK': '8', 'UY': '1', 'YT': '5', 'LB': '1', 'LC': '60', 'TV': '14', 'TT': '1',
         'TR': '42', 'LK': '56', 'LI': '1', 'LV': '27', 'TO': '14', 'TL': '14', 'LU': '1', 'LR': '1', 'LS': '60', 'TH': '48',
         'TG': '1', 'TD': '1', 'VC': '60', 'AE': '55', 'VE': '1', 'AG': '60', 'AF': '57', 'IQ': '1', 'IS': '1', 'IR': '1',
         'AM': '1', 'AL': '1', 'VN': '51', 'AS': '17', 'AR': '21', 'AU': '14', 'VU': '14', 'AW': '0', 'IN': '1', 'IC': '22',
         'IE': '32', 'ID': '50', 'UA': '26', 'QA': '1', 'BH': '1'}
        if countryCode in define_data.keys():
            result = define_data[countryCode]
        else:
            result = ""
        return result

