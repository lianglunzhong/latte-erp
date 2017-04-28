def global_template_variables(request):
    data = {}
    # data['barcode128'] = "http://barcode.cnaidc.com/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGcode128&text="
    # data['gs1_128'] = "http://barcode.cnaidc.com/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGgs1128&text="

    # data['barcode128'] = "http://example.barcodebakery.com/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGcode128&text="
    # data['gs1_128'] = "http://example.barcodebakery.com/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGgs1128&text="
    
    data['barcode128'] = "http://barcode.wxzeshang.com:8008/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGcode128&text="
    data['gs1_128'] = "http://barcode.wxzeshang.com:8008/html/image.php?filetype=PNG&dpi=200&scale=2&rotation=0&font_family=0&font_size=8&thickness=30&start=C&code=BCGgs1128&text="
    return data