# -*- coding: utf-8 -*-
from django.http import HttpResponse
from order.models import *
from shipping.models import Package
from product.models import Item
from xlwt import *
import StringIO
import datetime
import random
def export_order_invoice(modeladmin, request, queryset):
    response = HttpResponse(content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment;filename=export_invoice.xls'
    wb = Workbook(encoding='utf-8')

    fnt_header = Font()
    fnt_header.name = 'Tahoma'
    fnt_header.height = 300
    fnt_header.bold = True
    fnt_content = Font()
    fnt_content.name = 'Arial'
    borders_header = Borders()
    borders_header.left = 0
    borders_header.right = 0
    borders_header.top = 0
    borders_header.bottom = 0
    borders_content = Borders()
    borders_content.left = 1
    borders_content.right = 1
    borders_content.top = 1
    borders_content.bottom = 1
    align = Alignment()
    align.horz = Alignment.HORZ_CENTER
    align.vert = Alignment.VERT_CENTER
    align.wrap = Alignment.NOT_WRAP_AT_RIGHT
    align_not = Alignment()

    for query in queryset:
        ws = wb.add_sheet(query.ordernum)
        style = XFStyle()
        style.font = fnt_header
        style.borders = borders_header
        style.alignment = align
        # header
        ws.write_merge(3, 4, 1, 1, 'Choies', style)
        ws.col(0).width = 4000
        ws.col(1).width = 6000
        ws.col(3).width = 3000
        ws.col(4).width = 6000
        ws.col(5).width = 4000

        style.font = fnt_content
        style.alignment = align_not

        date = datetime.datetime.now().strftime("%B %d,%Y")
        random_num = random.randint(10, 100)
        invoice_num = "%s%s" % (query.ordernum, random_num)
        ws.write(5, 4, "DATE:", style)
        ws.write(5, 5, date, style)
        ws.write(6, 4, "INVOICE:", style)
        ws.write(6, 5, invoice_num, style)

        # Bill to and Shipping to
        style.font = fnt_content
        style.alignment = align_not

        temp_billing_firstname = query.shipping_firstname if query.shipping_firstname else ""
        temp_billing_state = query.shipping_state if query.shipping_state else ""
        temp_billing_address = query.shipping_address if query.shipping_address else ""
        temp_billing_city = query.shipping_city if query.shipping_city else ""
        temp_billing_country = query.shipping_country.code if query.shipping_country else ""
        temp_billing_zipcode = query.shipping_zipcode if query.shipping_zipcode else ""

        temp_shipping_firstname = query.shipping_firstname if query.shipping_firstname else ""
        temp_shipping_state = query.shipping_state if query.shipping_state else ""
        temp_shipping_address = query.shipping_address if query.shipping_address else ""
        temp_shipping_city = query.shipping_city if query.shipping_city else ""
        temp_shipping_country = query.shipping_country.code if query.shipping_country else ""
        temp_shipping_zipcode = query.shipping_zipcode if query.shipping_zipcode else ""

        billingshipping_style = easyxf('align: wrap on')
        ws.write(8, 0, "Bill To:", style)
        ws.write(8, 1, temp_billing_firstname, style)
        ws.write(9, 1, temp_billing_address, billingshipping_style)
        ws.write(10, 1, temp_billing_city, style)
        ws.write(11, 1, temp_billing_state, style)
        ws.write(12, 1, temp_billing_country, style)
        ws.write(13, 1, temp_billing_zipcode, style)

        ws.write(8, 3, "Ship To:", style)
        ws.write(8, 4, temp_shipping_firstname, style)
        ws.write(9, 4, temp_shipping_address, billingshipping_style)
        ws.write(10, 4, temp_shipping_city, style)
        ws.write(11, 4, temp_shipping_state, style)
        ws.write(12, 4, temp_shipping_country, style)
        ws.write(13, 4, temp_shipping_zipcode, style)

        # content
        style.borders = borders_content
        style.alignment = align
        ws.write_merge(16, 16, 0, 1, "Tracking NO.", style)
        ws.write_merge(16, 16, 2, 3, "Ship Date", style)
        ws.write_merge(16, 16, 4, 5, "Ship Via", style)
        temp_packages = Package.objects.filter(order=query.id)
        cell_count = 17
        # 运费
        total_ship_price = query.amount_shipping
        for temp_package in temp_packages:
            temp_tracking_no = temp_package.tracking_no if temp_package.tracking_no else ""
            temp_shiptime = temp_package.ship_time.strftime("%Y-%m-%d %H:%M:%S") if temp_package.ship_time else ""
            temp_label = temp_package.shipping.label if temp_package.shipping else ""
            ws.write_merge(cell_count, cell_count, 0, 1, temp_tracking_no, style)
            ws.write_merge(cell_count, cell_count, 2, 3, temp_shiptime, style)
            ws.write_merge(cell_count, cell_count, 4, 5, temp_label, style)
            cell_count += 1
        ws.write_merge(cell_count, cell_count, 0, 5, "", style)
        cell_count += 1

        ws.write(cell_count, 0, "Product ID", style)
        ws.write_merge(cell_count, cell_count, 1, 2, "TDescription", style)
        ws.write(cell_count, 3, "Quantity", style)
        ws.write(cell_count, 4, "Unit Price", style)
        ws.write(cell_count, 5, "Line Total", style)
        cell_count += 1
        temp_orderitems = OrderItem.objects.filter(order=query.id)

        total_item_price = 0
        for temp_orderitem in temp_orderitems:
            ws.row(cell_count).height_mismatch = True
            ws.row(cell_count).height = 800
            temp_sku = temp_orderitem.sku
            temp_item_name = temp_orderitem.item.product.name
            #Item.objects.get(sku=temp_sku).name
            temp_description = temp_item_name
            temp_qty = temp_orderitem.qty
            temp_unit_price = temp_orderitem.price
            temp_dollar_unit_price = "$%s" % temp_unit_price
            temp_line_price = temp_qty*temp_unit_price
            temp_dollar_line_price = "$%s" % temp_line_price
            item_style = easyxf('align: wrap on, vert centre, horiz center')
            item_style.borders = borders_content
            ws.write(cell_count, 0, temp_sku, item_style)
            ws.write_merge(cell_count, cell_count, 1, 2, temp_description, item_style)
            ws.write(cell_count, 3, temp_qty, style)
            ws.write(cell_count, 4, temp_dollar_unit_price, style)
            ws.write(cell_count, 5, temp_dollar_line_price, style)
            total_item_price += temp_line_price
            cell_count += 1

        total_price = total_item_price + total_ship_price
        style.borders = borders_header
        style.alignment = align_not
        ws.write(cell_count, 4, "SUBTOTAL", style)
        style.alignment = align
        total_item_price = "$%s" % total_item_price
        ws.write(cell_count, 5, total_item_price, style)
        style.alignment = align_not
        cell_count += 1
        ws.write(cell_count, 4, "SHIPPING&HANDLING", style)
        style.alignment = align
        total_ship_price = "$%s" % total_ship_price
        ws.write(cell_count, 5, total_ship_price, style)
        style.alignment = align_not
        cell_count += 1
        ws.write(cell_count, 4, "TOTAL DUE", style)
        style.alignment = align
        total_price = "$%s" % total_price
        ws.write(cell_count, 5, total_price, style)
        cell_count += 2
        ws.write_merge(cell_count, cell_count, 0, 5, "THANK YOU FOR YOUR BUSINESS!", style)

    output = StringIO.StringIO()
    wb.save(output)
    output.seek(0)
    response.write(output.getvalue())

    return response