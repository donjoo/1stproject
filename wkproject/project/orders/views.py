from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from cart.models import CartItem
import datetime
from .models import Order,Payment,OrderProduct
from .forms import OrderForm
from userauth.models import User,Address
import json
from app.models import Stock,Variants,Coupon,Transaction
from django.core.mail import EmailMessage
from django.template.loader import render_to_string
from django.utils import timezone
from userauth.views import wallet_balence
import secrets
from cart.views import apply_offer
from django.contrib.auth import authenticate
# Create your views here.

def generate_transaction_id():
    # Generate a random UUID (Universally Unique Identifier)
   trans_id = secrets.token_hex(8)
    # Return the transaction ID
   return trans_id

def cod_payment(request,order_id):
    order = Order.objects.get(id=order_id)
    user = User.objects.get(id=request.user.id)
    
    order.payment.payment_id =  generate_transaction_id()
    order.payment.amount_paid = order.order_total
    order.payment.status ='on Delivery'
    order.payment.save() 

    order.is_ordered =True
    order.save()
         
    CartItem.objects.filter(user=request.user).delete()
    if 'coupon_id' in request.session:
       del request.session['coupon_id']


    email_subject = 'Thank you for your order'
    message = render_to_string('app/order_recieved_email.html',{
        'user':user,
        'order':order
    })
    to_email = request.user.email
    send_email = EmailMessage(email_subject,message,to=[to_email])
    send_email.send()

    ordered_products = OrderProduct.objects.filter(order=order)

    subtotal = 0
    for item in ordered_products:
        subtotal += item.product_price * item.quantity

    data = {
        'order_number': order.order_number,
        'transID': order.payment.payment_id, 
        'order':order, 
        'ordered_products':ordered_products,
        'payment':order.payment,
        'subtotal':subtotal,
    }
    

    return render(request, "app/order_complete.html",data)


    
def wallet_auth(request,order_id):
    order = Order.objects.get(id=order_id)
    amount = order.order_total

    if request.method == "POST": 
        password = request.POST.get('password')
        if not request.user.check_password(password):
            messages.error(request, 'Your old password is incorrect.')
            return redirect('orders:wallet_auth',order_id)
        else:
            return redirect('orders:wallet_payment', order_id=order_id)
        
    context = {
        'amount':amount,

    }
    return render(request,'app/walletpay.html',context)

def wallet_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    user = User.objects.get(id=request.user.id)

    Transaction.objects.create(
        user=user,
        description="Placed Order  " + order_id,
        amount=order.order_total,
        transaction_type="Debit",
    )



    order.payment.payment_id =  generate_transaction_id()
    order.payment.amount_paid = order.order_total
    order.payment.status ='Completed'
    order.payment.save()


    order.is_ordered =True
    order.save()

    CartItem.objects.filter(user=request.user).delete()
    if 'coupon_id' in request.session:
        coupon_id = request.session['coupon_id']
        del request.session['coupon_id']
    

    email_subject = 'Thank you for your order'
    message = render_to_string('app/order_recieved_email.html',{
        'user':user,
        'order':order
    })
    to_email = request.user.email
    send_email = EmailMessage(email_subject,message,to=[to_email])
    send_email.send()

    ordered_products = OrderProduct.objects.filter(order=order)

    subtotal = 0
    for item in ordered_products:
        subtotal += item.product_price * item.quantity

    data = {
        'order_number': order.order_number,
        'transID': order.payment.payment_id, 
        'order':order, 
        'ordered_products':ordered_products,
        'payment':order.payment,
        'subtotal':subtotal
    }

    return render(request, "app/order_complete.html",data)



def payment(request):
    user = request.user
    body = json.loads(request.body)
    order_id = body['orderID']
    order = Order.objects.get(user=request.user,is_ordered=False,order_number=order_id)

    order.payment.payment_id = body['transID']
    order.payment.amount_paid = order.order_total
    order.payment.status = body['status']
    order.payment.save()

    order.is_ordered =True
    order.save()

    CartItem.objects.filter(user=request.user).delete()
    if 'coupon_id' in request.session:
       del request.session['coupon_id']

    email_subject = 'Thank you for your order'
    message = render_to_string('app/order_recieved_email.html',{
        'user':user,
        'order':order
    })
    to_email = request.user.email
    send_email = EmailMessage(email_subject,message,to=[to_email])
    send_email.send()

    data = {
        'order_number': order.order_number,
        'transID': order.payment.payment_id,
    }

    return JsonResponse(data)


def payment_type(request,payement_option):
    id = request.user.id
    wallet_amount = wallet_balence(request, id)
    if payement_option == "wallet":
      
      if Order.order_total > wallet_amount:
        messages.warning(request, "Insufficient Balence!")
        return False  
    return True  
    

