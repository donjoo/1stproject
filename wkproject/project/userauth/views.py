from django.shortcuts import render,redirect,get_object_or_404
from .forms import CreateUserForm,Profileform,PasswordChangeForm,AddFundsForm
from django.contrib import messages
from app.models import UserDetails,Transaction,Coupon,WishList,Product
from userauth.models import User,Address
from django.contrib.auth import login,authenticate,logout
from django.views.decorators.cache import never_cache
import random
from django.core.mail import send_mail
from django.contrib.auth.hashers import make_password
from app.backends import EmailBackend
from django.contrib.auth import update_session_auth_hash
from django.views.decorators.cache import cache_control
from django.urls import reverse
from django.http import HttpResponseBadRequest,HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from cart.models import Cart,CartItem
from cart.views import _cart_id
import requests
from urllib.parse import urlparse
from orders.models import Order,OrderProduct,Payment
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from orders.models import Order
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from app.models import Variants,Stock
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

# Create your views here.

@never_cache
def handel_signup(request):
    if request.method == 'POST':
        form = CreateUserForm(request.POST,None)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            password = form.cleaned_data.get('password1')
            request.session["username"]=username
            request.session["password"]=password
            request.session["email"]=email

            messages.success(request,f'hey {username},your account was created succesfully')
            email=request.POST["email"]
            send_otp(request)
            return render(request,'userauth/otp.html',{"email":email})

    else:
        form = CreateUserForm()
    
    context = {'form':form}
    return render(request,'userauth/signup.html',context)

@never_cache
def send_otp(request):
    otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])

    # Store OTP and expiry in session
    expiry_time = timezone.now() + timedelta(minutes=5)
    request.session["otp"] = otp
    request.session["otp_expiry"] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')

    # Prepare email content
    subject = "Your OTP Code for AnimWear Signup"
    message = f"""
                Hello {request.session.get('username', '')},

                Your One-Time Password (OTP) for completing your signup at AnimWear is:

                    🔐 {otp}

                Please enter this code on the verification page within **5 minutes**.

                ⏰ This OTP will expire at: {expiry_time.strftime('%I:%M %p on %B %d, %Y')}.

                If you didn’t request this, please ignore this email.

                Best regards,  
                AnimWear Team
                """

    send_mail(
        subject,
        message,
        'djangoalerts0011@gmail.com',
        [request.session['email']],
        fail_silently=False,
    )
    return render(request,"userauth/otp.html")
    
# def otp_verification(request):
#     if request.method == 'POST':
#             otp_ = request.POST.get("otp")

#             if otp_ == request.session["otp"]:
#                 encrypted_password = make_password(request.session['password'])
#                 nameuser = User(username=request.session['username'],email=request.session['email'],password=encrypted_password)
#                 nameuser.is_active = True
#                 nameuser.save()

#                 newuser = UserDetails(user=nameuser)
#                 newuser.save()

#                 login(request,nameuser,backend='django.contrib.auth.backends.ModelBackend')
#                 messages.success(request,'Account activation succesful.You are nw logged in.')
#                 return redirect('app:index')
#             else:
#                 messages.error(request,"OTP doesn't match")
#     return render(request,'userauth/otp.html')

# ---------------- VERIFY OTP ----------------
def otp_verification(request):
    if request.method == 'POST':
        otp_input = request.POST.get("otp")
        otp_session = request.session.get("otp")
        otp_expiry_str = request.session.get("otp_expiry")

        if not otp_session or not otp_expiry_str:
            messages.error(request, "OTP session expired. Please request a new one.")
            return redirect('userauth:resend_otp')

        otp_expiry = timezone.strptime(otp_expiry_str, '%Y-%m-%d %H:%M:%S')

        if timezone.now() > otp_expiry:
            messages.error(request, "OTP has expired. Please request a new one.")
            return redirect('userauth:resend_otp')

        if otp_input == otp_session:
            encrypted_password = make_password(request.session['password'])
            user = User(
                username=request.session['username'],
                email=request.session['email'],
                password=encrypted_password,
                is_active=True,
            )
            user.save()

            UserDetails.objects.create(user=user)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')

            request.session.pop('otp', None)
            request.session.pop('otp_expiry', None)

            messages.success(request, 'Account activation successful. You are now logged in.')
            return redirect('app:index')
        else:
            messages.error(request, "Invalid OTP. Please try again.")

    return render(request, 'userauth/otp.html')



