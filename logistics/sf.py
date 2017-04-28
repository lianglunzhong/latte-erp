#coding:utf-8
import base64
import hashlib
import xmltodict
from suds.client import Client

class Sfworld(object):
    '''下单的api转化成功, 使用obj.order(package)'''

    '''
    可进行的操作有:
    分配运单号=>order
    订单发货确认=>operate_flag置为1则自动确认
    订单信息查询=>search
    路由查询=>route
    订单标签打印=>label
    '''

    clientCode = '0200023083'
    checkword = '53F82321AEFE59269F0546215F93233A'

    #错误代码
    err_dict = {'6101' : "请求数据缺少必选项",
                '6102' : "寄件方公司名称为空",
                '6103' : "寄方联系人为空",
                '6106' : "寄件方详细地址为空",
                '6107' : "到件方公司名称为空",
                '6108' : "到件方联系人为空",
                '6111' : "到件方地址为空",
                '6112' : "到件方国家不能为空",
                '6114' : "必须􏰂供客户订单号",
                '6115' : "到件方所属城市名称不能为空",
                '6116' : "到件方所在县/区不能为空",
                '6117' : "到件方详细地址不能为空",
                '6118' : "订单号不能为空",
                '6119' : "到件方联系电话不能为空",
                '6120' : "快递类型不能为空",
                '6121' : "寄件方联系电话不能为空",
                '6122' : "筛单类别不合法",
                '6123' : "运单号不能为空",
                '6124' : "付款方式不能为空",
                '6125' : "需生成电子运单,货物名称等不能为空",
                '6126' : "月结卡号不合法",
                '6127' : "增值服务名不能为空",
                '6128' : "增值服务名不合法",
                '6129' : "付款方式不正确",
                '6130' : "体积参数不合法",
                '6131' : "订单操作标识不合法",
                '6132' : "路由查询方式不合法",
                '6133' : "路由查询类别不合法",
                '6134' : "未传入筛单数据",
                '6135' : "未传入订单信息",
                '6136' : "未传入订单确认信息",
                '6137' : "未传入请求路由信息",
                '6138' : "代收货款金额传入错误",
                '6139' : "代收货款金额小于 0 错误",
                '6140' : "代收月结卡号不能为空",
                '6141' : "无效月结卡号,未配置代收货款上限",
                '6142' : "超过代收货款费用限制",
                '6143' : "是否自取件只能为 1 或 2",
                '6144' : "是否转寄件只能为 1 或 2",
                '6145' : "是否上门收款只能为 1 或 2",
                '6146' : "回单类型错误 ",
                '6150' : "订单不存在",
                '8000' : "报文参数不合法", 
                '8001' : "IP未授权", 
                '8002' : "服务(功能)未授权", 
                '8003' : "查询单号超过最大限制", 
                '8004' : "路由查询条数超限制", 
                '8005' : "查询次数超限制", 
                '8006' : "已下单,无法接收订单确认请求", 
                '8007' : "此订单已经确认,无法接收订单确认请求", 
                '8008' : "此订单人工筛单还未确认,无法接收订单确认请求", 
                '8009' : "此订单不可收派,无法接收订单确认请求。", 
                '8010' : "此订单未筛单,无法接收订单确认请求。", 
                '8011' : "不存在该接入编码与运单号绑定关系", 
                '8012' : "不存在该接入编码与订单号绑定关系", 
                '8013' : "未传入查询单号", 
                '8014' : "校验码错误", 
                '8015' : "未传入运单号信息", 
                '8016' : "重复下单", 
                '8017' : "订单号与运单号不匹配", 
                '8018' : "未获取到订单信息", 
                '8019' : "订单已确认", 
                '8020' : "不存在该订单跟运单绑定关系", 
                '8021' : "接入编码为空", 
                '8022' : "校验码为空", 
                '8023' : "服务名为空", 
                '8024' : "未下单", 
                '8025' : "未传入服务或不􏰂供该服务", 
                '8026' : "不存在的客户", 
                '8027' : "不存在的业务模板", 
                '8028' : "客户未配置此业务", 
                '8029' : "客户未配置默认模板", 
                '8030' : "未找到这个时间的合法模板", 
                '8031' : "数据错误,未找到模板", 
                '8032' : "数据错误,未找到业务配置", 
                '8033' : "数据错误,未找到业务属性", 
                '8034' : "重复注册人工筛单结果推送", 
                '8035' : "生成电子运单,必须存在运单号", 
                '8036' : "注册路由推送必须存在运单号", 
                '8037' : "已消单", 
                '8038' : "业务类型错误", 
                '8039' : "寄方地址错误", 
                '8040' : "到方地址错误", 
                '8041' : "寄件时间格式错误", 
                '8042' : "客户账号异常,请联系客服人员!", 
                '8043' : "该账号已被锁定,请联系客服人员!", 
                '8044' : "此订单已经处理中,无法接收订单修改请求", 
                '4001' : "系统发生数据错误或运行时异常", 
                '4002' : "报文解析错误", 
                '9000' : "身份验证失败", 
                '9001' : "客户订单号超过长度限制", 
                '9002' : "客户订单号存在重复", 
                '9003' : "客户订单号格式错误,只能包含数字和字母", 
                '9004' : "运输方式不能为空", 
                '9005' : "运输方式错误", 
                '9006' : "目的国家不能为空", 
                '9007' : "目的国家错误,请填写国家二字码", 
                '9008' : "收件人公司名超过长度限制", 
                '9009' : "收件人姓名不能为空", 
                '9010' : "收件人姓名超过长度限制", 
                '9011' : "收件人州或省超过长度限制", 
                '9012' : "收件人城市超过长度限制", 
                '9013' : "联系地址不能为空", 
                '9014' : "联系地址超过长度限制", 
                '9015' : "收件人手机号码超过长度限制", 
                '9016' : "收件人邮编超过长度限制", 
                '9017' : "收件人邮编只能是英文和数字", 
                '9018' : "重量数字格式不准确", 
                '9019' : "重量必须大于0", 
                '9020' : "重量超过长度限制", 
                '9021' : "是否退件填写错误,只能填写 Y 或 N", 
                '9022' : "海关申报信息不能为空", 
                '9023' : "英文申报品名不能为空", 
                '9024' : "英文申报品名超过长度限制", 
                '9025' : "英文申报品名只能为英文、数字、空格、()、 ()、,、,%", 
                '9026' : "申报价值必须大于 0", 
                '9027' : "申报价值必须为正数", 
                '9028' : "申报价值超过长度限制", 
                '9029' : "申报品数量必须为正整数", 
                '9030' : "申报品数量超过长度限制", 
                '9031' : "中文申报品名超过长度限制", 
                '9032' : "中文申报品名必须为中文", 
                '9033' : "海关货物编号超过长度限制", 
                '9034' : "海关货物编号只能为数字", 
                '9035' : "收件人手机号码格式不正确", 
                '9036' : "服务商单号或顺丰单号已用完,请联系客服人员", 
                '9037' : "寄件人姓名超过长度限制", 
                '9038' : "寄件人公司名超过长度限制", 
                '9039' : "寄件人省超过长度限制", 
                '9040' : "寄件人城市超过长度限制", 
                '9041' : "寄件人地址超过长度限制", 
                '9042' : "寄件人手机号码超过长度限制", 
                '9043' : "寄件人手机号码格式不准确", 
                '9044' : "寄件人邮编超过长度限制", 
                '9045' : "寄件人邮编只能是英文和数字", 
                '9046' : "不支持批量操作", 
                '9047' : "批量交易记录数超过限制", 
                '9048' : "此订单已确认,不能再操作", 
                '9049' : "此订单已收货,不能再操作", 
                '9050' : "此订单已出货,不能再操作", 
                '9051' : "此订单已取消,不能再操作", 
                '9052' : "收件人电话超过长度限制", 
                '9053' : "收件人电话格式不正确", 
                '9054' : "寄件人电话超过长度限制", 
                '9055' : "寄件人电话格式不正确", 
                '9056' : "货物件数必须为正整数", 
                '9057' : "货物件数超过长度限制", 
                '9058' : "寄件人国家错误,请填写国家二字码,默认为 CN", 
                '9059' : "货物单位超过长度限制,默认为 PCE", 
                '9060' : "货物单位重量格式不正确", 
                '9061' : "货物单位重量超过长度限制", 
                '9062' : "该运输方式暂时不支持此国家的派送,请选择其他派送方式", 
                '9063' : "当前运输方式暂时不支持该国家此邮编的派送,请选择其他派送方式!", 
                '9064' : "该运输方式必须输入邮编", 
                '9065' : "寄件人国家国家不能为空", 
                '9066' : "寄件人公司名不能为空", 
                '9067' : "寄件人公司名不能包含中文", 
                '9068' : "寄件人姓名不能为空", 
                '9069' : "寄件人姓名不能包含中文", 
                '9070' : "寄件人城市不能为空", 
                '9071' : "寄件人城市不能包含中文", 
                '9072' : "寄件人地址不能为空", 
                '9073' : "寄件人地址不能包含中文", 
                '9074' : "寄件人邮编不能为空", 
                '9075' : "寄件人邮编不能包含中文", 
                '9076' : "收件人公司名不能为空", 
                '9077' : "收件人公司名不能包含中文", 
                '9078' : "收件人城市不能为空", 
                '9079' : "收件人城市不能包含中文", 
                '9080' : "查询类别不正确,合法值为:1(运单号),2 (订单号)", 
                '9081' : "查询号不能不能为空。", 
                '9082' : "查询方法错误,合法值为:1(标准查询)", 
                '9083' : "查询号不能超过 10 个。注:多个单号,以逗号分隔。", 
                '9084' : "收件人电话不能为空", 
                '9085' : "收件人姓名不能包含中文", 
                '9086' : "英文申报品名必须为英文", 
                '9087' : "收件人手机不能包含中文", 
                '9088' : "收件人电话不能包含中文", 
                '9089' : "寄件人电话不能包含中文", 
                '9090' : "寄件人手机不能包含中文", 
                '9091' : "海关货物编号不能为空", 
                '9092' : "联系地址不能包含中文", 
                '9093' : "当总申报价值超过 75 欧元时【收件人邮箱】不能为空", 
                '9094' : "收件人邮箱超过长度限制", 
                '9095' : "收件人邮箱格式不正确", 
                '9096' : "寄件人省不能包含中文", 
                '9097' : "收件人州或省超不能包含中文", 
                '9098' : "收件人邮编不能包含中文", 
                '9099' : "英文申报品名根据服务商要求,申报品名包含 disc、speaker、power bank、battery、 magne 禁止运输,请选择其他运输方式!", 
                '9100' : "寄件人省不能为空", 
                '9101' : "收件人州或省不能为空", 
                '9102' : "收件人邮编只能为数字", 
                '9103' : "收件人邮编只能为 4 个字节", 
                '9104' : "【收件人邮编】,【收件人城市】,【州╲省】不匹配", 
                '9105' : "申报价值大于 200 美元时,【海关货物编号】不 能为空!", 
                '9106' : "收件人州或省不正确", 
                '9107' : "寄件人邮编只能包含数字", 
                '9108' : "收件人邮编格式不正确", 
                '9109' : "【州╲省】美国境外岛屿、区域不支持派送!", 
                '9110' : "【州╲省】APO/FPO 军事区域不支持派送!", 
                '9111' : "客户 EPR 不存在!", 
                '9112' : "【配货备注】长度超过限制!", 
                '9113' : "【配货名称】不能包含中文!", 
                '9114' : "【配货名称】长度超过限制!", 
                '9115' : "【包裹长(CM)】数字格式不正确!", 
                '9116' : "【包裹长(CM)】不能超过 4 位!", 
                '9117' : "【包裹长(CM)】必须大于 0!", 
                '9118' : "【包裹宽(CM)】数字格式不正确!", 
                '9119' : "【包裹宽(CM)】不能超过 4 位!", 
                '9120' : "【包裹宽(CM)】必须大于 0!", 
                '9121' : "【包裹高(CM)】数字格式不正确!", 
                '9122' : "【包裹高(CM)】不能超过 4 位!", 
                '9123' : "【包裹高(CM)】必须大于 0!", 
                '9124' : "【收件人身份证号/护照号】只能为数字和字母!", 
                '9125' : "【收件人身份证号/护照号】长度不能超过 18 个字符!", 
                '9126' : "【VAT 税号】只能为数字和字母!", 
                '9127' : "【VAT 税号】长度不能超过 20 个字符!", 
                '9128' : "【是否电池】填写错误,只能填写 Y 或 N!", 
                '9129' : '寄件人公司名不能包含,或"', 
                '9130' : '寄件人姓名不能包含,或"', 
                '9131' : '寄件人省不能包含,或"', 
                '9132' : '寄件人城市不能包含,或"', 
                '9133' : '寄件人地址不能包含,或"', 
                '9134' : '寄件人电话不能包含,或"', 
                '9135' : '寄件人手机号码不能包含,或"', 
                '9136' : '收件人公司名不能包含,或"', 
                '9137' : '收件人姓名不能包含,或"', 
                '9138' : '收件人城市不能包含,或"', 
                '9139' : '联系地址不能包含,或"', 
                '9140' : '收件人电话不能包含,或"', 
                '9141' : '收件人手机不能包含,或"', 
                '9142' : '英文申报品名不能包含,或"', }

    #定义加密算法
    def _encrypt_data(self, xml):
        #将xml数据和密钥进行连接
        content = xml + self.checkword
        content = content.encode('utf-8')
        #将获得的数据用md5加密并转化为大写
        md5_data = hashlib.md5(content).hexdigest().upper()
        #用base64对md5数据进行转码
        encrypt_data = base64.b64encode(md5_data)
        return encrypt_data

    def _call_service(self, xml):
        verify_code = self._encrypt_data(xml)
        # client = Client("http://120.24.60.8:8003/CBTA/ws/sfexpressService?wsdl")
        # client = Client("http://www.sfb2c.com:8003/CBTA/ws/sfexpressService?wsdl")
        # 顺丰的api更新
        client = Client("http://intl.sf-express.com/CBTA/ws/sfexpressService?wsdl")

        result = client.service.sfexpressService(xml, verify_code)#xml,verify_code)
        
        return xmltodict.parse(result)

    #定义各个功能
    #下单并获取运单号
    def order(self, package):
        result = {}

        '''处理shipping为SEB和NLR的package
        接收package对象
        调用SF的API下单并返回运单号'''
        #我们的产品只上传一件, 数量是package中的总数量, 重量是固定的0.3kg, 价格是custom_amount
        cargo = package.set_to_logistics()
        if not cargo:
            result['success'] = False
            result['msg'] = u'包裹中没有产品'
            return result

        cargo.price = package.price

        cargos_xml = u'''<Cargo ename="{cargo.name}"
        count="{package.qty}"
        unit="PCE"
        amount="{cargo.price}"
        diPickName="{cargo.name}"></Cargo>
        '''.format(cargo=cargo, package=package)

        if package.shipping.label == "SEB":
            package.express_type = 'B1'
        elif package.shipping.label == "NLR":
            package.express_type = "A1"
        else:
            result['success'] = False
            result['msg'] = u'包裹的shipping_label不是SEB或NLR'
            return result

        try:
            phone = package.shipping_phone.split('|')
            package.tel = phone[0]
            package.mobile = phone[-1]
        except Exception, e:
            package.tel = ''
            package.mobile = ''


        order_xml = u'''<Request service="OrderService" lang="zh-CN">
<Head>{self.clientCode}</Head>
    <Body>
        <Order orderid="{package.id}"
        express_type="{package.express_type}"
        j_company="广州辅仁电子商务有限公司"
        j_contact="wei shengbing"
        j_tel=""
        j_mobile=""
        j_address="广州市白云区 石槎路穗新创意园 A402"
        d_contact="{package.name}"
        d_tel="{package.tel}"
        d_mobile="{package.mobile}"
        operate_flag="1"
        d_address="{package.address}"
        parcel_quantity="1"
        j_province="广东省"
        j_city="广州市"
        d_province="{package.shipping_state}"
        d_city="{package.shipping_city}"
        j_country="CN"
        j_post_code=""
        d_country="{package.shipping_country.code}"
        d_post_code="{package.shipping_zipcode}"
        cargo_total_weight="0.3"
        returnsign="N">
            {cargos}
        </Order>
    </Body>
</Request>'''.format(self=self, package=package, cargos=cargos_xml)
        order_xml = order_xml.replace("&", " ")
        result = self._call_service(order_xml)
        res = {
            "success": False,
            "msg": '',
            "tracking_no": '',
        }
        if result['Response']['Head'] == 'ERR':
            err_code = result['Response']['ERROR']['@code'].split(',')
            res['msg'] = ','.join([Sfworld.err_dict.get(i, i) for i in err_code])
            return res
        elif result['Response']['Head'] == 'OK':
            res['status'] = True
            #服务商单号, 对应我们的运单号
            res['tracking_no'] = result['Response']['Body']['OrderResponse']['@agent_mailno']
            #顺丰单号, 顺丰用的
            res['sf_numbers'] = result['Response']['Body']['OrderResponse']['@mailno']
            #渠道转单号, SEB专用
            res['skybill_code'] = result['Response']['Body']['OrderResponse']['@skybill_code']
            return res

    #确认订单
    def confirm(self, package, dealtype):
        '''确认订单'''
        package = Package.objects.get(pk=package.id)
        confirm_xml = u'''<Request service=”OrderConfirmService” lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderConfirm orderid=”{package.id}” mailno="{package.tracking_no}” dealtype =”{dealtype}”> </OrderConfirm>
        </Body>
</Request>'''.format(clientCode=self.clientCode, package=package, dealtype=dealtype)
        return self._call_service(confirm_xml)

    #查询订单
    def search(self, package_id, search_type=1):
        '''search_type为1返回运单号, 为2返回所有数据'''
        search_xml = u'''<Request service="OrderSearchService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderSearch orderid="{package_id}" />
        </Body> 
</Request>'''.format(clientCode=self.clientCode, package_id=package_id)
        result = self._call_service(search_xml)
        if result['Response']['Head'] == 'ERR':
            err_code = result['Response']['ERROR']['@code']
            return False
        elif search_type == 1:
            trackcode = result['Response']['Body']['OrderSearchResponse']['@coservehawbcode']
            return trackcode
        elif search_type == 2:
            return result
        elif search_type == 3:
            res_response  = result['Response']['Body']['OrderSearchResponse']
            res = {}
            res['tracking_no'] = res_response['@coservehawbcode']
            res['sf_numbers'] = res_response['@mailno']
            res['skybill_code'] = res_response['@coskybillcode']
            return res
            

    #路由查询
    def route(self, package_id):
        '''限定只能使用package_id进行查询, tracking_type设置为2'''
        route_xml = '''<Request service="RouteService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <RouteRequest tracking_type="2" method_type="1" tracking_number="{package_id}" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_id=package_id)
        result = self._call_service(route_xml)
        route = []
        a = result['Response']['body']['RouteResponse']['Route']
        #解析route, 注意list或tule直接传递到页面上时, 中文会显示成utf-8的源码
        if type(a) != list:
            a = [a] 
        for i in a:
            route.append((i['@acceptTime'], i['@acceptAddress'].encode('utf-8'), i['@remark'].encode('utf-8') ))
        return route

    #打印标签
    def label(self, package_id_list):
        '''接收n个package_id, 返回pdf文件, 一次最多打印200个'''
        if type(package_id_list) != list or len(package_id_list) > 200:
            return False
        package_ids = ','.join([str(i) for i in package_id_list])
        print_xml = '''<Request service="OrderLabelPrintService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderLabelPrint orderid="{package_ids}" mailno="" dealtype="1" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_ids=package_ids)
        result = self._call_service(print_xml)
        return result

    #获取分拣码: 产品代码+分区代码+黄色标签标识
    @staticmethod
    def get_pick_code(package):
        pick_code = {}
        #SEB
        cou = package.shipping_country.code
        if package.shipping.label == "SEB":
            product_code = '2R'

            #1228号SEB版本
            #这些量大的国家分区代码为国家二字码
            if cou in ["FR", "ES", "DE", "GB", "NL", "HU", "SK", "IT", "IE", "CZ", "DK", "US", "IL", "CA", "UA", "SE", "AU", "BR", "BY", "CH", "NZ", "MX", "NO", "IN", "TR", "CL",]:
                zone_code = cou
            #这些国家是C区
            elif cou in ["LU", "BG", "HR", "CY", "EE", "LV", "MT", "RO", "AT", "BE", "FI", "GR", "LT", "PL", "PT", "AE", "AR", "ZA", "SA", "ID", "IS", "JP",]:
                zone_code = "C"
            #余下的为R区
            else:
                zone_code = 'R'

            #是否加*
            if cou in ["FR", "ES", "DE", "GB", "NL", "HU", "BE", "SK", "IT", "AT", "FI", "IE", "CZ", "DK", "GR", "PT", "LT", "PL", "LU", "BG", "HR", "CY", "EE", "LV", "MT", "RO",]:
                yellow_code = True
            else:
                yellow_code = False

        #NLR
        elif package.shipping.label == "NLR":
            product_code = '1P'

            zone_code = cou

            #这28个国家需要有黄色
            if cou in ['AT', 'LV', 'BE', 'LT', 'BG', 'LU', 'CY', 'MT', 'CZ', 'NL', 'DK', 'PL', 'EE', 'PT', 'FI', 'RO', 'FR', 'SK', 'DE', 'SI', 'GR', 'ES', 'HU', 'SE', 'IE', 'GB', 'IT', 'HR']:
                yellow_code = True
            else:
                yellow_code = False

        pick_code['product_code'] = product_code
        pick_code['zone_code'] = zone_code
        pick_code['yellow_code'] = yellow_code
        return pick_code