def place_order(request,total=0,quantity=0,):
    id = request.user.id
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    coupon_id = request.session.get('coupon_id')
  
    if cart_count <= 0:
        return redirect('app:index')
    
    grand_total = 0
    coupon_discount = 0
    offer_price=0     
  
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    subtotal=total 
    shipping = (3 * total) / 100
    
    if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, valid_to__gte=timezone.now(), active=True)
                percentage =  (coupon.discount/ 100) * float(total)
                subtotal = float(total) - percentage
                
                coupon_discount = coupon.discount
            except Coupon.DoesNotExist:
                pass

    subtotal = float(subtotal)
    grand_total = subtotal + float(shipping)
    grand_total = round(grand_total,2)
    grand_total,offer_price = apply_offer(cart_items, grand_total)
    grand_total = round(grand_total,2)

    user = User.objects.all()
    billing = Address.objects.all()
   
    if request.method == "POST":
        form = OrderForm(request.POST)

        if form.is_valid():
                data = Order()
                payment = request.POST.get('payment_option')
                
                wallet_amount = wallet_balence(request, id)
                if payment == "Wallet":
                    if grand_total > wallet_amount:
                        messages.warning(request, "Insufficient Balance!")
                        return redirect('cart:Checkout')  # Stop the order creation process
                
                if payment == "cash on delivery":
                    if grand_total > 1000:
                        messages.warning(request,"COD is not available for orders above 1000")
                        return redirect('cart:Checkout')

                
                data.user = request.user     
                data.billing_address = form.cleaned_data['billing_address']
                data.shipping_address = form.cleaned_data['shipping_address']
            
                data.order_note = form.cleaned_data['order_note']
                data.order_total = round(grand_total,2)
                data.shipping = shipping
                data.created_at = datetime.datetime.now()
                if offer_price:
                  data.offer_price=offer_price
                    
                data.ip = request.META.get('REMOTE_ADDR')
                data.save()
                current_date = datetime.date.today()

                # Extract year, day, and month from the current date
                yr = int(current_date.strftime('%Y'))
                dt = int(current_date.strftime('%d'))
                mt = int(current_date.strftime('%m'))
                    

                if mt < 1 or mt > 12:
                    # Handle the invalid month value here, such as setting it to 1 or displaying an error message
                    mt = 1 
                    
                try:
                    d = datetime.date(yr, mt, dt)  # Corrected order of parameters
                except ValueError as e:
                    return HttpResponse(f"Error: {e}")

                current_date = d.strftime("%Y%m%d")
                order_number = current_date + str(data.id)
                data.order_number = order_number
            
                payement = request.POST.get('payment_option')
                if coupon_id:
                    try:
                        coupon = Coupon.objects.get(id=coupon_id)
                        data.coupon = coupon  # Assign Coupon instance to the order
                    except Coupon.DoesNotExist:
                        pass 

                payment_data = Payment(
                    user = request.user,
                    payment_method = payement,
                    status = "Payment pending"

                )
                payment_data.save()
                data.payment = payment_data 
                data.save()
                
                order = Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
                print(order.created_at)
                order_products(request,order,payment_data)
                context={
                    'order':order,
                    'cart_items':cart_items,
                    'total':total,
                    'grand_total':grand_total,
                    'shipping':shipping,
                    'payment':payement,
                    'coupon_discount':coupon_discount,
                    'offer_price':offer_price,
                        
                }
                return render(request,'app/payements.html',context)
        else:
                for field, errors in form.errors.items():
                    for error in errors:
                         messages.error(request, f"Error in {field}: {error}")
        return redirect('cart:Checkout')          
    else:        
        return redirect('app:index')

def payment_pending(request,order_id):
    order = Order.objects.get(id = order_id)
    order_products = OrderProduct.objects.filter(order=order)
    total = 0
    grand_total = 0      
    coupon_discount = 0

    for item in order_products:
        total += (item.product.price * item.quantity)

    cart_items = order_products
    grand_total = order.order_total
    shipping = order.shipping
    payment = order.payment.payment_method
    try:
       coupon_discount = order.coupon.discount 
    except:
        pass
    offer_price = order.offer_price          
    context = {
        'order':order,
        'cart_items':cart_items,
        'total':total,
        'grand_total':grand_total,
        'shipping':shipping,
        'payment':payment,
        'coupon_discount':coupon_discount,
        'offer_price':offer_price,
   }
   
    return render(request,'app/payements.html',context)

def order_products(request,order,payment_data):


    cart_items = CartItem.objects.filter(user=request.user)

    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment_data
        orderproduct.user_id = item.user_id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered=True
        orderproduct.save()


        cart_item =CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        orderproduct=OrderProduct.objects.get(id = orderproduct.id)
        orderproduct.variations.set(product_variation)
        orderproduct.save()


       
        product_variations = item.variations.all()
        for variation in product_variations:
            stock = get_object_or_404(Stock, variant=variation)
            stock.stock -= item.quantity
            stock.save()


def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status != 'Returned':
        order.status = 'Returned'
        order.save()
        messages.success(request, 'Order has been returned successfully.')
    else:
        messages.warning(request, 'Order is already returned.')
    return redirect('order_detail', order_id=order_id)

def order_complete(request):
    order_number=request.GET.get('order_number')
    transID = request.GET.get('payment_id')

    
    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order=order)

        payment = Payment.objects.get(payment_id=transID)
        
        subtotal = 0
        for i in order_products:
            subtotal += i.product_price * i.quantity

        context ={
            'order':order,
            'ordered_products':order_products,
            'order_number':order.order_number,
            'transID': payment.payment_id,
            'payment':payment,
            'subtotal':subtotal
        }
        return render(request,'app/order_complete.html',context)
    
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('app:index')


    

