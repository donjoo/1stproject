from django.shortcuts import render,redirect,get_object_or_404
from app.models import Product,Variants,Coupon,ProductOffer,CategoryOffer,Stock
from .models import Cart,CartItem
from django.http import HttpResponse,JsonResponse
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.decorators import login_required
from userauth.models import Address
from userauth.models import User
from django.contrib import messages
from .forms import CouponForm
from django.utils import timezone
import datetime
from django.db.models import Max




current_date = datetime.date.today()


# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart 


def add_cart(request,pid):
    current_user = request.user
    print(current_user)
    product = Product.objects.get(pid=pid)
    if current_user.is_authenticated:
        
        product_size =[]
        if request.method == "POST":
            for item in request.POST:   
                key = item
                value = request.POST[key]
        

            try:
                
                sizess = Variants.objects.get(product=product,size__iexact=value)
                product_size.append(sizess)
                print(product_size,"hiiiierhtei")
                print('here')
            except:       
                pass
        for sizess in product_size:
            print(sizess)
        product_size_set = set([sizess.id for sizess in product_size])
        print( product_size_set,'set')
        is_cart_item_exists = CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,user = current_user)
            
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variations = item.variations.all()
                ex_var_list.append(list(existing_variations))
                id.append(item.id)
                print(list(id),'heyydyehyuhf') 
            ex_var_list = [set(item.variations.values_list('id', flat=True)) for item in cart_item]

            if  product_size_set in ex_var_list:
                index = ex_var_list.index(product_size_set)
                item_id = id[index]  
                item = CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                if product_size:  # Check if product_size is not empty
                    stock = Stock.objects.get(variant=product_size[0])              
                    if item.quantity <= stock.stock:
                        item.save()
                    else:
                            messages.error(request, "Sorry, the requested quantity is not available in stock.")
                            return redirect('cart:cart')
                else:
                    messages.error(request,"please select a size.")
                    return redirect('app:product_detail',product.pid)
            else:
                item = CartItem.objects.create(product=product,quantity=1,user=current_user)

                if len(product_size)> 0:
                    item.variations.clear()
                    print('hekllo')
                    item.variations.add(*product_size)                
                    item.save()
            
        else:
            
            cart_item = CartItem.objects.create(
                product = product,
                quantity =1,
                user = current_user,
            )
            if len(product_size)> 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_size)
            cart_item.save()
        
        
        return redirect('cart:cart')


    else:
        product_size =[]
        if request.method == "POST":
            for item in request.POST:
                key = item
                value = request.POST[key]
        

            try:
                
                sizess = Variants.objects.get(product=product,size__iexact=value)
                product_size.append(sizess)
                print(product_size,"hiiiierhtei")
                print('here')
            except:       
                pass

        
        try:
            cart =Cart.objects.get(cart_id = _cart_id(request))
            print('now')
            print('just')
        except Cart.DoesNotExist:
            cart = Cart.objects.create(
                cart_id = _cart_id(request)
            )
        cart.save()
    
        is_cart_item_exists = CartItem.objects.filter(product=product,cart=cart).exists()
        if is_cart_item_exists:
            cart_item = CartItem.objects.filter(product=product,cart=cart)
            
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variations = item.variations.all()
                ex_var_list.append(list(existing_variations))
                id.append(item.id)
            print(ex_var_list) 

            if  product_size in ex_var_list:
                index = ex_var_list.index(product_size)
                item_id = id[index]
                item = CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                item.save()
            else:
                item = CartItem.objects.create(product=product,quantity=1,cart=cart)

                if len(product_size)> 0:
                    item.variations.clear()
                    print('hekllo')
                    item.variations.add(*product_size)                
                    item.save()
        else:
            cart_item = CartItem.objects.create(
                product = product,
                quantity =1,
                cart = cart,
            )
            if len(product_size)> 0:
                cart_item.variations.clear()
                cart_item.variations.add(*product_size)
            cart_item.save()
        
        
        return redirect('cart:cart')
def get_product_offer(product):
    today = timezone.now().date()
    try:
        product_offer = ProductOffer.objects.filter(
            product=product,
            end_date__gte=today,
        )
        if product_offer.exists():
            max_discount = product_offer.aggregate(Max('discount'))['discount__max']
            return max_discount
        else:
            return 0
    except ProductOffer.DoesNotExist:
        return 0
def get_category_offer(category):
       today = timezone.now().date()
       try:
           category_offer = CategoryOffer.objects.filter(
               category= category,
               end_date__gte=today,
           )
           if category_offer.exists():
            max_discount = category_offer.aggregate(Max('discount'))['discount__max']
            return max_discount
           else:
             return 0
       except CategoryOffer.DoesNotExist:
           return 0

def apply_offer(cart_items, grand_total):
    applied_offer = None
    has_offer = False
    
    for cart_item in cart_items:
        product = cart_item.product
        category = product.category
        
        product_offer = get_product_offer(product)
        category_offer = get_category_offer(category)
        
        if product_offer and category_offer:
            offer = max(product_offer, category_offer)
        elif product_offer:
            offer = product_offer
        elif category_offer:
            offer = category_offer
        else:
            offer = 0
        offer = float(offer)
        if offer > 0:
            grand_total -= offer
            applied_offer = offer
            has_offer = True

    return grand_total, applied_offer