#     def bulk_route_service(self, package_ids):
#         request_xml = ''
#         for package_id in package_ids:
#             request_xml += '''<RouteRequtest tracking_type="2" method_type="1" tracking_number="{package_id}" />
# '''.format(package_id=package_id)
#         bulk_route_xml = '''<Request service="RouteService" lang="zh-CN">
#     <Head>{clientCode}</Head>
#         <Body>
#             {request_xml}
#         </Body>
# </Request>'''.format(clientCode=self.clientCode, request_xml=request_xml)
#         return self.call_service(bulk_search_xml)

class Sfhome(object):

    """
    可进行的操作有:
    分配运单号=>order
    订单发货确认=>operate_flag置为1则自动确认
    订单信息查询=>search
    路由查询=>route
    订单标签打印=>label
    顺丰BSP群号：314535266
    """

    # 港澳台地区代码
    d_deliverycodes = {
        "HK": 852,
        "MO": 853,
        "TW": 886
    }

    # 测试账号
    # clientCode = 'BSPdevelop'
    # checkword = 'j8DzkIFgmlomPt0aLuwU'
    # url = "http://bspoisp.sit.sf-express.com:11080/bsp-oisp/ws/sfexpressService?wsdl"

    # 联调账号
    # clientCode = "VSSAT"
    # checkword = "jDapBYM7Uxz1YqH3"
    # url = "http://bspoisp.sit.sf-express.com:11080/bsp-oisp/ws/sfexpressService?wsdl"

    # 生产环境账号
    clientCode = "0200253762"
    checkword = "1eVYXJ6eMq4HoTTJTJPBqAwdK567SI8g"
    url = "http://bsp-ois.sf-express.com/bsp-ois/ws/sfexpressService?wsdl"


    # 定义加密算法
    def _encrypt_data(self, xml):
        # 将xml数据和密钥进行连接
        content = xml + self.checkword
        content = content.encode('utf-8')

        # 将获得的数据用md5加密
        m = hashlib.md5()
        m.update(content)
        md5_data = m.digest()

        # 用base64对md5数据进行转码
        encrypt_data = base64.b64encode(md5_data)
        return encrypt_data

    def _call_service(self, xml):
        verify_code = self._encrypt_data(xml)
        client = Client(self.url)

        result = client.service.sfexpressService(xml, verify_code)
        return xmltodict.parse(result)

    # 下单并获取运单号
    def order(self, package):
        result = {}

        '''处理shipping为SEB和NLR的package
        接收package对象
        调用SF的API下单并返回运单号'''
        # 我们的产品只上传一件, 数量是package中的总数量, 重量是固定的0.3kg, 价格是custom_amount
        cargo = package.set_to_logistics()
        if not cargo:
            result['success'] = False
            result['msg'] = u'包裹中没有产品'
            return result

        cargo.price = package.price

        cargos_xml = u'''
        <Cargo name="{cargo.cn_name}"
        count="{package.qty}"
        unit="piece"
        weight="0.300"
        amount="{cargo.price}"
        currency="USD"
        source_area="CN"></Cargo>
        '''.format(cargo=cargo, package=package)

        package.express_type = "B1"

        try:
            phone = package.shipping_phone.split('|')
            package.tel = phone[0]
            package.mobile = phone[-1]
        except:
            package.tel = ''
            package.mobile = ''

        # 获取港澳台的delivery_code
        try:
            package.deliverycode = self.d_deliverycodes[package.shipping_country.code.upper()]
        except:
            result['success'] = False
            result['msg'] = u'国家错误'
            return result

        order_xml = u'''<Request service="OrderService" lang="zh-CN">
<Head>{self.clientCode}</Head>
    <Body>
        <Order 
        orderid="{package.id}"
        j_company="广州辅仁电子商务有限公司"
        j_contact="韦胜彬"
        j_tel="18512521182"
        j_province="广州省"
        j_city="广州市"
        j_country="CN"
        j_address="石槎路穗新创意园 A402"

        d_company="{package.name}"
        d_company="{package.name}"
        d_tel="{package.tel}"
        d_mobile="{package.mobile}"
        d_province="{package.shipping_state}"
        d_city="{package.shipping_city}"
        d_county="{package.shipping_country.code}"
        d_address="{package.address}"
        d_deliverycode='{package.deliverycode}'
        d_post_code="{package.shipping_zipcode}"

        express_type="1"
        pay_method="1"
        parcel_quantity="1"
        custid="{self.clientCode}"
        declared_value_currency="USD"
        cargo_total_weight="0.300"
        declared_value ="{package.custom_amount}"
        remark='{package.id}'>
            {cargos}
        </Order>
    </Body>
</Request>'''.format(self=self, package=package, cargos=cargos_xml)

        # 测试xml
