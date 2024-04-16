from django.urls import path
from . import views


app_name = 'orders'

urlpatterns = [
    path('place_order/',views.place_order,name='place_order'),
    path('payment/',views.payment,name='payment'),
    path('order_complete',views.order_complete,name='order_complete'),
    path('payment_type/<str:payment>',views.payment_type,name='payment_type'),
    path('wallet_payment/<order_id>',views.wallet_payment,name='wallet_payment'),
    path('cod_payment/<order_id>',views.cod_payment,name='cod_payment'),
    path('payment_pending/<order_id>',views.payment_pending,name='payment_pending'),
    # path('download_invoice/',views.download_invoice_pdf,name='download_invoice_pdf'),
]
