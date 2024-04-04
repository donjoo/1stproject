from .models import Cart,CartItem
from app.models import WishList
from .views import _cart_id

def counter(request):
    cart_count = 0
    if 'admin' in request.path:
        return {}
    else:
        try:
            cart = Cart.objects.filter(cart_id=_cart_id(request))
            if request.user.is_authenticated:
                cart_items = CartItem.objects.all().filter(user=request.user)
            else:
                cart_items = CartItem.objects.all().filter(cart=cart[:1])
            for cart_item in cart_items:
                cart_count += 1 #cart_item.quantity
        except Cart.DoesNotExist:
            cart_count = 0
    return dict(cart_count=cart_count)

def wishlist_counter(request):
    wishlist_count = 0
    if request.user.is_authenticated:
        wishlist_items = WishList.objects.filter(user=request.user)
        for wishlist in wishlist_items:
            wishlist_count += wishlist.products.count()
    print(wishlist_count)
    return {'wishlist_count': wishlist_count}
