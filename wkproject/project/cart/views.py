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
from decimal import Decimal



current_date = datetime.date.today()

 
# Create your views here.

def _cart_id(request):
    cart = request.session.session_key
    if not cart:
        cart = request.session.create()
    return cart 


def add_cart(request,pid):
    current_user = request.user
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
            except:       
                pass
        product_size_set = set([sizess.id for sizess in product_size])
        is_cart_item_exists = CartItem.objects.filter(product=product,user=current_user).exists()
        if is_cart_item_exists:        
            cart_item = CartItem.objects.filter(product=product,user = current_user)
            
            ex_var_list = []
            id = []
            for item in cart_item:
                existing_variations = item.variations.all()
                ex_var_list.append(list(existing_variations))
                id.append(item.id)
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
                        response_data = {
                                        'status': 'error',
                                        'message': f"Insufficient stock. Only available."
                                    }
                        return JsonResponse(response_data)  
                else:
                    response_data = {
                                        'status': 'error',
                                        'message': f"please select a size."
                                    }
                    return JsonResponse(response_data) 
            else:
                item = CartItem.objects.create(product=product,quantity=1,user=current_user)

                if len(product_size)> 0:
                    item.variations.clear()
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
        
        
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':

            return JsonResponse({"success": True})
        else:
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
            except:       
                pass

        
        try:
            cart =Cart.objects.get(cart_id = _cart_id(request))
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

            if  product_size in ex_var_list:
                index = ex_var_list.index(product_size)
                item_id = id[index]
                item = CartItem.objects.get(product=product,id=item_id)
                item.quantity += 1
                if product_size:  # Check if product_size is not empty
                    stock = Stock.objects.get(variant=product_size[0])              
                    if item.quantity <= stock.stock:
                        item.save()
                    else: 
                        response_data = {
                                        'status': 'error',
                                        'message': f"Insufficient stock. Only available."
                                    }
                        return JsonResponse(response_data) 
                item.save()
            else:
                item = CartItem.objects.create(product=product,quantity=1,cart=cart)

                if len(product_size)> 0:
                    item.variations.clear()
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

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({"success": True})
        else:
            return redirect('cart:cart')
def get_product_offer(product):
    """Return the highest valid active product offer discount for a given product."""
    today = timezone.now().date()
    
    product_offer = (
        ProductOffer.objects.filter(
            product=product,
            active=True,        # ✅ Only active offers
            delete=False,       # ✅ Not deleted
            start_date__lte=today,  # ✅ Offer already started
            end_date__gte=today,    # ✅ Offer still valid
        )
        .aggregate(max_discount=Max('discount'))
    )

    return product_offer['max_discount'] or 0
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
        
        quantity = (cart_item.quantity-1)
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
        offer += offer*quantity
        offer = Decimal(offer)
        if offer > Decimal(0):
            grand_total = Decimal(grand_total)
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
            response_data = {
                        'status': 'error',
                        'message': "product deleted"
                    }
            return JsonResponse(response_data) 
    except:
        pass
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({"success": True})
    else:
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
                coupon = Coupon.objects.get(code=code)
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
    coupon_percentage = None
    try:
        if request.user.is_authenticated:
            cart_items = CartItem.objects.filter(user=request.user, is_active=True)
        else:          
            cart = Cart.objects.get(cart_id=_cart_id(request))
            cart_items = CartItem.objects.filter(cart=cart, is_active=True)
            response_data = {
            'status': 'error',
            'message': 'Please log in to Ckeckout'
            }
            return JsonResponse(response_data)

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
                discount_percentage = Decimal(str(coupon.discount))
                coupon_percentage = discount_percentage
                total_decimal = Decimal(str(total))
                discount_amount =  (discount_percentage/ 100) * total_decimal
                subtotal = total_decimal- discount_amount
                coupon_discount = discount_amount #coupon.discount
            except Coupon.DoesNotExist:
                pass
           
        try:
            address = Address.objects.filter(user=request.user,status= 'False')
                
        except Address.DoesNotExist:
            address='none'

       
        grand_total = float(subtotal) + float(shipping)
        grand_total,offer_price = apply_offer(cart_items, grand_total)
        grand_total = float(grand_total)

    except ObjectDoesNotExist:
        pass

    coupons = Coupon.objects.filter(active=True,valid_from__lte=timezone.now(),valid_to__gte=timezone.now())
   
    context = {
        'total': total,
        'subtotal':subtotal,
        'quantity': quantity,
        'cart_items': cart_items,  
        'shipping': shipping,
        'grand_total': grand_total,
        'coupon_form': coupon_form,
        'address':address,
        'coupons':coupons,
        'coupon_id':coupon_id,
        'coupon':coupon_percentage,
        'coupon_discount':coupon_discount,
        'offer_price':offer_price,
    }

    if request.method == 'POST':
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

