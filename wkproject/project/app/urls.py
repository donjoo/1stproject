from django.urls import path
from app import views


app_name = "app"

urlpatterns = [
    path('',views.index,name='index'),
    path('product_detail/<str:pid>/',views.product_detail,name='product_detail'),
    path('category/',views.category_list_view,name='category_list'),
    path("category/<cid>/",views.category_product_list,name='category_product_list'),
    path("Anime/<aid>/",views.Anime_product_list,name='Anime_product_list'),
    path("character/<lid>/",views.Character_product_list,name='Character_product_list'),
    path("add_address/",views.add_address,name='add_address'),
    path('search/',views.search_view,name='search'),
    path('filter/',views.filter,name='filter'),
    path('whishlist/',views.whishlist,name='wishlist'),
    path('add-to-wishlist/<str:pid>/',views.add_to_wishlist, name='add_to_wishlist'),
    path('remove-from-wishlist/<str:pid>/',views.remove_from_wishlist, name='remove_from_wishlist'),
   


   

]
