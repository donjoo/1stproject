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

# Create your views here.



def generate_transaction_id():
    # Generate a random UUID (Universally Unique Identifier)
   trans_id = secrets.token_hex(8)
    # Return the transaction ID
   return trans_id

def cod_payment(request,order_id):
    order = Order.objects.get(id=order_id)
    user = User.objects.get(id=request.user.id)

    payment = Payment(
        user = request.user,
        payment_id = generate_transaction_id(),
        payment_method ='Cash on Delivery',
        amount_paid = order.order_total,
        status ='on Delivery',

    )
    payment.save()

    order.payment=payment
    order.is_ordered =True
    order.save()
    

    cart_items = CartItem.objects.filter(user=request.user)
    print('product')
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
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
        


    CartItem.objects.filter(user=request.user).delete()
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

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id, 
        'order':order, 
        'ordered_products':ordered_products,
        'payment':payment
    }
    

    return render(request, "app/order_complete.html",data)


    
def wallet_payment(request, order_id):
    order = Order.objects.get(id=order_id)
    user = User.objects.get(id=request.user.id)
    cart_items = CartItem.objects.filter(user=request.user)

    Transaction.objects.create(
        user=user,
        description="Placed Order  " + order_id,
        amount=order.order_total,
        transaction_type="Debit",
    )
    payment = Payment(
        user = request.user,
        payment_id = generate_transaction_id(),
        payment_method ='Wallet',
        amount_paid = order.order_total,
        status ='Completed',

    )
    payment.save()

    order.payment=payment
    order.is_ordered =True
    order.save()

    print('product')
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
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
        


    CartItem.objects.filter(user=request.user).delete()
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

    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id, 
        'order':order, 
        'ordered_products':ordered_products,
        'payment':payment
    }

    return render(request, "app/order_complete.html",data)



def payment(request):
    user = request.user
    body = json.loads(request.body)
    print(body['orderID'], 'thi is the header of paye')
    order = Order.objects.get(user=request.user,is_ordered=False,order_number=body['orderID'])
    payment = Payment(
        user = request.user,
        payment_id = body['transID'],
        payment_method =body['payment_method'],
        amount_paid = order.order_total,
        status = body['status'],

    )
    payment.save()

    order.payment=payment
    order.is_ordered =True
    order.save()



    cart_items = CartItem.objects.filter(user=request.user)


    print('product')
    for item in cart_items:
        orderproduct = OrderProduct()
        orderproduct.order_id = order.id
        orderproduct.payment = payment
        orderproduct.user_id = item.user_id
        orderproduct.product_id = item.product_id
        orderproduct.quantity = item.quantity
        orderproduct.product_price = item.product.price
        orderproduct.ordered=True
        orderproduct.save()
        print('order producttttt')


        cart_item =CartItem.objects.get(id=item.id)
        product_variation = cart_item.variations.all()
        print('hiii1')
        print('hiii1')
        orderproduct=OrderProduct.objects.get(id = orderproduct.id)
        print('hiii2')
        orderproduct.variations.set(product_variation)
        orderproduct.save()


        # variants = Variants.objects.get(id=item.variations)
        # stock = Stock.objects.get(variant_id=variants.id)
        # stock.stock -= item.quantity
        # stock.save()
        product_variations = item.variations.all()
        for variation in product_variations:
            stock = get_object_or_404(Stock, variant=variation)
            stock.stock -= item.quantity
            stock.save()
        


    CartItem.objects.filter(user=request.user).delete()
    del request.session['coupon_id']


    email_subject = 'Thank you for your order'
    message = render_to_string('app/order_recieved_email.html',{
        'user':user,
        'order':order
    })
    to_email = request.user.email
    send_email = EmailMessage(email_subject,message,to=[to_email])
    send_email.send()
    # try:
    #     print(order.order_number,'heyy youuu')
    # except:
    #     print('order.order_number')


    try:
        print(payment.payment_id,'hey yuuuu')
    except:
        print('payment.payment_id')


  
    data = {
        'order_number': order.order_number,
        'transID': payment.payment_id,
        # Add any other relevant data here
    }

    return JsonResponse(data)
    # return render(request,'app:category_list')


def payment_type(request,payement_option):
    id = request.user.id
    wallet_amount = wallet_balence(request, id)
    if payement_option == "wallet":
      if Order.order_total > wallet_amount:
        print(wallet_amount)
        print(Order.order_total)
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
  
    
    for cart_item in cart_items:
        total += (cart_item.product.price * cart_item.quantity)
        quantity += cart_item.quantity
    subtotal=total 
    shipping = (3 * total) / 100
    if coupon_id:
            try:
                coupon = Coupon.objects.get(id=coupon_id, valid_to__gte=timezone.now(), active=True)
                subtotal=total - coupon.discount
                coupon_discount = coupon.discount
            except Coupon.DoesNotExist:
                pass

  

    grand_total = subtotal + shipping

    user = User.objects.all()
    billing = Address.objects.all()

   
    
    if request.method == "POST":
        form = OrderForm(request.POST)
        if form.is_valid():
            data = Order()
            payment = request.POST.get('payment_option')

            wallet_amount = wallet_balence(request, id)
            print(payment)
            print(wallet_amount)
            if payment == "Wallet":
             print(grand_total, wallet_amount)
             if grand_total > wallet_amount:
                print(wallet_amount)
                print(grand_total)
                messages.warning(request, "Insufficient Balance!")
                return redirect('cart:Checkout')  # Stop the order creation process
             
            data.user = request.user     
            data.billing_address = form.cleaned_data['billing_address']
            data.shipping_address = form.cleaned_data['shipping_address']
        
            data.order_note = form.cleaned_data['order_note']
            data.order_total = grand_total
            data.shipping = shipping
                
            print(data.billing_address,data.shipping_address,data.order_note,data.order_total)
            # data.shipping = shipping
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

            # d = datetime.date(yr, mt,dt)
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
            
              
            data.save()
            
                


            order = Order.objects.get(user=current_user,is_ordered=False,order_number=order_number)
            context={
                'order':order,
                'cart_items':cart_items,
                'total':total,
                'grand_total':grand_total,
                'shipping':shipping,
                'payment':payement,
                'coupon_discount':coupon_discount,
                    
            }
            return render(request,'app/payements.html',context)   
            

    return redirect('app:index')








def order_complete(request):
    order_number=request.GET.get('order_number')
    transID = request.GET .get('payment_id')


    try:
        order = Order.objects.get(order_number=order_number, is_ordered=True)
        order_products = OrderProduct.objects.filter(order_id =order.id)

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




def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    if order.status != 'Returned':
        order.status = 'Returned'
        order.save()
        messages.success(request, 'Order has been returned successfully.')
    else:
        messages.warning(request, 'Order is already returned.')
    return redirect('order_detail', order_id=order_id)





        

    

