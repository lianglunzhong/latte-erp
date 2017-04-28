# coding:utf-8

def get_tracking_provider(label):
    #ws和wish的物流方式对应关系
    dict_shipping = {
         "SUB"    : "EPacket",
         "ARAMEX" : "ARAMEX",
         "KYD"    : "EPacket",
         "MU"     : "EPacket",
         "XRA"    : "RussianPost",
         "DGM"    : "DHL",
         "NLR"    : "SFExpress",
         "SGB"    : "SingaporePost",
         "SEB"    : "SFExpress",
         "EUB"    : "EPacket",
         "EMS"    : "EMS(China)",
         "HKPT"   : "HongKongPost",
         "SDHL"   : "DHL",
         "DHL"    : "DHL",
    }
    return dict_shipping.get(label, '')

    