def cart(request, total=0,quantity=0,cart_items=None):
    try:
        shipping=0
        grand_total=0
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user,is_active=True)
        else:          
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart,is_active=True)
        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity

        shipping = (3 * total)/100
        grand_total = total + shipping
        grand_total,offer_price = apply_offer(cart_items, grand_total)
    except ObjectDoesNotExist:
        pass

    context = {
        'total':total,
        'quantity':quantity,
        'cart_items':cart_items,
        'shipping':shipping,
        'grand_total':grand_total,
        'offer_price':offer_price,
    }
    return render(request,'app/cart.html',context)



def remove_cart(request,pid,item_id):
    product = get_object_or_404(Product,pid=pid)
    try:
        if request.user.is_authenticated:
            cart_item=CartItem.objects.get(product=product,user=request.user,id=item_id)
        else:
            cart =Cart.objects.get(cart_id=_cart_id(request))
            cart_item = CartItem.objects.get(product=product,cart=cart,id=item_id)
        if cart_item.quantity > 1:
            cart_item.quantity -= 1
            cart_item.save()
        else: 
            cart_item.delete()
    except:
        pass
    return redirect('cart:cart')

def remove_cart_item(request,pid,item_id):
    product = get_object_or_404(Product,pid=pid)
    if request.user.is_authenticated:
            cart_item = CartItem.objects.get(product=product,user=request.user,id=item_id)
    else:
        cart = Cart.objects.get(cart_id=_cart_id(request))
        cart_item = CartItem.objects.get(product=product,cart=cart,id=item_id)
    cart_item.delete()
    return redirect('cart:cart')

def apply_coupon(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():          
            code = form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code=code) #valid_to__gte=timezone.now(), active=True)
                if coupon.valid_to < timezone.now() and coupon.active == True:
                    messages.error(request,"coupon expired.")
                    request.session['coupon_id'] = None
                else:
                    request.session['coupon_id'] = coupon.id

            except Coupon.DoesNotExist:
                messages.error(request,"no coupon esxistsssss.")
                request.session['coupon_id'] = None
        else:
            messages.error(request,"invalid.")
     
    return redirect('cart:Checkout')

def remove_coupon(request):
    if request.method == 'POST':
        coupon_id = request.POST.get('coupon_id')
        if coupon_id:
            # Remove the coupon from session or database
            del request.session['coupon_id']
            # Optionally, you may want to update other related data
            # For example, recalculating the order total without the coupon
            # And updating the cart or order accordingly
            # Optionally, you can display a success message
            messages.success(request, 'Coupon removed successfully.')
    return redirect('cart:Checkout')


def Checkout(request):
    shipping = 0
    grand_total = 0
    total = 0
    quantity = 0
    cart_items = None
    coupon_discount=None
    coupon_form = CouponForm(request.POST or None)
    coupon_id = request.session.get('coupon_id')

    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:          
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)

        for cart_item in cart_items:
            total += (cart_item.product.price * cart_item.quantity)
            quantity += cart_item.quantity
        

        shipping = (3 * total) / 100
        subtotal = total
        if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, valid_to__gte=timezone.now(), active=True)
                # import pdb
                # pdb.set_trace()
                subtotal =  (coupon.discount/ 100) * float(total)
                coupon_discount = coupon.discount
            except Coupon.DoesNotExist:
                pass
           
        try:
            address = Address.objects.filter(user=request.user)
                
        except Address.DoesNotExist:
            address='none'

       
        grand_total = subtotal + float(shipping)
        grand_total,offer_price = apply_offer(cart_items, grand_total)

    except ObjectDoesNotExist:
        pass
   
    context = {
        'total': total,
        'subtotal':subtotal,
        'quantity': quantity,
        'cart_items': cart_items,  
        'shipping': shipping,
        'grand_total': grand_total,
        'coupon_form': coupon_form,
        'address':address,
        'coupon_id':coupon_id,
        'coupon_discount':coupon_discount,
        'offer_price':offer_price,
    }

    if request.method == 'POST':
        print("helllooo\n\n\n\n\n\n\n")
        if coupon_form.is_valid():
            code = coupon_form.cleaned_data['code']
            try:
                coupon = Coupon.objects.get(code=code, valid_to__gte=timezone.now(), active=True)
                request.session['coupon_id'] = coupon.id
                return redirect('cart:Checkout')
            except Coupon.DoesNotExist:
                request.session['coupon_id'] = None
                messages.error(request, 'Invalid coupon code. Please try again.')
          
      

    return render(request, 'app/checkout.html', context)


# @login_required(login_url='userauth:login')
# def Checkout(request,total=0,quantity=0,cart_items=None):
#     shipping=0
#     grand_total=0
#     try:
#         if request.user.is_authenticated:
#             cart_items = CartItem.objects.filter(user=request.user,is_active=True)
#         else:          
#             cart = Cart.objects.get(cart_id=_cart_id(request))
#             cart_items = CartItem.objects.filter(cart=cart,is_active=True)
#         for cart_item in cart_items:
#             total += (cart_item.product.price * cart_item.quantity)
#             quantity += cart_item.quantity

#         shipping = (3 * total)/100
#         grand_total = total + shipping
#     except ObjectDoesNotExist:
#         pass
#     user = User.objects.all()
#     address = Address.objects.filter(user=request.user)
#     context = {
#         'total':total,
#         'quantity':quantity,
#         'cart_items':cart_items,  
#         'shipping':shipping,
#         'grand_total':grand_total,
#         'address':address,
#     }
#     return render(request,'app/checkout.html' ,context)