# ---------------- RESEND OTP ----------------
@never_cache
def resend_otp(request):
    """
    Sends a new OTP when user clicks 'Resend OTP'.
    """
    if not request.session.get('email'):
        messages.error(request, "Session expired. Please sign up again.")
        return redirect('userauth:signup')

    otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    expiry_time = timezone.now() + timedelta(minutes=5)

    request.session["otp"] = otp
    request.session["otp_expiry"] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')

    subject = "Your New OTP Code for AnimWear Signup"
    message = f"""
        Hello {request.session.get('username', '')},

        Here’s your new One-Time Password (OTP) for completing your signup:

            🔐 {otp}

        Please enter this code within **5 minutes**.

        ⏰ This OTP will expire at: {expiry_time.strftime('%I:%M %p on %B %d, %Y')}.

        If you didn’t request this, you can safely ignore this email.

        Best regards,  
        AnimWear Team
        """

    send_mail(subject, message, 'djangoalerts0011@gmail.com', [request.session['email']], fail_silently=False)

    messages.info(request, "A new OTP has been sent to your email.")
    return redirect('userauth:otp_verification')

@never_cache
def handel_login(request):
    if request.user.is_authenticated:
        messages.warning(request,f'you are already logged in')
        return redirect("app:index")
    if request.method == "POST":
        email = request.POST.get('email')
        password = request.POST.get('password')
        request.session["email"]=email  
        if not User.objects.filter(email=email).exists():
            messages.error(request,"Invalid email adress")
            return redirect('userauth:login')
        if not User.objects.filter(email=email,is_active=True).exists():
            messages.error(request,"Account blocked!!!")
            return redirect('userauth:login')
        try:
            user = User.objects.get(email=email)
            user = authenticate(email=email,password=password,backend=EmailBackend)

            if user is not None:
                try:
                    cart=Cart.objects.get(cart_id=_cart_id(request))
                    is_cart_item_exists = CartItem.objects.filter(cart=cart).exists()
                    if is_cart_item_exists:
                        cart_item = CartItem.objects.filter(cart=cart)
                        product_size =[]
                        for item in cart_item:
                            variataion = item.variations.all()
                            product_size.append(list(variataion))

                        cart_item = CartItem.objects.filter(user=user)           
                        ex_var_list = []
                        id = []
                        for item in cart_item:
                            existing_variations = item.variations.all()
                            ex_var_list.append(list(existing_variations))
                            id.append(item.id)
                        
                        for pr in product_size:
                            if pr in ex_var_list:
                                index = ex_var_list.index(pr)
                                item_id=id[index]
                                item=CartItem.objects.get(id=item_id)
                                item.quantity += 1
                                item.user=user
                                item.save()
                            else:
                                cart_item = CartItem.objects.filter(cart=cart)
                                for item in cart_item:
                                    item.user = user
                                    item.save()

                except:
                    pass
                try:
                    # Transfer wishlist items
                    wishlist_pids = request.session.get('wishlist', [])
                    if wishlist_pids:
                        wishlist = WishList.objects.get_or_create(user=user)[0]
                        products = Product.objects.filter(pid__in=wishlist_pids)
                        wishlist.products.add(*products)
                        del request.session['wishlist']

                except WishList.DoesNotExist:
                    pass

                login(request,user)
                messages.success(request,'Login successful.')
                url = request.META.get('HTTP_REFERER')
                try:
                    query = requests.utils.urlparse(url).query
                    params = dict(x.split('=') for x in query.split('&'))
                    if 'next' in params:
                        nextpage = params['next']
                        return redirect(nextpage)
                except:
                  return redirect("app:index")
            else:
                messages.warning(request,'Username or passsword is incorrect.')

        except:
            messages.warning(request,f'User with {email} doesnt exists')

    context={}
    return render(request,'userauth/login.html',context)

