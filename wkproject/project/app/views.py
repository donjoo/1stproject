from django.shortcuts import render,HttpResponse,redirect,get_object_or_404,HttpResponseRedirect
from app.models import Product,ProductImage,Category,CategoryAnime,AnimeCharacter,Variants,WishList
from userauth.models import User,Address
from django.contrib.auth import login,authenticate
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Q
from cart.models import CartItem
from cart.views import _cart_id
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator


# Create your views here.

def index(request):
    products = Product.objects.all().order_by('-date') 
    paginator = Paginator(products,9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)

    context = {
        "products":paged_products
    }
    return render(request,'app/index.html',context)

def category_list_view(request):
    categories = Category.objects.all()
    context ={
        "categories":categories
    }
    return render(request, 'app/category_list.html',context)

def category_product_list(request,cid):
    category = Category.objects.get(cid=cid)

    products = Product.objects.filter(status='True', category=category)
     
    context = {
        "category":category,
        "products":products
    }
    return render(request,"app/category_product_list.html",context)

def Anime_product_list(request,aid):
    animes = CategoryAnime.objects.get(aid=aid)
    
    products = Product.objects.filter(status='True', anime=animes)
     
    context = {
        "category":animes,
        "products":products
    }
    return render(request,"app/category_product_list.html",context)


def Character_product_list(request,lid):
    character = AnimeCharacter.objects.get(lid=lid)
    
    products = Product.objects.filter(status='True', character=character)
     
    context = {
        "category":character,
        "products":products
    }
    return render(request,"app/category_product_list.html",context)


def product_detail(request, pid):
    try:
        product = get_object_or_404(Product,pid=pid)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request),product=product).exists()
       
    except Product.DoesNotExist:
        messages.warning(request,f'you are already logged in')
        return redirect("app:index")
   
    p_image = product.p_images.all()
    sizes = Variants.objects.filter(product=product)
    context={
        "product":product,
        "p_image":p_image,
        'in_cart':in_cart,
        'sizes':sizes,
    }

    return render(request,'app/product_detail.html',context)


@login_required(login_url='userauth:handel_login')
def add_address(request):
    if not request.user.is_authenticated:
        return redirect('userauth:handel_login')
        
   
    # user = User.objects.get(pk=request.user.pk)
    user = request.user
   

    if request.method == 'POST':
        
        house = request.POST.get('house')
        street = request.POST.get('street')
        landmark = request.POST.get('landmark')
        pincode = request.POST.get('pincode')
        town = request.POST.get('town')
        state = request.POST.get('state')
    
        address = Address(
        
            user=user,
            house = house,
            street = street,
            landmark =landmark,
            pincode = pincode,
            town = town,
            state = state,
            
        )
        address.save()
       


        return redirect('app:index')
    else:
        form_data ={
            'user':user.username,
            'house':'', 
           ' street':'', 
            'landmark':'',
            'pincode':'',
           ' town':'',
            'state':'',
        }
        
    content={
        
        
        
        'form_data':form_data,
    }
    return render(request,'userauth/add_address.html',content)

def search_view(request):
    query = request.GET.get("q")
    print("Received query:", query)  # Debug print
    products = Product.objects.filter(Q(title__icontains=query) | Q(descriptions__icontains=query)|Q(specifications__icontains=query)).order_by('-date')
    products_count=products.count()
    print("Matching products:")  # Debug print
    for p in products:
        print(p.title, "\n\n\n")  # Debug print
    context = {
        'products': products,
        'query': query,
        'count':products_count
    }
    return render(request, 'app/search.html', context)




def filter(request):
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    character = AnimeCharacter.objects.all()

    context ={
        'categories':categories,
        'animes':animes,
        'characters':character,
    }
    return render(request,'app/filter.html',context)


def whishlist(request):
    wishlist_items = WishList.objects.filter(user=request.user.id)
    
    context = {
        'wishlist_items': wishlist_items,
    }

    return render(request, 'app/wishlist.html', context)


def add_to_wishlist(request, pid):
    user = request.user
    product = Product.objects.get(pid=pid)
    wishlist, created = WishList.objects.get_or_create(user=user)
    wishlist.products.add(product)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_from_wishlist(request, pid):
    user = request.user
    product = Product.objects.get(pid=pid)
    wishlist = WishList.objects.get(user=user)
    wishlist.products.remove(product)
    return redirect('app:wishlist')

# def add_to_cart(request):
#     cart_product = {}
#     cart_product[str(request.GET['id'])] = {
#         'title': request.GET['title'],
#         'qty': request.GET['qty'],
#         'price': request.GET['price'],
#         'image': request.GET['image'],
#         'pid': request.GET['pid'],
#     }

#     if 'cart_data_obj' in request.session:
#         if str(request.GET['id']) in request.session['cart_data_obj']:
#             cart_data = request.session['cart_data_obj']
#             cart_data[str(request.GET['id'])]['qty'] = int(cart_product[str(request.GET['id'])]['qty'])
#             cart_data.update(cart_data)
#             request.session['cart_data_obj'] = cart_data
#         else:
#             cart_data = request.session['cart_data_obj']
#             cart_data.update(cart_product)
#             request.session['cart_data_obj'] = cart_data

#     else:
#         request.session['cart_data_obj'] = cart_product
#     return JsonResponse({"data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj'])})

 
# def cart_view(request):
#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         print('this is arat cart view ', request.session['cart_data_obj'])
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
#             return render(request,'app/cart.html',{"cart_data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount})
        
#     else:
#         messages.warning(request,'cart is empty')
#         return render(request,'app/index.html')



        
# <_____________________________----------------------------__________________________>

# def delete_item_from_cart(request):
#     product_id = str(request.GET('id'))
#     if 'cart_data_obj' in request.session:
#         if product_id in request.session['cart_data_obj']:
#            cart_data = request.session['cart_data_obj']
#            del request.session['cart_data_obj'][product_id]
#            request.session['cart_data_obj'] = cart_data

#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         for p_id, item in request.session['cart_data_obj'].items():
#             cart_total_amount += int(item['qty'])* float(item['price'])

#         request.session['cart_data_obj']=cart_data
#     context = render_to_string("app/async/cart-list.html",{"cart_data":request.session['cart_data_obj'],'totalcartitems':len(request.session['cart_data_obj']),'cart_total_amount':cart_total_amount})
#     return JsonResponse({"data":context,'totalcartitems':len(request.session['cart_data_obj'])})


# <_______________________________________________________________________________________________>




# def delete_item_from_cart(request):
#     product_id = str(request.GET['id'])
#     print(product_id, 'adfad\n\n\n', request.session['cart_data_obj'][product_id])
#     if 'cart_data_obj' in request.session:
#         if product_id in request.session['cart_data_obj']:
#             del request.session['cart_data_obj'][product_id]
#             print(request.session['cart_data_obj'])

#     cart_total_amount = 0
#     if 'cart_data_obj' in request.session:
#         cart_data = request.session['cart_data_obj']
#         for p_id, item in cart_data.items():
#             cart_total_amount += int(item['qty']) * float(item['price'])
#     print(cart_data, '\n\n there\n', request.session['cart_data_obj'])

#     context = {"cart_data": cart_data, 'totalcartitems': len(cart_data), 'cart_total_amount': cart_total_amount, 'totalcartitems': len(cart_data)}
#     return JsonResponse(context,)

# def checkout(request):
#     cart_total_amount=0
#     if 'cart_data_obj' is request.session:
#         for p_id,item is 

#     return render(request,'app/checkout.html')