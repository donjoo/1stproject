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
from django.http import HttpResponseBadRequest
from django.db.models import OuterRef, Subquery
from decimal import Decimal
from django.db.models import Avg, Count
from orders.models import ProductRating
from .forms import ProductRatingForm
# Create your views here.
current_date = datetime.date.today()



def out_of_stock_products():
    products_out_of_stock = []
    products = Product.objects.filter(delete='False')

    for product in products:
        variants = Variants.objects.filter(product=product,delete='False')
        out_of_stock = True

        for variant in variants:
            stocks = Stock.objects.filter(variant=variant)
            
            for stock in stocks:
                if stock.stock > 0:
                    out_of_stock = False
                    break

        if out_of_stock:
            products_out_of_stock.append(product)
    return products_out_of_stock


def index(request):
    products = Product.objects.filter(delete='False').order_by('-date')
    categories = Category.objects.filter(delete='False') 

   

    # Get wishlist product IDs for authenticated users
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist = WishList.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_product_ids = list(wishlist.products.values_list('id', flat=True))
    else:
        # For guest users (session-based wishlist)
        wishlist_pids = request.session.get('wishlist', [])
        wishlist_product_ids = list(Product.objects.filter(pid__in=wishlist_pids).values_list('id', flat=True))


    # Define a subquery to get the ID of the first offer for each product
    first_offer_subquery = ProductOffer.objects.filter(delete='False',
        product=OuterRef('product'), 
        start_date__lte=current_date,
        end_date__gte=current_date
    ).order_by('-discount').values('id')[:1]

    # Query to retrieve the first offer of each product
    offers = ProductOffer.objects.filter(
        id__in=Subquery(first_offer_subquery)
    ).order_by('product')  # Optionally, you can order the offers by product

    
    paginator = Paginator(products,9)
    page = request.GET.get('page')
    paged_products = paginator.get_page(page)
    out_of_stock_product = out_of_stock_products()
    context = {
        "products":paged_products,   
        "offers":offers,
        "categories":categories,
        "out_of_stock_products":out_of_stock_product,
        "wishlist_product_ids": wishlist_product_ids,  # 👈 Added this
    }
    return render(request,'app/index.html',context)




# def category_product_list(request,cid):
#     category = Category.objects.get(cid=cid)
#     categories = Category.objects.filter(delete='False')
#     animes = CategoryAnime.objects.filter(delete='False')
#     character = AnimeCharacter.objects.filter(delete='False')


#     product = Product.objects.filter(status='True', category=category,delete='False')
    
#     p=Paginator(product,8)
#     page = request.GET.get('page')
#     products=p.get_page(page)

#     context = {
#         "category":category,
#         "products":products,
#         'categories':categories,
#         'animes':animes,
#         'characters':character,
#     }
#     return render(request,"app/shop-filter.html",context)

# def Anime_product_list(request,aid):
#     anime = CategoryAnime.objects.get(aid=aid)
#     categories = Category.objects.filter(delete='False')
#     animes = CategoryAnime.objects.filter(delete='False')
#     character = AnimeCharacter.objects.filter(delete='False')

 
#     product = Product.objects.filter(status='True', anime=anime,delete='False')

#     p=Paginator(product,8)
#     page = request.GET.get('page')
#     products=p.get_page(page)
     
#     context = {
#         "products":products,
#         'categories':categories,
#         'animes':animes,
#         'characters':character, 
#     }
#     return render(request,"app/shop-filter.html",context)


# def Character_product_list(request,lid):
#     character = AnimeCharacter.objects.get(lid=lid)
#     categories = Category.objects.filter(delete='False')
#     animes = CategoryAnime.objects.filter(delete='False')
#     characters = AnimeCharacter.objects.filter(delete='False')

 
#     product = Product.objects.filter(status='True', character=character,delete='False')

#     p=Paginator(product,8)
#     page = request.GET.get('page')
#     products=p.get_page(page)
     
#     context = {
       
#         "products":products,
#         'categories':categories,
#         'animes':animes,
#         'characters':characters,
#     }
#     return render(request,"app/shop-filter.html",context)



def shop(request):
    """Updated shop view to use the same filter functionality"""
    return filter_view(request)


def category_product_list(request, cid):
    """Redirect to filter view with category pre-selected"""
    return redirect(f'/filter/?category={cid}')


def Anime_product_list(request, aid):
    """Redirect to filter view with anime pre-selected"""
    return redirect(f'/filter/?anime={aid}')


def Character_product_list(request, lid):
    """Redirect to filter view with character pre-selected"""
    return redirect(f'/filter/?character={lid}')
















