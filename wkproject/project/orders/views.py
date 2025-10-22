from django.shortcuts import render,redirect,get_object_or_404
from django.http import HttpResponse,JsonResponse
from django.contrib import messages
from cart.models import CartItem
import datetime
from .models import Order,Payment,OrderProduct,ProductRating
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
from django.contrib.auth.decorators import login_required
from decimal import Decimal
import logging

# Set up logging
logger = logging.getLogger(__name__)

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

    # Try to send email, but don't let it fail the payment
    try:
        email_subject = 'Thank you for your order'
        message = render_to_string('app/order_recieved_email.html',{
            'user':user,
            'order':order
        })
        to_email = request.user.email
        send_email = EmailMessage(email_subject,message,to=[to_email])
        send_email.send()
    except Exception as email_error:
            # Log the email error but don't fail the payment
            logger.error(f"Email sending failed for COD order {order.order_number}: {email_error}")

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
    

    # Try to send email, but don't let it fail the payment
    try:
        email_subject = 'Thank you for your order'
        message = render_to_string('app/order_recieved_email.html',{
            'user':user,
            'order':order
        })
        to_email = request.user.email
        send_email = EmailMessage(email_subject,message,to=[to_email])
        send_email.send()
    except Exception as email_error:
        # Log the email error but don't fail the payment
        logger.error(f"Email sending failed for wallet order {order.order_number}: {email_error}")

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


@login_required(login_url='userauth:login')
def payment(request):
    try:
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

        # Try to send email, but don't let it fail the payment
        try:
            email_subject = 'Thank you for your order'
            message = render_to_string('app/order_recieved_email.html',{
                'user':user,
                'order':order
            })
            to_email = request.user.email
            send_email = EmailMessage(email_subject,message,to=[to_email])
            send_email.send()
        except Exception as email_error:
            # Log the email error but don't fail the payment
            logger.error(f"Email sending failed for order {order.order_number}: {email_error}")

        data = {
            'order_number': order.order_number,
            'transID': order.payment.payment_id,
        }

        return JsonResponse(data)
    
    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON data'}, status=400)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)
    except Exception as e:
        # Log the error for debugging
        logger.error(f"Payment processing error: {e}")
        return JsonResponse({'error': 'Payment processing failed'}, status=500)


def payment_type(request,payement_option):
    id = request.user.id
    wallet_amount = wallet_balence(request, id)
    if payement_option == "wallet":
      
      if Order.order_total > wallet_amount:
        messages.warning(request, "Insufficient Balence!")
        return False  
    return True  
    
@login_required(login_url='userauth:login')
def place_order(request,total=0,quantity=0,):
    id = request.user.id
    current_user = request.user
    cart_items = CartItem.objects.filter(user=current_user)
    cart_count = cart_items.count()
    coupon_id = request.session.get('coupon_id')
    coupon_discount=None
    coupon_percentage = None

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
                coupon_percentage = coupon.discount
                discount_percentage = Decimal(str(coupon.discount))
                total_decimal = Decimal(str(total))
                discount_amount =  (discount_percentage/ 100) * total_decimal
                subtotal = total_decimal- discount_amount
                coupon_discount = discount_amount

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
                data.created_at = timezone.now()
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
                    'coupon_percentage':coupon_percentage,
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


@login_required(login_url='userauth:login')
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

@login_required(login_url='userauth:login')
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
        coupon_discount = Decimal('0.00')
        if order.coupon:
            try:
                # coupon = Coupon.objects.get(id=order.coupon_id)
                coupon = Coupon.objects.get(
                    id=order.coupon_id,
                    active=True,
                    valid_to__gte=timezone.now()
                )
                discount_percentage = Decimal(str(coupon.discount))
                total_decimal = Decimal(str(subtotal))
                coupon_discount = (discount_percentage / 100) * total_decimal


            except Coupon.DoesNotExist:
                coupon = None
                coupon_discount = Decimal('0.00')
        context ={
            'order':order,
            'ordered_products':order_products,
            'order_number':order.order_number,
            'transID': payment.payment_id,
            'payment':payment,
            'subtotal':subtotal,
            'coupon_discount':coupon_discount,
        }
        return render(request,'app/order_complete.html',context)
    
    except (Payment.DoesNotExist,Order.DoesNotExist):
        return redirect('app:index')


    






