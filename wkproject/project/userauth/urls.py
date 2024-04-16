from django.urls import path
from userauth import views

app_name = 'userauth'

urlpatterns = [
    path('signup/',views.handel_signup,name='signup'),
    path('login/',views.handel_login,name='login'),
    path('logout/',views.logoutUser,name='logout'),
    path('sign-up/otp_verification',views.otp_verification,name="otp_verification"),
    path('login_otp/',views.login_otp,name ='login_otp'),
    path('login/otp_verification_login',views.otp_verification_login,name="otp_verification_login"),
    path('user_profile/',views.user_profile,name='user_profile'),
    path('profile_update/',views.profile_update,name='profile_update'),
    path('change_password/',views.change_password,name='change_password'),
    path('address_edit/<id>/',views.address_edit,name='address_edit'),
    path('delete_address/<id>/',views.delete_address,name='delete_address'),
    path('sample/',views.sample,name='sample'),
    path('my_order/<int:order_id>/',views.my_order,name='my_order'),
    path('cancel_order/<int:order_id>/',views.cancel_order,name='cancel_order'),
    path('return_order/<int:order_id>/',views.return_order,name='return_order'),

    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('new_password/',views.new_password,name='new_password'),

    path('wallet/',views.user_wallet,name='user_wallet'),
    path('orders_lists/',views.order_list,name='orders_lists'),
    # path('add_funds/',views.ad   d_funds,name='add_funds'),


]
