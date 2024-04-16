from django.shortcuts import render,HttpResponse,redirect,get_object_or_404,HttpResponseRedirect
from app.models import Product,ProductImage,Category,CategoryAnime,AnimeCharacter,Variants,WishList,ProductOffer,Stock
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
import datetime
from django.utils import timezone


# Create your views here.
current_date = datetime.date.today()



def out_of_stock_products():
    products_out_of_stock = []
    products = Product.objects.all()

    for product in products:
        variants = Variants.objects.filter(product=product)
        out_of_stock = True

        for variant in variants:
            stocks = Stock.objects.filter(variant=variant)
            
            for stock in stocks:
                if stock.stock > 0:
                    out_of_stock = False
                    break

        if out_of_stock:
            products_out_of_stock.append(product)
    print(products_out_of_stock)
    return products_out_of_stock



def index(request):
    products = Product.objects.all().order_by('-date')
    categories = Category.objects.all() 
    offers = ProductOffer.objects.filter(start_date__lte=current_date, end_date__gte=current_date)

    paginator = Paginator(products,9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    out_of_stock_product = out_of_stock_products()
    print(out_of_stock_product)
    context = {
        "products":paged_products,   
        "offers":offers,
        "categories":categories,
        "out_of_stock_products":out_of_stock_product
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
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    character = AnimeCharacter.objects.all()


    products = Product.objects.filter(status='True', category=category)
     
    context = {
        "category":category,
        "products":products,
        'categories':categories,
        'animes':animes,
        'characters':character,
    }
    return render(request,"app/shop-filter.html",context)

def Anime_product_list(request,aid):
    anime = CategoryAnime.objects.get(aid=aid)
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    character = AnimeCharacter.objects.all()

 
    products = Product.objects.filter(status='True', anime=anime)
     
    context = {
        "products":products,
        'categories':categories,
        'animes':animes,
        'characters':character, 
    }
    return render(request,"app/shop-filter.html",context)


def Character_product_list(request,lid):
    character = AnimeCharacter.objects.get(lid=lid)
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    characters = AnimeCharacter.objects.all()

 
    products = Product.objects.filter(status='True', character=character)
     
    context = {
       
        "products":products,
        'categories':categories,
        'animes':animes,
        'characters':characters,
    }
    return render(request,"app/shop-filter.html",context)

def product_detail(request, pid):
    try:
        product = get_object_or_404(Product, pid=pid)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
        offers = ProductOffer.objects.filter(start_date__lte=timezone.now(), end_date__gte=timezone.now(), product=product)
    except Product.DoesNotExist:
        messages.warning(request, 'Product does not exist')
        return redirect("app:index")
    
    p_image = product.p_images.all()
    sizes = Variants.objects.filter(product=product)

    # Passing pid to is_size_out_of_stock function
    sizes_out_of_stock = {size.size: is_size_out_of_stock(pid, size.size) for size in sizes}
    all_sizes_out_of_stock = all(sizes_out_of_stock.values())
     
    for size in sizes:
       print(sizes_out_of_stock[size.size])
    context = {
        "product": product,
        "p_image": p_image,
        'in_cart': in_cart,
        'sizes': sizes,
        "offers": offers,
        "sizes_out_of_stock": sizes_out_of_stock,
        "all_sizes_out_of_stock":all_sizes_out_of_stock
    }

    return render(request, 'app/product_detail.html', context)

def is_size_out_of_stock(pid, size):
    try:
        product = Product.objects.get(pid=pid)
        variant = Variants.objects.get(product=product, size=size)
        stock = Stock.objects.get(variant=variant)
        return stock.stock <= 0
    except (Product.DoesNotExist, Variants.DoesNotExist, Stock.DoesNotExist):
        return True

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



def filter_view(request):
    print('heklpppppppppppppppppppppppppppppppppp')
    min_price = request.GET.get('min_price')
    max_price = request.GET.get('max_price')
    size = request.GET.get('size')
    # print('size')

    # Filter products based on price range
    if min_price and max_price:
        products = Product.objects.filter(price__gte=min_price, price__lte=max_price)
    else:
        products = Product.objects.all()

    # Filter products based on size
    if size:
         products = products.filter(variants__size__iexact=size)

    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    character = AnimeCharacter.objects.all()

    context ={
        'products': products,
        'categories':categories,
        'animes':animes,
        'characters':character, 
        
    }
    return render(request,'app/shop-filter.html',context)


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

def shop(request):
    products = Product.objects.all()
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    character = AnimeCharacter.objects.all()

    context = {
        'categories':categories,
        'animes':animes,
        'characters':character, 
        'products':products
    }
    return render(request,"app/shop-filter.html",context)

from django.http import HttpResponse
from django.shortcuts import render
from .models import Product, Category, CategoryAnime, AnimeCharacter

def sort_by(request):
    sort_by = request.GET.get('sort_by')
    product_ids_string = request.GET.get('products')
    print(product_ids_string)  # Get the comma-separated string of product IDs
    product_ids = product_ids_string.split(',') if product_ids_string else []  # Split the string into a list of IDs
    print(product_ids)
    # Convert the list of IDs to integers
    product_ids = [int(id) for id in product_ids if id.isdigit()]
    print(product_ids,'huvuwebvuyw')
    # Filter products based on the received IDs
    products = Product.objects.filter(id__in=product_ids)
    
    if sort_by == 'price_low_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-price')
    elif sort_by == 'release_date':
        products = products.order_by('release_date')
    
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    characters = AnimeCharacter.objects.all()

    context = {
        'products': products,
        'categories': categories,
        'animes': animes,
        'characters': characters,
    }
    return render(request, 'app/shop-filter.html', context)



def about(request):
    return render(request,"app/about.html")