@never_cache
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def login_otp(request):
    '''
    Used when user logs in using OTP instead of password.
    '''
    if request.user.is_authenticated:
        messages.warning(request, "Hey, you are already logged in.")
        return redirect("app:index")
    
    if request.method == "POST":
        email = request.POST.get("email")
        request.session["email"] = email

        if not User.objects.filter(email=email).exists():
            messages.error(request, "Invalid email address.")
            return redirect("userauth:login_otp")
        
        if not User.objects.filter(email=email, is_active=True).exists():
            messages.error(request, "Account is blocked.")
            return redirect("userauth:login_otp")
        
        try: 
            user = User.objects.get(email=email)
            if user is not None:
                send_otp_login(request,"login")
                return render(request, "userauth/otp_login.html", {"email": email})
        except User.DoesNotExist:
            messages.warning(request, f"User with email {email} does not exist.")
            return redirect("userauth:login_otp")

    return render(request, "userauth/login_otp.html")

def forgot_password(request):
    
    if request.method == "POST":
        email = request.POST.get("email")
        request.session["email"] = email
        request.session["method"] = "forgot_password"

        if not User.objects.filter(email=email).exists():
            messages.error(request, "Invalid email address.")
            return redirect("userauth:forgot_password")
        
        if not User.objects.filter(email=email, is_active=True).exists():
            messages.error(request, "Account is blocked.")
            return redirect("userauth:forgot_password")
        
        try: 
            user = User.objects.get(email=email)
            if user is not None:
                send_otp_login(request, "forgot_password")
                return render(request, "userauth/otp_login.html", {"email": email})
        except User.DoesNotExist:
            messages.warning(request, f"User with email {email} does not exist.")
            return redirect("userauth:forgot_password")

    return render(request, "userauth/login_otp.html")

  
    








@never_cache
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def send_otp_login(request,purpose="login"):
    '''
    Used when user logs in using OTP instead of password.
    Sends OTP to reset password
    '''
    otp = ''.join([str(random.randint(0, 9)) for _ in range(4)])
    expiry_time = timezone.now() + timedelta(minutes=5)

    request.session["otp"] = otp
    request.session["otp_expiry"] = expiry_time.strftime('%Y-%m-%d %H:%M:%S')

    subject_map = {
        "login": "Your OTP Code for Login",
        "forgot_password": "Reset Your Password with OTP"
    }
    subject = subject_map.get(purpose, "Your OTP Code")

    message = f"""
    Hello {request.session.get('username', '') or ''},

    Your One-Time Password (OTP) is: {otp}

    This OTP will expire at {expiry_time.strftime('%I:%M %p on %B %d, %Y')}.

    - AnimWear Team
    """

    send_mail(subject, message, 'djangoalerts0011@gmail.com', [request.session['email']], fail_silently=False)

@never_cache
@cache_control(no_cache=True,must_revalidate=True, no_store=True)
def otp_verification_login(request):
    '''
    Used when user logs in using OTP instead of password.
    Sends OTP to reset password, and after verifying OTP
    '''
    if request.method == 'POST':
        otp_ = request.POST.get("otp")

        try:
            if otp_ == request.session["otp"]:
                request.session.pop('otp',None)
                if request.session["method"] == 'forgot_password':
                    return redirect('userauth:new_password')
            

                user = User.objects.get(email=request.session.get("email"))

                user.is_active = True

                user.save()
                login(request,user,backend='django.contrib.auth.backends.ModelBackend')

                messages.success(request,'Account activated successfully.')
                redirect_url=reverse('app:index')
                return HttpResponseRedirect(redirect_url)
            else:
                messages.error(request,"otp doesn't match.")

        except KeyError:
            messages.error(request,"session expired.please try logging in again")


def new_password(request):
    if request.method == 'POST':
        new_password1 = request.POST.get('new_password1')
        new_password2 = request.POST.get('new_password2')
        
        try:
            if new_password1 != new_password2:
                messages.error(request, 'The new passwords do not match.')
                return redirect('userauth:new_password')
        
            user = User.objects.get(email=request.session.get("email"))
            user.set_password(new_password1)
            user.save()
            login(request,user,backend='django.contrib.auth.backends.ModelBackend')


            messages.success(request, 'Your password was successfully updated!')
            redirect_url=reverse('app:index')
            return HttpResponseRedirect(redirect_url)
        
        except KeyError:
            messages.error(request,"session expired.please try logging in again")
    
    return render(request,'userauth/new_password.html')

   
@never_cache
def logoutUser(request):
    logout(request)
    request.session.flush()
    messages.success(request,'you logged out')
    return redirect('app:index')



                    # FORGOT_PASSWORD# FORGOT_PASSWORD# FORGOT_PASSWORD
                    # FORGOT_PASSWORD# FORGOT_PASSWORD# FORGOT_PASSWORD
                    # FORGOT_PASSWORD# FORGOT_PASSWORD# FORGOT_PASSWORD
                    # FORGOT_PASSWORD# FORGOT_PASSWORD# FORGOT_PASSWORD