#         order_xml = u'''<Request service="OrderService" lang="zh-CN">
# <Head>BSPdevelop</Head>
#     <Body>
#         <Order         orderid="72664"        j_company="广州辅仁电子商务有限公司"
#       j_contact="韦胜彬"        j_tel="18512521182"        j_province="广州省"
#   j_city="广州市"        j_country="CN"        j_address="石槎路穗新创意园 A402"
#         d_company="Kinga Kwiatkowska"        d_contact="Kinga Kwiatkowska"        d_tel="48722175944"        d_mobile="48722175944"        d_province="澳門"
#         d_city="黑沙環"        d_county="MO"        d_address="寰宇天下第四座47樓B"        d_deliverycode='853'        d_post_code=" 27-400"
#         express_type="1"        pay_method="1"        parcel_quantity="1"        custid="0200253762"        declared_value_currency="USD"        declared_value ="2"
#     remark=''>
#             <Cargo name="Round Sunglasses with Metal Ar"        count="1"        unit="piece"        weight="300.0"        amount="2.0"        currency="USD"        source_area="CN"></Cargo>
#         </Order>
#     </Body>
# </Request>
# '''
        order_xml = order_xml.replace("&", "")  # 去除特殊字符
        result = self._call_service(order_xml)
        res = {
            "success": False,
            "msg": '',
            "tracking_no": '',
        }
        if result['Response']['Head'] == 'ERR':
            err_code = result['Response']['ERROR']['@code'].split(',')
            res['msg'] = ','.join([SFWorldApi.err_dict.get(i, i) for i in err_code])
        elif result['Response']['Head'] == 'OK':
            res['success'] = True
            res['tracking_no'] = result['Response']['Body']['OrderResponse']['@mailno']
        return res

    #确认订单
    def confirm(self, package, dealtype):
        '''确认订单'''
        package = Package.objects.get(pk=package.id)
        confirm_xml = u'''<Request service="OrderConfirmService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderConfirm orderid="{package.id}" mailno="{package.tracking_no}" dealtype="{dealtype}"> </OrderConfirm>
        </Body>
</Request>'''.format(clientCode=self.clientCode, package=package, dealtype=dealtype)
        return self._call_service(confirm_xml)

    # 查询订单
    def search(self, package_id):
        # 返回的result_data
        result_data = {}
        result_data["status"] = 0
        result_data["trackcode"] = ""
        result_data["destcode"] = ""
        result_data["msg"] = ""
        search_xml = u'''<Request service="OrderSearchService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderSearch orderid="{package_id}" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_id=package_id)
        result = self._call_service(search_xml)
        if result['Response']['Head'] == 'ERR':
            result_data["msg"] = SFWorldApi.err_dict[result['Response']['ERROR']['@code']]
        elif result['Response']['Head'] == 'OK':
            result_data["status"] = 1
            result_data["trackcode"] = result['Response']['Body']['OrderResponse']['@mailno']
            result_data["destcode"] = result['Response']['Body']['OrderResponse']['@destcode']
        return result_data

    # 路由查询
    def route(self, tracking_no):
        '''限定只能使用tracking_no进行查询, tracking_type设置为1'''
        route_xml = '''<Request service="RouteService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <RouteRequest tracking_type="1" method_type="1" tracking_number="{tracking_no}" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, tracking_no=tracking_no)
        result = self._call_service(route_xml)
        route = []
        a = result['Response']['Body']['RouteResponse']['Route']
        #解析route, 注意list或tule直接传递到页面上时, 中文会显示成utf-8的源码
        if type(a) != list:
            a = [a] 
        for i in a:
            route.append((i['@accept_time'], i['@accept_address'].encode('utf-8'), i['@remark'].encode('utf-8') ))
        return route

    #打印标签
    def label(self, package_id_list):
        '''接收n个package_id, 返回pdf文件, 一次最多打印200个'''
        if type(package_id_list) != list or len(package_id_list) > 200:
            return False
        package_ids = ','.join([str(i) for i in package_id_list])
        print_xml = '''<Request service="OrderLabelPrintService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderLabelPrint orderid="{package_ids}" mailno="" dealtype="1" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_ids=package_ids)
        result = self._call_service(print_xml)
        return result

class Sfru(object):
    '''
    可进行的操作有:
    分配运单号=>order
    订单发货确认=>operate_flag置为1则自动确认
    订单信息查询=>search
    路由查询=>route
    订单标签打印=>label
    '''

    #测试帐号
    # clientCode = 'ELSNJKY'
    # checkword = 'PGMWUo7eJgAxdKDy'
    # url = 'http://bspoisp.sit.sf-express.com:11080/bsp-oisp/ws/sfexpressService?wsdl'
    #正式帐号
    clientCode = '0253759738'
    checkword = 'JbzjARc5VBWSXuinv89gqwml6SRm2RDQ'
    url = 'http://bsp-oisp.sf-express.com/bsp-oisp/ws/sfexpressService?wsdl'

    @staticmethod
    def get_pick_code(country_code):
        dict_pick_code = {
            "RU":'6-EE-RU-G',
            "LT":'8-EE-LT-G',
            "LV":'12-EE-LV-G',
            "EE":'10-EE-EE-G',
            "SE":'16-EE-SE-G',
            "NO":'18-EE-NO-G',
            "FI":'14-EE-FI-G',
            "BY":'20-EE-BY-G',
            "UA":'22-EE-UA-G',
            "PL":'24-EE-PL-G',
        }                       
        return dict_pick_code.get(country_code, '')


    #定义加密算法
    def _encrypt_data(self, xml):
        #将xml数据和密钥进行连接
        content = xml + self.checkword
        content = content.encode('utf-8')
        #将获得的数据用md5加密并转化为大写
        md5_data = hashlib.md5(content).digest()
        #用base64对md5数据进行转码
        encrypt_data = base64.b64encode(md5_data)
        return encrypt_data

    def _call_service(self, xml):
        verify_code = self._encrypt_data(xml)
        client = Client(self.url)
        result = client.service.sfexpressService(xml, verify_code)#xml,verify_code)
        
        return xmltodict.parse(result)

    #定义各个功能
    #下单并获取运单号
    def order(self, package):
        result = {}

        '''处理shipping为SEB和NLR的package
        接收package对象
        调用SF的API下单并返回运单号'''
        cargo = package.set_to_logistics()
        #我们的产品只上传一件, 数量是package中的总数量, 重量是固定的0.3kg, 价格是get_customs_amount
        if not cargo:
            result['success'] = False
            result['msg'] = u'包裹中没有产品'
            return result

        cargo.cargo_weight = round(0.3 / package.qty, 2)
        cargo.price = package.price

        cargos_xml = u'''
        <Cargo name="{cargo.name}"
        count="{package.qty}"
        unit="piece"
        amount="{cargo.price}"
        currency = "{package.order.currency}"
        weight="{cargo.cargo_weight}"
        source_area="China"></Cargo>'''.format(cargo=cargo, package=package)

        if package.shipping.label == "SFRU":
            package.express_type = 10
        else:
            result['success'] = False
            result['msg'] = u'包裹的shipping_label不是SFRU'
            return result

        dict_d_deliverycode = {"RU":"MOW", "LT":"VNO", "LV":"RIX", "EE":"TLL", "SE":"ARN", "NO":"OSL", "FI":"HEL", "BY":"MSQ", "UA":"KBP", "PL":"WAW", "US":"NY"}
        package.d_deliverycode = dict_d_deliverycode.get(package.shipping_country.code, '')
    
        order_xml = u'''<Request service="OrderService" lang="zh-CN">
