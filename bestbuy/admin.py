from django.contrib import admin
from .models import Customer, Product, Order, OrderItem

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'order_id', 'date')  # Ensure these fields exist on Customer model

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'price')

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'date', 'total_amount']  # Adjusted to match the Order model fields

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'tax', 'discount', 'total_amount')  # Updated 'product_name' to 'product'

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