@login_required(login_url='userauth:login')
def user_profile(request):
    # user = request.user
    if not request.user.is_authenticated:
        return redirect('userauth:login')
    try:
        address = Address.objects.filter(user=request.user,status= 'False')
    except Address.DoesNotExist:
        address = None
    try:
        userdetail = UserDetails.objects.get(user=request.user)
    except UserDetails.DoesNotExist:
        userdetail = None
    

    try:
       orders = Order.objects.filter(user=request.user).order_by('-created_at')
    except Order.DoesNotExist:
       orders = None

    try:
        order_products = OrderProduct.objects.filter(order=orders)
    except:
        order_products = None

    try:
        profile = UserDetails.objects.get(user=request.user)
        # address = Address.objects.get(user=request.user)
    except UserDetails.DoesNotExist:
        # Create UserDetails instance if it doesn't exist
        profile = UserDetails(user=request.user)
        profile.save()
    form = Profileform(instance=profile)

  
   
    context = {
        'form':form,
        'address':address,
        'user':userdetail,
        'orders': orders,
        'order_products':order_products,
    }
    
    return render(request,"userauth/user_profile.html",context)

@login_required(login_url='userauth:login')
def order_list(request):
    # Retrieve all orders
    all_orders = Order.objects.filter(user=request.user).order_by('-created_at')

    # Paginate orders
    paginator = Paginator(all_orders, 10)  # Show 10 orders per page
    page_number = request.GET.get('page')

    try:
        orders = paginator.page(page_number)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        orders = paginator.page(1)
    except EmptyPage:
        # If page is out of range, deliver last page of results.
        orders = paginator.page(paginator.num_pages)

    return render(request,'userauth/orders_lists.html',{'orders': orders})



@login_required(login_url='userauth:login')
def address_edit(request,id):
    if not request.user.is_authenticated:
       
            return redirect('userauth:login')
    
    
    
    address = get_object_or_404(Address,id=id)
    if address.user != request.user:
        messages.error(request, "You are not authorized to edit this address.")
        return redirect('userauth:user_profile')
    if request.method == 'POST':
        house = request.POST.get("house")
        street = request.POST.get("street")
        landmark = request.POST.get("landmark")
        pincode = request.POST.get("pincode")
        town = request.POST.get("town")
        state = request.POST.get("state")
        


        address.house  =  house 
        address.street = street
        address.landmark = landmark
        address.pincode = pincode
        address.town = town
        address.state = state
        

        address.save()

       
        return redirect('userauth:user_profile') 

   
    try:
        addresses = get_object_or_404(Address,id=id)
    except Address.DoesNotExist:
        addresses = None

    try:
        user_detail = UserDetails.objects.get(user=request.user)
    except UserDetails.DoesNotExist:
        user_detail = None

    context = {
        'addresses': addresses,
        'user_detail': user_detail,
    }

    return render(request, 'userauth/address_edit.html', context)