<Head>{clientCode}</Head>
    <Body>
        <Order orderid="{package.id}"
        custid="{clientCode}"
        express_type="{package.express_type}"
        declared_value="{package.custom_amount}"
        declared_value_currency="{package.order.currency}"
        j_company="NANJING KUAIYUE E-COMMENCE CO.LTD"
        j_contact="chen yiwei"
        j_tel="13218887792"
        j_mobile="13218887792"
        j_address="No 75 Longtan Logistics Base A No 1 Shugang Road Longtan Street Nanjing Economic Development Zone"
        j_shippercode="025"
        d_company="{package.name}"
        d_contact="{package.name}"
        d_tel="{package.shipping_phone}"
        d_mobile="{package.shipping_phone}"
        pay_method="1"
        d_address="{package.address}"
        parcel_quantity="1"
        j_province="Jiangsu"
        j_city="Nanjing"
        j_county="Qixia District"
        d_province="{package.shipping_state}"
        d_city="{package.shipping_city}"
        j_country="CN"
        j_post_code="210058"
        d_country="{package.shipping_country.code}"
        d_deliverycode="{package.d_deliverycode}"
        d_post_code="{package.shipping_zipcode}"
        cargo_total_weight="0.3">
            {cargos}
        </Order>
    </Body>
</Request>'''.format(clientCode=self.clientCode, package=package, cargos=cargos_xml)
        order_xml = order_xml.replace("&", "")  # 去除特殊字符
        result = self._call_service(order_xml)

        res = {
            "success": False,
            "msg": '',
            "tracking_no": '',
        }
        if result['Response']['Head'] == 'ERR':
            err_code = result['Response']['ERROR']['@code'].split(',')
            res['msg'] = ','.join([Sfworld.err_dict.get(i, i) for i in err_code])
            return res
        elif result['Response']['Head'] == 'OK':
            res['success'] = True
            #服务商单号, 对应我们的运单号
            res['tracking_no'] = result['Response']['Body']['OrderResponse']['@agent_mailno']
            #顺丰单号, 顺丰用的
            res['sf_numbers'] = result['Response']['Body']['OrderResponse']['@mailno']
            return res

    #确认订单
    def confirm(self, package, dealtype):
        '''确认订单'''
        package = Package.objects.get(pk=package.id)
        confirm_xml = u'''<Request service=”OrderConfirmService” lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderConfirm orderid=”{package.id}” mailno="{package.tracking_no}” dealtype =”{dealtype}”> </OrderConfirm>
        </Body>
