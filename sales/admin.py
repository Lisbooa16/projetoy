# admin.py
from django.contrib import admin

from sales.form import SaleForm
from sales.models.sales_of_products import Product, SaleHistory, TypeProduct
from sales.models.stock import Stock


class StockInline(admin.StackedInline):
    model = Stock
    extra = 0
    min_num = 1
    max_num = 1
    can_delete = False
    fields = ("quantity", "cost_price")

@admin.register(TypeProduct)
class TypeProductAdmin(admin.ModelAdmin):
    list_display = ("type_product",)
    search_fields = ("type_product",)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "type_product", "get_stock_qty", "get_price")
    search_fields = ("name",)
    inlines = [StockInline]

    def get_stock_qty(self, obj):
        return obj.stock.quantity if hasattr(obj, "stock") else "-"
    get_stock_qty.short_description = "Qtd em estoque"

    def get_price(self, obj):
        latest_price = obj.prices.order_by("-updated_at").first()
        return f"R$ {latest_price.price}" if latest_price else "-"
    get_price.short_description = "Preço Atual"

@admin.register(SaleHistory)
class SaleHistoryAdmin(admin.ModelAdmin):
    form = SaleForm
    list_display = ("sales_by", "created_at")
    readonly_fields = ("created_at",)

