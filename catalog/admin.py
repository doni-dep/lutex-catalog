from django.contrib import admin
from unfold.admin import ModelAdmin
from .models import (
    Category, Product, Wishlist, Cart, Order, OrderItem,
    Review, WholesaleRequest
)

@admin.register(Category)
class CategoryAdmin(ModelAdmin):
    list_display = ('name', 'slug')

@admin.register(Product)
class ProductAdmin(ModelAdmin):
    list_display = ('name', 'category', 'price', 'is_on_sale', 'is_bestseller')
    list_filter = ('category', 'is_on_sale', 'is_bestseller')
    search_fields = ('name',)
    fieldsets = (
        ('Основное', {'fields': ('category', 'name', 'description', 'price')}),
        ('Дополнительно', {'fields': ('is_on_sale', 'discount_price', 'is_bestseller', 'sizes')}),
    )

@admin.register(Wishlist)
class WishlistAdmin(ModelAdmin):
    list_display = ('user', 'product', 'added_at')

@admin.register(Cart)
class CartAdmin(ModelAdmin):
    list_display = ('user', 'product', 'quantity')

@admin.register(Order)
class OrderAdmin(ModelAdmin):
    list_display = ('id', 'user', 'created_at', 'status', 'total_price')
    list_filter = ('status',)
    search_fields = ('user__username', 'address', 'phone')

@admin.register(OrderItem)
class OrderItemAdmin(ModelAdmin):
    list_display = ('order', 'product', 'quantity', 'price')

@admin.register(Review)
class ReviewAdmin(ModelAdmin):
    list_display = ('product', 'name', 'rating', 'created_at')
    list_filter = ('rating',)

@admin.register(WholesaleRequest)
class WholesaleRequestAdmin(ModelAdmin):
    list_display = ('name', 'phone', 'created_at', 'consent')