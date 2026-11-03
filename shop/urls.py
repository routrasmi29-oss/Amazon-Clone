from django.urls import path
from django.conf import settings
from django.conf.urls.static import static
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('product/<int:id>/', views.product_detail, name='product_detail'),
    path('register/', views.register, name='register'),
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('add-to-cart/<int:id>/', views.add_to_cart, name='add_to_cart'),
    path('cart/', views.cart, name='cart'),
    path('increase/<int:id>/', views.increase_quantity, name='increase_quantity'),
    path('decrease/<int:id>/', views.decrease_quantity, name='decrease_quantity'),
    path('remove/<int:id>/', views.remove_from_cart, name='remove_from_cart'),
    path('checkout/', views.checkout, name='checkout'),
    path('payment-success/', views.payment_success, name='payment_success'),
    path('payment-failed/', views.payment_failed, name='payment_failed'),
    path('order-success/', views.order_success, name='order_success'),
    path('my-orders/', views.my_orders, name='my_orders'),
    path('order-details/<int:id>/', views.order_details, name='order_details'),
    path('return-order/<int:id>/', views.return_order, name='return_order'),
    path('pay-online/<int:order_id>/', views.pay_online, name='pay_online'),
    path('wishlist/', views.wishlist, name='wishlist'),
    path('add-to-wishlist/<int:id>/', views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-wishlist/<int:id>/', views.remove_from_wishlist, name='remove_from_wishlist'),
    path('add-review/<int:id>/', views.add_review, name='add_review'),
    path('buy/<int:id>/', views.buy_now, name='buy_now'),
    path('profile/', views.profile, name='profile'),
    path('cancel-order/<int:order_id>/', views.cancel_order, name='cancel_order'),
    path('invoice/<int:id>/', views.download_invoice, name='download_invoice'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('apply-coupon/', views.apply_coupon, name='apply_coupon'),
    path('admin-orders/', views.admin_orders, name='admin_orders'),
    path('update-order-status/<int:order_id>/', views.update_order_status, name='update_order_status'),
    path('admin-order-details/<int:order_id>/', views.admin_order_detail, name='admin_order_detail'),
    path('admin-products/', views.admin_products, name='admin_products'),
    path('admin-products/add/', views.add_product, name='add_product'),
    path('admin-products/edit/<int:product_id>/', views.edit_product, name='edit_product'),
    path('admin-products/delete/<int:product_id>/', views.delete_product, name='delete_product'),
    path('admin-return-requests/',views.admin_return_requests,name='admin_return_requests'),
    path('update-return-status/<int:return_id>/',views.update_return_status,name='update_return_status'),
    path('admin-return-detail/<int:return_id>/',views.admin_return_detail,name='admin_return_detail'),
    path('live-search/', views.live_search, name='live_search'),
]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)