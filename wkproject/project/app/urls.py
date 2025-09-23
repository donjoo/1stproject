from django.urls import path
from app import views


app_name = "app"

urlpatterns = [
    path('',views.index,name='index'),
    path('product_detail/<str:pid>/',views.product_detail,name='product_detail'),
    path("category/<cid>/",views.category_product_list,name='category_product_list'),
    path("Anime/<aid>/",views.Anime_product_list,name='Anime_product_list'),
    path("character/<lid>/",views.Character_product_list,name='Character_product_list'),
    path("add_address/",views.add_address,name='add_address'),
    path('search/',views.search_view,name='search'),
    path('filter_view/',views.filter_view,name='filter_view'),
    path('whishlist/',views.wishlist,name='wishlist'),
    path('add-to-wishlist/<str:pid>/',views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<str:pid>/',views.remove_from_wishlist, name='remove_from_wishlist'),
    path('shop/',views.shop,name="shop"),
    path('sort_by/',views.sort_by,name="sort_by"),
    path('get_sizes/<str:pid>/', views.get_sizes, name='get_sizes'),


       

]
