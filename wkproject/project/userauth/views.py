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
    s =""
    for x in range(0,4):
        s += str(random.randint(0,9))
    request.session["otp"]=s
    send_mail("otp for sign up",s,'djangoalerts0011@gmail.com',[request.session['email']],fail_silently=False)
    return render(request,"userauth/otp.html")
    
def otp_verification(request):
    if request.method == 'POST':
            otp_ = request.POST.get("otp")

            if otp_ == request.session["otp"]:
                encrypted_password = make_password(request.session['password'])
                nameuser = User(username=request.session['username'],email=request.session['email'],password=encrypted_password)
                nameuser.is_active = True
                nameuser.save()

                newuser = UserDetails(user=nameuser)
                newuser.save()

                login(request,nameuser,backend='django.contrib.auth.backends.ModelBackend')
                messages.success(request,'Account activation succesful.You are nw logged in.')
                return redirect('app:index')
            else:
                messages.error(request,"OTP doesn't match")
    return render(request,'userauth/otp.html')



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
                send_otp_login(request)
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
                send_otp_login(request)
                return render(request, "userauth/otp_login.html", {"email": email})
        except User.DoesNotExist:
            messages.warning(request, f"User with email {email} does not exist.")
            return redirect("userauth:forgot_password")

    return render(request, "userauth/login_otp.html")

  
    








@never_cache
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def send_otp_login(request):
    s=""
    for x in range(0,4):
        s += str(random.randint(0,9))
    request.session["otp"]=s
    send_mail("otp for sign up",s,'djangoalerts0011@gmail.com',[request.session['email']],fail_silently=False)
    return render(request,"userauth/otp_login.html")

@never_cache
@cache_control(no_cache=True,must_revalidate=True, no_store=True)
def otp_verification_login(request):
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




















def user_profile(request):
    # user = request.user
    if not request.user.is_authenticated:
        return redirect('userauth:login')
    try:
        address = Address.objects.filter(user=request.user,status= 'False')
    except Address.DoesNotExist:
        address = None
    userdetail = UserDetails.objects.get(user=request.user)

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

def address_edit(request,id):
    if not request.user.is_authenticated:
       
            return redirect('userauth:login')
    
    address = get_object_or_404(Address,id=id)
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
    except ValueError:
        return redirect('userauth:user_profile')
    # address.delete()
    address.status = True
    address.save()

    return redirect('userauth:user_profile')
        
def profile_update(request):
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


 
def my_order(request,order_id):
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)

    subtotal = 0
    for i in order_products:
            subtotal += i.product_price * i.quantity
    for item in order_products:
        item.total_price = item.product.price * item.quantity 
    context = {
        'order': order,
        'order_products': order_products,
        'subtotal':subtotal,
    }

    return render(request, 'userauth/my_order.html',context)

   


def cancel_order(request, order_id,):
    if request.method == "POST":
        data = Order.objects.get(id=order_id)
        data.status = "Cancelled"
        data.save()
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

# def cancel_order(request, order_id):
#     order = get_object_or_404(Order, id=order_id)
#     if order.status != 'Cancelled':
#         order.status = 'Cancelled'
#         order.save()
#         messages.success(request, 'Order has been cancelled successfully.')
#     else:
#         messages.warning(request, 'Order is already cancelled.')
#     return redirect('userauth:my_order', order_id=order_id)




def return_order(request, order_id):
        if request.method == "POST":
            data = Order.objects.get(id=order_id)
            data.status = "Returned"
            data.save()
            messages.success(request, 'Order has been returned successfully.')
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






# def view_wallet(request):
#     try:
#         wallet = Wallet.objects.get(user=request.user)
#     except Wallet.DoesNotExist:
#         # Handle the case where the wallet does not exist for the user
#         wallet = None 
#     transactions = Transaction.objects.filter(wallet=wallet)
#     return render(request, 'app/wallet.html', {'wallet': wallet, 'transactions': transactions})


# @csrf_exempt
# def add_funds(request):
#     if request.method == 'POST':
#         try:
#             data = json.loads(request.body)
#             amount = data.get('amount')
#             transaction_id = data.get('transaction_id')
#             if amount is not None and transaction_id is not None:
#                 wallet, created = Wallet.objects.get_or_create(user=request.user)
#                 wallet.balance += amount
#                 wallet.save()
#                 Transaction.objects.create(wallet=wallet, amount=amount, transaction_id=transaction_id)
#                 return JsonResponse({'success': True})
#             else:
#                 return JsonResponse({'error': 'Invalid JSON data. Required fields are missing.'}, status=400)
#         except json.JSONDecodeError:
#             return JsonResponse({'error': 'Invalid JSON data'}, status=400)
#     else:
#         return JsonResponse({'error': 'Only POST requests are allowed'}, status=405)




def wallet_balence(request, user_id):
    datas = Transaction.objects.filter(user=user_id)
    grand_total = 0
    for data in datas:
        if data.transaction_type == "Credit":
            grand_total += data.amount
        else:
            grand_total -= data.amount
    return grand_total



# def user_wallet(request, user_id):
def user_wallet(request):
    user_id = request.user
    total = wallet_balence(request, user_id)

    content = {
        "TransactionHistory": Transaction.objects.filter(user=user_id)
        .order_by("id")
        .reverse(),
        "wallet_total": total,
    }

    return render(request, "app/wallet.html", content)