</Request>'''.format(clientCode=self.clientCode, package=package, dealtype=dealtype)
        return self._call_service(confirm_xml)

    #查询订单
    def search(self, package_id, search_type=1):
        '''search_type为1返回运单号, 为2返回所有数据'''
        search_xml = u'''<Request service="OrderSearchService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderSearch orderid="{package_id}" />
        </Body> 
</Request>'''.format(clientCode=self.clientCode, package_id=package_id)
        result = self._call_service(search_xml)
        if result['Response']['Head'] == 'ERR':
            err_code = result['Response']['ERROR']['@code']
            return False
        elif search_type == 1:
            trackcode = result['Response']['Body']['OrderSearchResponse']['@coservehawbcode']
            return trackcode
        elif search_type == 2:
            return result
            

    #路由查询
    def route(self, package_id):
        '''限定只能使用package_id进行查询, tracking_type设置为2'''
        route_xml = '''<Request service="RouteService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <RouteRequest tracking_type="2" method_type="1" tracking_number="{package_id}" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_id=package_id)
        result = self._call_service(route_xml)
        route = []
        #解析route, 注意list或tule直接传递到页面上时, 中文会显示成utf-8的源码
        for i in result['Response']['body']['RouteResponse']['Route']:
            route.append((i['@acceptTime'], i['@acceptAddress'].encode('utf-8'), i['@remark'].encode('utf-8') ))
        return route

    #打印标签
    def label(self, package_id_list):
        '''接收n个package_id, 返回pdf文件, 一次最多打印200个'''
        if type(package_id_list) != list or len(package_id_list) > 200:
            return False
        package_ids = ','.join([str(i) for i in package_id_list])
        print_xml = '''<Request service="OrderLabelPrintService" lang="zh-CN">
    <Head>{clientCode}</Head>
        <Body>
            <OrderLabelPrint orderid="{package_ids}" mailno="" dealtype="1" />
        </Body>
</Request>'''.format(clientCode=self.clientCode, package_ids=package_ids)
        result = self._call_service(print_xml)
        return result

