from django.contrib import admin
from .models import Product, Customer

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'stock', 'price')
    search_fields = ('name',)

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'order_id', 'number', 'date', 'product')
    search_fields = ('name',)
