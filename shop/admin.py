from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Supplier, Product, ProductImage, Order


class ProductImageInline(admin.TabularInline):
    model  = ProductImage
    extra  = 3
    fields = ['url', 'order']


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Isabella Barcelona', {'fields': ('customer_number', 'phone', 'street', 'city', 'postal_code', 'country', 'role', 'is_verified', 'accepts_marketing')}),
    )
    list_display = ['email', 'first_name', 'last_name', 'role', 'is_verified']
    search_fields = ['email', 'first_name', 'last_name']


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ['name', 'country', 'avg_shipping_days', 'is_active']
    search_fields = ['name']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display  = ['sku', 'name_es', 'category', 'price', 'stock_qty', 'is_published']
    search_fields = ['sku', 'name_es']
    list_filter   = ['category', 'is_published', 'supplier']
    inlines       = [ProductImageInline]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ['order_number', 'user', 'status', 'total_amount', 'created_at']
    search_fields = ['order_number']
    list_filter = ['status', 'payment_method']