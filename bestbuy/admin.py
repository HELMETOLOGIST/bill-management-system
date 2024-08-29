from django.contrib import admin
from .models import Customer, Product, Order, OrderItem, Cart, Supplier, CustomerTransaction

class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'number', 'order_id', 'date')

class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'price')

class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_id', 'customer', 'date', 'total_amount']

class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price', 'tax', 'discount', 'total_amount')

class CartAdmin(admin.ModelAdmin):
    list_display = ('product', 'quantity', 'price', 'tax', 'discount', 'total_amount')

class SupplierAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'product_name', 'quantity', 'credit', 'debit', 'date_time')

class CustomerTransactionAdmin(admin.ModelAdmin):
    list_display = ('customer_name', 'phone_number', 'credit', 'debit', 'date_time')

admin.site.register(Customer, CustomerAdmin)
admin.site.register(Product, ProductAdmin)
admin.site.register(Order, OrderAdmin)
admin.site.register(OrderItem, OrderItemAdmin)
admin.site.register(Cart, CartAdmin)
admin.site.register(Supplier, SupplierAdmin)
admin.site.register(CustomerTransaction, CustomerTransactionAdmin)