def product_detail(request, pid):
    try:
        product = get_object_or_404(Product, pid=pid)
        in_cart = CartItem.objects.filter(cart__cart_id=_cart_id(request), product=product).exists()
        offer = get_highest_discount_offer(product)
    except Product.DoesNotExist:
        messages.warning(request, 'Product does not exist')
        return redirect("app:index")
    
    p_image = product.p_images.all()
    sizes = Variants.objects.filter(product=product,delete='False')

    # Check if product is already in wishlist
    in_wishlist = False
    if request.user.is_authenticated:
        wishlist = WishList.objects.filter(user=request.user).first()
        if wishlist and product in wishlist.products.all():
            in_wishlist = True
    else:
        wishlist_pids = request.session.get('wishlist', [])
        if pid in wishlist_pids:
            in_wishlist = True


    # Passing pid to is_size_out_of_stock function
    sizes_out_of_stock = {size.size: is_size_out_of_stock(pid, size.size) for size in sizes}
    all_sizes_out_of_stock = all(sizes_out_of_stock.values())
    avg_rating = ProductRating.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg'] or 0
    rounded_rating = round(avg_rating)

    # Get ratings and reviews with pagination
    ratings = ProductRating.objects.filter(product=product).order_by('-created_at')
    paginator = Paginator(ratings, 5)  # 5 reviews per page
    page = request.GET.get('page')
    ratings_page = paginator.get_page(page)
    
    # Calculate star count breakdown
    star_counts = {}
    star_percentages = {}
    total_reviews = ProductRating.objects.filter(product=product).count()
    
    for i in range(1, 6):
        count = ProductRating.objects.filter(product=product, rating=i).count()
        star_counts[i] = count
        if total_reviews > 0:
            star_percentages[i] = round((count / total_reviews) * 100)
        else:
            star_percentages[i] = 0

    # Check if user has already rated this product
    user_rating = None
    can_rate = False
    if request.user.is_authenticated:
        try:
            user_rating = ProductRating.objects.get(user=request.user, product=product)
        except ProductRating.DoesNotExist:
            user_rating = None
        
        # Check if user can rate (has purchased and product is delivered)
        if not user_rating:  # Only if user hasn't rated yet
            # Check if user has purchased this product and it's delivered
            from orders.models import Order, OrderProduct
            delivered_orders = Order.objects.filter(
                user=request.user,
                status='Delivered'
            )
            for order in delivered_orders:
                if OrderProduct.objects.filter(
                    order=order,
                    product=product,
                    ordered=True
                ).exists():
                    can_rate = True
                    break

    # Handle rating submission
    if request.method == 'POST' and 'rating_form' in request.POST:
        if request.user.is_authenticated and can_rate:
            form = ProductRatingForm(request.POST)
            if form.is_valid():
                rating = form.save(commit=False)
                rating.user = request.user
                rating.product = product
                rating.save()
                messages.success(request, 'Thank you for your rating!')
                return redirect('app:product_detail', pid=product.pid)
            else:
                messages.error(request, 'Please fill in all required fields.')
        elif not request.user.is_authenticated:
            messages.error(request, 'Please login to rate this product.')
        else:
            messages.error(request, 'You can only rate products you have purchased and received.')
    else:
        form = ProductRatingForm()

    context = {
        "product": product,
        "p_image": p_image,
        'in_cart': in_cart,
        'sizes': sizes,
        "offer": offer,
        "sizes_out_of_stock": sizes_out_of_stock,
        "all_sizes_out_of_stock":all_sizes_out_of_stock,
        "in_wishlist": in_wishlist,  # 👈 Add this
        "avg_rating": rounded_rating,
        "ratings": ratings_page,
        "form": form,
        "user_rating": user_rating,
        "star_counts": star_counts,
        "star_percentages": star_percentages,
        "can_rate": can_rate,
    }

    return render(request, 'app/product_detail.html', context)


def get_highest_discount_offer(product):
    offer = ProductOffer.objects.filter(
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now(),
        product=product,
        delete='False'
    ).order_by('-discount').first()
    
    return offer

def is_size_out_of_stock(pid, size):
    try:
        product = Product.objects.get(pid=pid)
        variant = Variants.objects.get(product=product, size=size,delete='False')
        stock = Stock.objects.get(variant=variant)
        return stock.stock <= 0
    except (Product.DoesNotExist, Variants.DoesNotExist, Stock.DoesNotExist):
        return True