def add_rating(request, order_product_id):
    if request.method == 'POST':
        order_product = get_object_or_404(OrderProduct, id=order_product_id, user=request.user)
        product = order_product.product
        rating_value = int(request.POST.get('rating', 0))
        review_text = request.POST.get('review', '')

        # Allow rating only if the order was delivered
        if order_product.order.status != 'Delivered':
            messages.warning(request, 'You can rate only after delivery.')
            return redirect('orders:order_detail', order_product.order.id)

        rating, created = ProductRating.objects.update_or_create(
            user=request.user,
            product=product,
            defaults={'rating': rating_value, 'review': review_text, 'order_product': order_product}
        )

        messages.success(request, 'Your rating has been submitted!')
        return redirect('userauth:my_order', order_product.order.id)


@login_required(login_url='userauth:login')
def cancel_order_item(request, order_product_id):
    """Cancel a specific product in an order"""
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')
    
    if request.method == "POST":
        order_product = get_object_or_404(OrderProduct, id=order_product_id, user=request.user)
        
        # Check if item can be cancelled
        if order_product.item_status != 'Ordered':
            messages.warning(request, f'This item is already {order_product.item_status.lower()}.')
            return redirect('userauth:my_order', order_product.order.id)
        
        # Check if order is in a cancellable state
        if order_product.order.status in ['Delivered', 'Cancelled', 'Returned']:
            messages.warning(request, 'This order cannot be cancelled.')
            return redirect('userauth:my_order', order_product.order.id)
        
        # Update item status
        order_product.item_status = 'Cancelled'
        order_product.save()
        
        # Add stock back for this specific item
        canceladd_stock_for_item(request, order_product)
        
        # Process refund for this specific item
        if order_product.order.payment:
            if (order_product.order.payment.payment_method == "Paypal" or 
                order_product.order.payment.payment_method == "Wallet"):
                
                item_total = order_product.product_price * order_product.quantity
                user = request.user
                Transaction.objects.create(
                    user=user,
                    description=f"Cancelled Item: {order_product.product.title} from Order {order_product.order.order_number}",
                    amount=item_total,
                    transaction_type="Credit",
                )
        
        # Check if all items are cancelled, then cancel the entire order
        remaining_items = OrderProduct.objects.filter(
            order=order_product.order, 
            item_status='Ordered'
        )
        if not remaining_items.exists():
            order_product.order.status = 'Cancelled'
            order_product.order.save()
            messages.success(request, 'Item cancelled successfully. Order has been cancelled as all items were cancelled.')
        else:
            messages.success(request, 'Item cancelled successfully.')
        
        return redirect('userauth:my_order', order_product.order.id)


@login_required(login_url='userauth:login')
def return_order_item(request, order_product_id):
    """Return a specific product in an order"""
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')
    
    if request.method == "POST":
        order_product = get_object_or_404(OrderProduct, id=order_product_id, user=request.user)
        
        # Check if item can be returned
        if order_product.item_status != 'Ordered':
            messages.warning(request, f'This item is already {order_product.item_status.lower()}.')
            return redirect('userauth:my_order', order_product.order.id)
        
        # Check if order is delivered
        if order_product.order.status != 'Delivered':
            messages.warning(request, 'Items can only be returned after delivery.')
            return redirect('userauth:my_order', order_product.order.id)
        
        # Update item status
        order_product.item_status = 'Returned'
        order_product.save()
        
        # Add stock back for this specific item
        canceladd_stock_for_item(request, order_product)
        
        # Process refund for this specific item
        if order_product.order.payment:
            item_total = order_product.product_price * order_product.quantity
            user = request.user
            Transaction.objects.create(
                user=user,
                description=f"Returned Item: {order_product.product.title} from Order {order_product.order.order_number}",
                amount=item_total,
                transaction_type="Credit",
            )
        
        # Check if all items are returned, then mark the entire order as returned
        remaining_items = OrderProduct.objects.filter(
            order=order_product.order, 
            item_status='Ordered'
        )
        if not remaining_items.exists():
            order_product.order.status = 'Returned'
            order_product.order.save()
            messages.success(request, 'Item returned successfully. Order has been marked as returned as all items were returned.')
        else:
            messages.success(request, 'Item returned successfully.')
        
        return redirect('userauth:my_order', order_product.order.id)


def canceladd_stock_for_item(request, order_product):
    """Add stock back for a specific cancelled/returned item"""
    try:
        for variant in order_product.variations.all():
            stock = Stock.objects.get(variant=variant)
            stock.stock += order_product.quantity
            stock.save()
    except Stock.DoesNotExist:
        logger.error(f"Stock not found for variant {variant} in order product {order_product.id}")
    except Exception as e:
        logger.error(f"Error adding stock back for order product {order_product.id}: {e}")