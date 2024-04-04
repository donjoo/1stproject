from django.urls import path
from . import views


app_name = 'cart'

urlpatterns = [
    path('cart/',views.cart,name='cart'),
    path('add_cart/<pid>/',views.add_cart,name='add_cart'),
    path('remove_cart/<pid>/<int:item_id>',views.remove_cart,name='remove_cart'),
    path('remove_cart_item/<pid>/<int:item_id>',views.remove_cart_item,name='remove_cart_item'),
    path('checkout/',views.Checkout,name='Checkout'),
    path('apply_coupon',views.apply_coupon,name='apply_coupon'),
    path('remove_coupon/', views.remove_coupon, name='remove_coupon'),



]