@login_required(login_url='userauth:handel_login')
def add_address(request):
    if not request.user.is_authenticated:
        return redirect('userauth:handel_login')
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
       

        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'address': {
                    'id': address.id,
                    'user': address.user.username,
                    'house': address.house,
                    'street': address.street,
                    'landmark': address.landmark,
                    'pincode': address.pincode,
                    'town': address.town,
                    'state': address.state,
                }
            }, status=201)


        return redirect('userauth:user_profile')
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
    product = Product.objects.filter(Q(title__icontains=query) | Q(descriptions__icontains=query)|Q(specifications__icontains=query),delete='False').order_by('-date')
    product_count=product.count()

    p=Paginator(product,8)
    page = request.GET.get('page')
    products=p.get_page(page)

    context = {
        'products': products,
        'query': query,
        'count':product_count
    } 
    return render(request, 'app/search.html', context) 




def filter_view(request):
    """
    Enhanced filter view with parallel filtering support
    Users can select multiple categories, anime, characters, price ranges, and sizes
    """
    # Get all filter parameters
    categories_selected = request.GET.getlist('category')
    animes_selected = request.GET.getlist('anime')
    characters_selected = request.GET.getlist('character')
    sizes_selected = request.GET.getlist('size')
    price_range = request.GET.get('price_range', '').strip()
    sort_by = request.GET.get('sort_by', '')

    # Parse price range
    min_price = ''
    max_price = ''
    if price_range and '-' in price_range:
        try:
            parts = price_range.split('-')
            min_price = parts[0].strip()
            max_price = parts[1].strip()
        except:
            pass

    # Start with all active products
    products = Product.objects.filter(delete='False', status='True')

    # Apply category filter (OR condition within categories)
    if categories_selected:
        products = products.filter(category__cid__in=categories_selected)

    # Apply anime filter (OR condition within anime)
    if animes_selected:
        products = products.filter(anime__aid__in=animes_selected)

    # Apply character filter (OR condition within characters)
    if characters_selected:
        products = products.filter(character__lid__in=characters_selected)

    # Apply price range filter
    if min_price and max_price:
        try:
            min_price_val = float(min_price)
            max_price_val = float(max_price)
            products = products.filter(price__gte=min_price_val, price__lte=max_price_val)
        except (ValueError, TypeError):
            # Invalid price values, skip filter
            min_price = ''
            max_price = ''

    # Apply size filter (products that have variants with selected sizes)
    if sizes_selected:
        # Filter for products that have at least one variant with the selected sizes
        from django.db.models import Q
        size_query = Q()
        for size in sizes_selected:
            size_query |= Q(variants__size__iexact=size, variants__delete='False')
        
        products = products.filter(size_query).distinct()

    # Apply sorting
    if sort_by == 'price_low_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_low':
        products = products.order_by('-price')
    else:
        products = products.order_by('-date')

    # Remove duplicates
    products = products.distinct()

    # Get all filter options
    categories = Category.objects.filter(delete='False')
    animes = CategoryAnime.objects.filter(delete='False')
    characters = AnimeCharacter.objects.filter(delete='False')
    
    # Get offers
    first_offer_subquery = ProductOffer.objects.filter(
        delete='False',
        product=OuterRef('product'), 
        start_date__lte=current_date,
        end_date__gte=current_date
    ).order_by('-discount').values('id')[:1]

    offers = ProductOffer.objects.filter(
        id__in=Subquery(first_offer_subquery)
    ).order_by('product')

    # Pagination
    paginator = Paginator(products, 12)
    page = request.GET.get('page')
    products_paginated = paginator.get_page(page)

    # Get out of stock products
    out_of_stock_product = out_of_stock_products()

    # Get wishlist product IDs for authenticated users
    wishlist_product_ids = []
    if request.user.is_authenticated:
        wishlist = WishList.objects.filter(user=request.user).first()
        if wishlist:
            wishlist_product_ids = list(wishlist.products.values_list('id', flat=True))
    else:
        # For guest users (session-based wishlist)
        wishlist_pids = request.session.get('wishlist', [])
        wishlist_product_ids = list(Product.objects.filter(pid__in=wishlist_pids).values_list('id', flat=True))


    context = {
        'products': products_paginated,
        'productss': products_paginated,  # For pagination template compatibility
        'categories': categories,
        'animes': animes,
        'characters': characters,
        'offers': offers,
        'out_of_stock_products': out_of_stock_product,
        # Selected filters for maintaining state
        'categories_selected': categories_selected,
        'animes_selected': animes_selected,
        'characters_selected': characters_selected,
        'sizes_selected': sizes_selected,
        'min_price': min_price,
        'max_price': max_price,
        'sort_by': sort_by,
        # Available sizes
        'available_sizes': ['S', 'M', 'L', 'XL', 'XXL'],
        "wishlist_product_ids": wishlist_product_ids, 

    }
    
    return render(request, 'app/shop-filter.html', context)



