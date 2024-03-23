from django.urls import path
from adminside import views

app_name ="adminside"

urlpatterns = [

    path('admin_index/',views.admin_index,name='admin_index'),
    path('admin_login/',views.admin_login,name='admin_login'),
    path('admin_logout/',views.admin_logout,name='admin_logout'),
    path('user_management/',views.user_management,name='user_management'),
    path('block_unblock/<int:user_id>/',views.block_unblock,name='block_unblock'),
    path('add_product/',views.add_product,name='add_product'),
    # path('add_variant/',views.add_variant,name='add_variant'),
    path('product_list/',views.product_list,name='product_list'),
    path('delete_product/<str:pid>/',views.delete_product,name='delete_product'),
    path('block_unblock_products/<str:pid>/',views.block_unblock_products,name='block_unblock_products'),
    path('category_list/',views.category_list,name='category_list'),
    # path('variant_list/',views.variant_list,name='variant_list'),
    path('category_edit/<str:cid>/',views.category_edit,name='category_edit'),
    path('add_category/',views.add_category,name='add_category'),
    path('new_html/',views.new,name='new'),
    path('available_category/<str:cid>/',views.available_category,name='available_category'),
    path('delete_category/<str:cid>/',views.delete_category,name='delete_category'),
    path('products_details/<str:pid>/',views.products_details,name='products_details'),
    path('product_edit/<str:pid>/',views.product_edit,name='product_edit'),
    path('add_newvariant/',views.add_newvariant,name='add_newvariant'),
    path('newvariant_list/',views.newvariant_list,name='newvariant_list'),
    path('block_size/<str:id>/',views.block_size,name='block_size'),
    path('delete_size/<str:id>/',views.delete_size,name='delete_size'),
    path('add_stock/', views.add_stock, name='add_stock'),
    path('get_variants/', views.get_variants, name='get_variants'),
    path('stock_list/', views.stock_list, name='stock_list'),





    path('add_animecat/',views.add_animecat,name='add_animecat'),
    path('animecat_list/',views.animecat_list,name='animecat_list'),
    path('animecat_edit/<str:aid>/',views.animecat_edit,name='animecat_edit'),
    path('available_animecat/<str:aid>/',views.available_animecat,name='available_animecat'),
    path('delete_animecat/<str:aid>/',views.delete_animecat,name='delete_animecat'),

    path('add_characters/',views.add_character,name='add_character'),
    path('characters_list/',views.character_list,name='character_list'),
    path('character_edit/<str:lid>/',views.character_edit,name='character_edit'),
    path('available_characters/<str:lid>/',views.available_characters,name='available_characters'),
    path('delete_character/<str:lid>/',views.delete_character,name='delete_character'),


    path('order_list/', views.order_list, name='order_list'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/update_status/', views.update_order_status, name='update_order_status'),



    path('create_coupon/',views.create_coupon,name='create_coupon'),
    path('coupon_list',views.coupon_list,name='coupon_list'),

    path('sales_report/',views.sales_report,name='sales_report'),
       



    
]
