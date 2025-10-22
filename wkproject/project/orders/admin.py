from django.contrib import admin
from .models import Payment,Order,OrderProduct

# Register your models here.

@admin.register(OrderProduct)
class OrderProductAdmin(admin.ModelAdmin):
    list_display = ['product', 'order', 'user', 'quantity', 'product_price', 'item_status', 'created_at']
    list_filter = ['item_status', 'created_at', 'order__status']
    search_fields = ['product__title', 'order__order_number', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['item_status']

admin.site.register(Payment)
admin.site.register(Order)