def wishlist(request):
    products = []

    if request.user.is_authenticated:
        wishlist_items = WishList.objects.filter(user=request.user).first()
        if wishlist_items:
            products = wishlist_items.products.all()
    else:
        # wishlist_items = []
        wishlist_pids = request.session.get('wishlist', [])
        if wishlist_pids:
            products = Product.objects.filter(pid__in=wishlist_pids)
        # products = Product.objects.filter(pid__in=wishlist_pids)
        # wishlist_items.append({'products': products})

    # products = []
    # for item in wishlist_items:
    #         products = item.products.all()


    paginator = Paginator(products, 3)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    out_of_stock_product = out_of_stock_products()

    context = {
        'wishlist_items':page_obj,
        "out_of_stock_products":out_of_stock_product,

    }

    return render(request, 'app/wishlist.html', context)


def add_to_wishlist(request, pid):
    product = Product.objects.filter(pid=pid).first()
    if not product:
        # Handle case where product does not exist
        return HttpResponseBadRequest("Product does not exist")

    if request.user.is_authenticated:
        # For authenticated users, add the product to their wishlist
        wishlist, created = WishList.objects.get_or_create(user=request.user)
        wishlist.products.add(product)
    else:
        # For anonymous users, add the product to their session-based wishlist
        wishlist_id = _wishlist_id(request)
        wishlist_pids = request.session.get('wishlist', [])
        if pid not in wishlist_pids:
            wishlist_pids.append(pid)
            request.session['wishlist'] = wishlist_pids
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


def remove_from_wishlist(request, pid):
    product = Product.objects.filter(pid=pid).first()
    if not product:
        # Handle case where product does not exist
        return HttpResponseBadRequest("Product does not exist")

    if request.user.is_authenticated:
        # For authenticated users, remove the product from their wishlist
        wishlist = WishList.objects.filter(user=request.user).first()
        if wishlist:
            wishlist.products.remove(product)
    else:
        # For anonymous users, remove the product from their session-based wishlist
        wishlist_pids = request.session.get('wishlist', [])
        if pid in wishlist_pids:
            wishlist_pids.remove(pid)
            request.session['wishlist'] = wishlist_pids

    return redirect('app:wishlist')


def _wishlist_id(request):
    wishlist = request.session.session_key
    if not wishlist:
        wishlist = request.session.create()
    return wishlist


# def shop(request):
#     product = Product.objects.filter(delete='False').order_by('-date')
#     categories = Category.objects.filter(delete='False')
#     animes = CategoryAnime.objects.filter(delete='False')
#     character = AnimeCharacter.objects.filter(delete='False')

#     p=Paginator(product,8)
#     page = request.GET.get('page')
#     products=p.get_page(page)

#     context = {
#         'categories':categories,
#         'animes':animes,
#         'characters':character, 
#         'products':products
#     }
#     return render(request,"app/shop-filter.html",context)

def sort_by(request):
    sort_by = request.GET.get('sort_by')
    product_ids_string = request.GET.get('products')
    product_ids = product_ids_string.split(',') if product_ids_string else []  # Split the string into a list of IDs
    # Convert the list of IDs to integers
    product_ids = [int(id) for id in product_ids if id.isdigit()]
    # Filter products based on the received IDs
    product = Product.objects.filter(id__in=product_ids)
    
    if sort_by == 'price_low_high':
        product = product.order_by('price')
    elif sort_by == 'price_high_low':
        product = product.order_by('-price')
    elif sort_by == 'release_date':
        product = product.order_by('release_date')
    
    categories = Category.objects.filter(delete='False')
    animes = CategoryAnime.objects.filter(delete='False')
    characters = AnimeCharacter.objects.all()


    p=Paginator(product,8)
    page = request.GET.get('page')
    products=p.get_page(page)


    context = {
        'products': products,
        'categories': categories,
        'animes': animes,
        'characters': characters,
    }
    return render(request, 'app/shop-filter.html', context)




def get_sizes(request, pid):
    variants = Variants.objects.filter(
        product__pid=pid, 
        is_active=True, 
        delete=False
    ).select_related()
    
    sizes_data = []
    for variant in variants:
        try:
            stock = Stock.objects.get(variant=variant)
            stock_count = stock.stock
        except Stock.DoesNotExist:
            stock_count = 0
        
        sizes_data.append({
            'id': variant.id,
            'size': variant.size,
            'stock': stock_count,
            'in_stock': stock_count > 0
        })
    
    return JsonResponse({'sizes': sizes_data})