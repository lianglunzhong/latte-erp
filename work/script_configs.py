# coding: utf-8


class ScriptTimings(object):
    script_name_list = ["do_package", "get_smt_order", ]

    # timgings是脚本的执行时间, dict格式为循环执行, list格式为指定不规则时间点
    script_dict = {
        "do_package"            : {'name'     : "do_package",
                                   'cn_name'  : u'打包',
                                   'timings'  : {"interval_hour": 1, "start_minute": 0, "start_hour": 1},
                                   'note'     : u'每个小时的半点开始', },
        "get_smt_order"         : {'name'     : "get_smt_order",
                                   'cn_name'  : u'抓取速卖通订单',
                                   'timings'  : {"interval_hour": 2, "start_minute": 30, "start_hour": 1},
                                   'note'     : u'每两个小时的半点开始', },

        "get_amazon_order"      : {'name'     : "get_amazon_order",
                                   'cn_name'  : u'抓取亚马逊订单',
                                   'timings'  : {"interval_hour": 2, "start_minute": 30, "start_hour": 1},
                                   'note'     : u'每两个小时的半点开始', },
        ########## 下面的是参考的设置 ##########
        "get_order"             : {'name'     : "get_order",
                                   'cn_name'  : u'抓取choies订单',
                                   'timings'  : {"interval_hour": 1, "start_minute": 40, "start_hour": 0},
                                   'note'     : u'每个小时的40分钟开始', },
        "possback_delivered"    : {'name'     : "possback_delivered",
                                   'cn_name'  : u'回传妥投信息 至choies',
                                   'timings'  : ["05:15", ],
                                   'note'     : u'每天早上5:15开始', },

        "possback_trackingno"   : {'name'     : "possback_trackingno",
                                   'cn_name'  : u'回传发货信息 至choies',
                                   'timings'  : ["12:15", "20:15", ],
                                   'note'     : u'每天12:15, 20:15开始', },

        "shipping_order"        : {'name'     : "shipping_order",
                                   'cn_name'  : u'自动物流商下单',
                                   'timings'  : {"interval_hour": 4, "start_minute": 10, "start_hour":0},
                                   'note'     : u"每4个小时的10分开始", },
    }
