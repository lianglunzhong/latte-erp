from django.contrib import admin

from tongguan.models import *

class Product3baoAdmin(admin.ModelAdmin):

    save_as = True
    save_on_top = True
    search_fields = ['sku', 'choies_models']
    list_display = ('id', 'product', 'sku','hs_code','unit','f_model','status','cn_name','choies_models' )
    readonly_fields = ('product',)
    list_filter = ('status', )
admin.site.register(Product3bao, Product3baoAdmin)


class Package3baoAdmin(admin.ModelAdmin):

    save_as = True
    save_on_top = True
    #search_fields = ['key', 'sku']
    list_display = ('id', 'package', 'is_tonanjing','is_over','remark')
    readonly_fields = ('package', )
    list_filter = ('is_tonanjing', 'is_over')
admin.site.register(Package3bao, Package3baoAdmin)