@login_required(login_url='userauth:login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_address(request,id):
    if not request.user.is_authenticated:
        return redirect('userauth:login')
        
    try:
        address = Address.objects.get(id=id)
        if address.user != request.user:
            messages.error(request, "You are not authorized to edit this address.")
            return redirect('userauth:user_profile')
    except ValueError:
        return redirect('userauth:user_profile')
    # address.delete()
    address.status = True
    address.save()

    return redirect('userauth:user_profile')
        
@login_required(login_url='userauth:login')
def profile_update(request):

    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')
    
    try:
        profile = UserDetails.objects.get(user=request.user)
        # address = Address.objects.get(user=request.user)
    except UserDetails.DoesNotExist:
        # Create UserDetails instance if it doesn't exist
        profile = UserDetails(user=request.user)
        profile.save()

    if request.method == 'POST':
        form = Profileform(request.POST, request.FILES, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully')
            return redirect('userauth:user_profile')
    else:
        form = Profileform(instance=profile)

    context = {
        'form': form,
        'profile': profile,
        # 'address':address
    }

    return render(request, 'userauth/user_profile.html', context)  


    
@login_required
def change_password(request):
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')
    if request.method == 'POST':
        old_password = request.POST.get('old_password')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        if not request.user.check_password(old_password):
            messages.error(request, 'Your old password is incorrect.')
            return redirect('userauth:change_password')
        
        if new_password != confirm_password:
            messages.error(request, 'The new passwords do not match.')
            return redirect('userauth:change_password')
        
        # Update the user's password
        # request.user.set_password(new_password1)
        # request.user.save()
        user = User.objects.get(email=request.user)
        user.set_password(new_password)
        user.save()
        
        messages.success(request, 'Your password was successfully updated!')
        return redirect('userauth:user_profile')
    
    return redirect('userauth:user_profile')


@login_required(login_url='userauth:login')
def my_order(request,order_id):
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')


    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    coupon = None
    coupon_discount = Decimal('0.00')

    if order.user != request.user:
        messages.error(request, "You are not authorized to view this order.")
        return redirect('userauth:orders_lists')

    subtotal = 0
    for i in order_products:
            subtotal += i.product_price * i.quantity
    for item in order_products:
        item.total_price = item.product.price * item.quantity 
    
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
    
    
    context = {
        'order': order,
        'order_products': order_products,
        'subtotal':subtotal,
        'coupon_discount':coupon_discount,
    }

    return render(request, 'userauth/my_order.html',context)

   

@login_required(login_url='userauth:login')
def cancel_order(request, order_id,):
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')
    
    if request.method == "POST":
        data = Order.objects.get(id=order_id)
        if data.user != request.user:
            messages.error(request, "You are not authorized to cancel this order.")
            return redirect('userauth:orders_lists')
        
        data.status = "Cancelled"
        data.save()
        canceladd_stock(request,data)
        messages.success(request, 'Order has been cancelled successfully.')
        if data.payment:
            if (
                data.payment.payment_method == "Paypal"
                or data.payment.payment_method == "Wallet"
            ):
                
                amount = data.order_total
                user = request.user
                Transaction.objects.create(
                    user=user,
                    description="Cancelled Order " + str(order_id),
                    amount=amount,
                    transaction_type="Credit",
                )

        return redirect("userauth:my_order",order_id)

@login_required(login_url='userauth:login')
def canceladd_stock(request,order):
    order_products = OrderProduct.objects.filter(order=order)
    
    for order_product in order_products:
            print(order_product.variations)
            for varian in order_product.variations.all():
                variant = Variants.objects.get(product=order_product.product,size=varian)
                stock = Stock.objects.get(variant=variant)
                stock.stock += order_product.quantity  # Add the cancelled quantity back to the variation's stock
                stock.save()
@login_required(login_url='userauth:login')
def return_order(request, order_id):
        if not request.user.is_active:
            messages.error(request, "Your account is blocked.")
            return redirect('userauth:login')
        
        if request.method == "POST":
            data = Order.objects.get(id=order_id)
            if data.user != request.user:
                messages.error(request, "You are not authorized to return this order.")
                return redirect('userauth:orders_lists')
            data.status = "Returned"
            data.save()
            canceladd_stock(request,data)
            messages.success(request, 'Order has been returned successfully.')
            if data.payment:
                # if (
                #     data.payment.payment_method == "Paypal"
                #     or data.payment.payment_method == "Wallet"
                # ):
                    
                    amount = data.order_total
                    user = request.user

                    Transaction.objects.create(
                        user=user,
                        description="Cancelled Order " + str(order_id),
                        amount=amount,
                         transaction_type="Credit",
                    )

            return redirect("userauth:my_order",order_id)



@login_required(login_url='userauth:login')
def wallet_balence(request, user_id):
    if not request.user.is_active:
        return 0
    
    datas = Transaction.objects.filter(user=user_id)
    grand_total = 0
    for data in datas:
        if data.transaction_type == "Credit":
            grand_total += data.amount
        else:
            grand_total -= data.amount
    return grand_total



# def user_wallet(request, user_id):
@login_required(login_url='userauth:login')
def user_wallet(request):
    if not request.user.is_active:
        messages.error(request, "Your account is blocked.")
        return redirect('userauth:login')

    user_id = request.user
    total = wallet_balence(request, user_id)

    content = {
        "TransactionHistory": Transaction.objects.filter(user=user_id)
        .order_by("id")
        .reverse(),
        "wallet_total": total,
    }

    return render(request, "app/wallet.html", content)

