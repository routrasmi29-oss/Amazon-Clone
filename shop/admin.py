from django.contrib import admin

from .models import (
    Product,
    Cart,
    Order,
    OrderItem,
    Wishlist,
    Review,
    Coupon,
    ReturnRequest,
)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "category",
        "price",
        "original_price",
        "discount",
        "stock",
    )

    list_filter = (
        "category",
    )

    search_fields = (
        "name",
    )


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "user",
        "full_name",
        "phone",
        "total_price",
        "payment_method",
        "payment_status",
        "order_status",
        "created_at",
    )

    list_editable = (
        "payment_status",
        "order_status",
    )

    list_filter = (
        "payment_status",
        "order_status",
        "payment_method",
        "created_at",
    )

    search_fields = (
        "id",
        "full_name",
        "phone",
        "user__username",
    )

    ordering = (
        "-created_at",
    )

    list_per_page = 20


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = (
        "order",
        "product",
        "quantity",
        "price",
    )


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product",
        "quantity",
    )


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product",
    )


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "product",
        "rating",
        "created_at",
    )

    list_filter = (
        "rating",
    )

    search_fields = (
        "user__username",
        "product__name",
    )


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = (
        "code",
        "discount_type",
        "discount",
        "minimum_amount",
        "expiry_date",
        "active",
    )

    list_filter = (
        "discount_type",
        "active",
    )

    search_fields = (
        "code",
    )

    list_editable = (
        "active",
    )

    ordering = (
        "-expiry_date",
    )


@admin.register(ReturnRequest)
class ReturnRequestAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "order",
        "reason",
        "status",
        "refund_amount",
        "created_at",
        "updated_at",
    )

    list_filter = (
        "status",
        "reason",
        "created_at",
    )

    search_fields = (
        "order__id",
        "order__user__username",
        "reason",
    )

    list_editable = (
        "status",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )