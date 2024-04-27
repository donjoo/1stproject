from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from userauth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.cache import cache_control
from app.models import Product,Category,ProductImage,ProductVariants,CategoryAnime,AnimeCharacter,Variants,Stock,Coupon,ProductOffer,CategoryOffer,Transaction,ProductOffer
from django.core.paginator import Paginator
from .forms import CreateProductForm,ProductVariantForm,CouponForm,ProductOfferForm,CategoryOfferForm
from django.http import Http404
from django.http import JsonResponse
from orders.models import Order,OrderProduct,Payment
from datetime import datetime,date,timedelta
from django.utils import timezone
import os
from django.conf import settings
from django.db.models import Sum
from django.utils.timezone import now
from django.db.models import Count
from django.db.models.functions import TruncMonth,TruncYear
current_date = timezone.now()   


def new(request):
    return render(request,'adminside/new.html')


@login_required(login_url='adminside:admin_login')
def admin_index(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    best_selling_products = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__title').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]

    best_selling_categories = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__category__title').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]
    
    best_selling_characters = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__character__name').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]
    

    orders = Order.objects.all().order_by('-created_at')
    # dates = [order.created_at for order in orders]
    # dates = [order.created_at.strftime('%Y.%m.%d') for order in orders]  # Format dates using strftime

    amounts = [order.order_total for order in orders]

    orderss = Order.objects.all().order_by('-created_at').exclude(status='Cancelled').exclude(status='Returned')[:6]
    revenue = calculate_revenue(request)
    product_count = Product.objects.filter(status='True')
    product_count = product_count.count
    category_count = Category.objects.filter(is_blocked='False')
    category_count = category_count.count
    order_count = Order.objects.filter(status='Delivered')
    order_count = order_count.count
    mothly_earnings =  calculate_average_earnings_per_month(request)


    end_date = timezone.now()
    start_date = end_date - timedelta(days=7)


    daily_order_counts = (
            Order.objects
            .filter(created_at__range=(start_date, end_date))
            .values('created_at')
            .annotate(order_count=Count('id'))
            .order_by('created_at')
        )
    print(f'daily orrderr {daily_order_counts}')
    print('SQL Query:', daily_order_counts.query)
    dates = [entry['created_at'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]
    print('Daily Chart Data:')
    print('Dates:', [entry['created_at'] for entry in daily_order_counts])
    print('Counts:', [entry['order_count'] for entry in daily_order_counts])
    print(dates)
    print(counts)


    end_date = timezone.now()
    start_date = end_date - timedelta(days=365) 
    
    monthly_order_counts = (
        Order.objects
        .filter(created_at__range=(start_date, end_date))   
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(order_count=Count('id'))
        .order_by('month')
    )
    monthlyDates = [entry['month'].strftime('%Y-%m') for entry in monthly_order_counts]
    monthlyCounts = [entry['order_count'] for entry in monthly_order_counts]
    
    yearly_order_counts = (
        Order.objects
        .annotate(year=TruncYear('created_at'))
        .values('year')
        .annotate(order_count=Count('id'))
        .order_by('year')
    )
    yearlyDates = [entry['year'].strftime('%Y') for entry in yearly_order_counts]
    yearlyCounts = [entry['order_count'] for entry in yearly_order_counts]

    statuses = ['Delivered','Paid','Pending', 'New', 'Conformed', 'Cancelled', 'Returned','Shipped']
    order_counts = [Order.objects.filter(status=status).count() for status in statuses]
    context = {
        'statuses':statuses,
        'order_counts':order_counts,
        'orders':orderss,
        # 'dates':dates,
        'revenue':revenue,
        'product_count':product_count,
        'category_count':category_count,
        'order_count':order_count,
        'mothly_earnings':mothly_earnings,
        'dates':dates,
        'counts':counts,
        'yearlyDates':yearlyDates,
        'yearlyCounts':yearlyCounts,
        'monthlyDates':monthlyDates,
        'monthlyCounts':monthlyCounts,
        # 'amounts':amounts,
        'best_selling_products':best_selling_products,
        'best_selling_categories':best_selling_categories,
        'best_selling_characters':best_selling_characters,

    }
    return render(request,'adminside/admin_index.html',context)


def calculate_revenue(request):
    orders = Order.objects.all().exclude(status ='Cancelled').exclude(status = 'Returned')
    revenue = 0
    for order in orders:
        products = OrderProduct.objects.filter(order = order)
        for item in products:
            revenue += item.product_price * item.quantity
    print(revenue)
    return revenue


def calculate_monthly_revenue(year, month):
    current_date = datetime.now()
    # year = current_date.year
    # month = current_date.month

    total_earnings = 0
    orders = Order.objects.filter(created_at__year = year,created_at__month = month).exclude(status = 'Cancelled').exclude(status = 'Returned')
    for order in orders:
        order_products = OrderProduct.objects.filter(order = order)
        for item in order_products:
            total_earnings += item.product_price * item.quantity
    return total_earnings

def calculate_average_earnings_per_month(request):
    # Get the current year and month
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    # Initialize variables to store total earnings and the number of months
    total_earnings = 0
    num_months = 0
    
    # Loop through each month of the current year
    for month in range(1, current_month + 1):
        # Calculate earnings for the current month
        earnings = calculate_monthly_revenue(current_year, month)
        
        # Add earnings to total earnings
        total_earnings += earnings
        
        # Increment the number of months
        num_months += 1
    
    # Calculate the average earnings per month
    if num_months > 0:
        average_earnings_per_month = total_earnings / num_months
        return average_earnings_per_month
    else:
        return 0

def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superadmin:
            return redirect('adminside:admin_index')
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        print(email,password)
        user = authenticate(request,email=email,password=password)
        print(user)
        if user:
            if user.is_authenticated:
                login(request,user)
                return redirect('adminside:admin_index')
            messages.error(request,"invalid admin credentials!")
    return render(request,'adminside/admin_login.html')


def admin_logout(request):
    logout(request)
    return redirect('adminside:admin_login')




'''-----Admin Dasboard--------'''


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def user_management(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    query = request.GET.get('q')
    if query:
        datas = User.objects.filter(
            Q(username__icontains=query)|Q(email__icontains=query)
        ).order_by('-date_joined')
    else:
        datas = User.objects.all().order_by('-date_joined')

    p=Paginator(datas,10)
    page = request.GET.get('page')  
    data=p.get_page(page)

    context={"data": data, "search_query":query}
    return render(request,'adminside/user_management.html',context)

@login_required(login_url='adminside:admin_login')
def block_unblock(request,user_id):
    if not request.user.is_authenticated:
        return HttpResponse("Unauthorized", status=401)
    user = get_object_or_404(User,id=user_id)

    if user.is_active:
        user.is_active=False
    else:
        user.is_active=True

    user.save()
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))


         #PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT
         #PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT
         #PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT
         #PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT#PRODUCTMANAGEMENT


@login_required(login_url='adminside:admin_login')
def add_product(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    characters = AnimeCharacter.objects.all()

    if request.method == 'POST':
        product_name = request.POST.get('name')
        description = request.POST.get('describtion')
        max_price = request.POST.get('old_price')
        sale_price = request.POST.get('price')
        category_name = request.POST.get('category')
        anime_name = request.POST.get('anime')
        character_name = request.POST.get('character')
        fit = request.POST.get('fit')
        fabric = request.POST.get('fabric')
        care = request.POST.get('care')
        sleeve = request.POST.get('sleeve')
        collar = request.POST.get('collar')
        specifications=request.POST.get('specifications')
        
        

        validation_errors = []

        if not product_name.strip():
            validation_errors = ["Title is required."]

        image_file = request.FILES.get('image_field')
        if image_file:
            if not is_valid_image(image_file):
                validation_errors.append("Invalid image file format. Only image files are allowed.")
        
        try:
            max_price = float(max_price)
            if max_price < 0:
                validation_errors.append("Max price must be a positive number")

            sale_price=float(sale_price)
            if sale_price < 0:
                validation_errors.append("Sale price must be a positive number")
        except ValueError as e:
            validation_errors.append(str(e))
        if validation_errors:
            form_data = {
                'name':product_name,
                'description':description,
                'old_price':max_price,
                'price':sale_price,
                'category':category_name,
                'anime':anime_name,
                'character':character_name,
                'fit': fit,
                'fabric': fabric,
                'care': care,
                'sleeve': sleeve,
                'collar': collar,
                'specifications':specifications
            }
            content ={
                'categories':categories,
                'animes':animes,
                'characters':characters,
                'additional_image-count':range(1,4),
                'error_messages':validation_errors,
                'form_data':form_data,

            } 
            return render(request,'adminside/add_product.html',content)
        

        
        category = get_object_or_404(Category, title=category_name)
        print(category)
        anime = get_object_or_404(CategoryAnime, title=anime_name)
        print(anime)
        character = get_object_or_404(AnimeCharacter, name=character_name)
        print(character)
    
        product = Product(
            title=product_name,
            category=category,
            anime=anime,
            character=character,
            descriptions=description,
            specifications=specifications,
            old_price=max_price,
            price=sale_price,
            fit=fit,
            fabric=fabric,
            care=care,
            sleeve=sleeve,
            collar=collar,
            image=request.FILES.get('image_field')
        )
        product.save()
        additional_image_count = 5
        for i in range(1,additional_image_count+1):
            image_field = f'product_image{i}'
            image= request.FILES.get(image_field)
            if image:
                ProductImage.objects.create(product=product,Images=image)


        return redirect('adminside:product_list')
    else:
        form_data ={
            'name':'',
            'description':'',
            'specifications':'',
            'old_price':'',
            'price':'',
            'category':'',
            'anime':'',
            'character':'',
            'fit':'',
            'fabric':'' ,
            'care':'',
            'sleeve':'' ,
            'collar':'' ,

        }
        
    content={
        'characters':characters,
        'animes':animes,
        'categories':categories,
        'additional_image_count':range(1,4),
        'form_data':form_data,
    }
    return render(request,'adminside/add_product.html',content)



# def get_characters(request):
#     if request.headers.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest' and request.method == 'GET':
#         print('heyyhyhvy')
#         anime_id = request.GET.get('aid')
#         characters = AnimeCharacter.objects.filter(animename_id=anime_id).values('id', 'name')
#         print("Received anime ID:", anime_id)
#         print("Characters:", characters)
#         return JsonResponse(list(characters), safe=False)
#     else:
#         # Handle invalid requests
#         return JsonResponse({'error': 'Invalid request'})



def delete_product(request,pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    try:
        product=Product.objects.get(pid=pid)
        product.active = False
        product.save()
        return redirect('adminside:product_list')
    except Product.DoesNotExist:
        return HttpResponse("product not Found",status=404)


def is_valid_image(file):
    valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
    ext = os.path.splitext(file.name)[1]
    return ext.lower() in valid_extensions
   
@login_required(login_url='adminside:admin_login')
def product_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    # products = Product.objects.all().order_by('-date') 
    p=Paginator(Product.objects.filter(active='True').order_by('-date'),10)
    page = request.GET.get('page')
    productss=p.get_page(page)

    context = {
        # "products":products,
        "productss":productss
    }
    return render(request,'adminside/products_list.html',context)


def block_unblock_products(request, pid):
    
  if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
  product = get_object_or_404(Product, pid=pid)
  if product.status:
    product.status=False
  else:
      product.status=True
  product.save()
  return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/'))




def product_edit(request, pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')

    product = get_object_or_404(Product, pid=pid)
    p_image = product.p_images.all()
    validation_errors = []
    if request.method == 'POST':
        product.title = request.POST.get('name')
        product.descriptions = request.POST.get('describtion')
        product.old_price = float(request.POST.get('old_price'))
        product.price = float(request.POST.get('price'))
        product.category = get_object_or_404(Category, title=request.POST.get('category'))
        product.anime = get_object_or_404(CategoryAnime, title=request.POST.get('anime'))
        product.character = get_object_or_404(AnimeCharacter, name=request.POST.get('character'))
        product.fit = request.POST.get('fit')
        product.fabric = request.POST.get('fabric')
        product.care = request.POST.get('care')
        product.sleeve = request.POST.get('sleeve')
        product.collar = request.POST.get('collar')
        product.specifications = request.POST.get('specifications')

        # # Handle image upload
        # new_image_file = request.FILES.get('image_field')
        # if new_image_file:
        #     product.image = new_image_file

        # Handle image deletion
        product_name=request.POST.get('name')
        if not product_name.strip():
            validation_errors = ["Title is required."]

        delete_image = request.POST.get('delete_image')
        if delete_image == 'on':
            product.image.delete()
            product.image = None
        
        for image in product.p_images.all():
            delete_checkbox_name = f'delete_image_{image.id}'
            replace_file_name = f'replace_image_{image.id}'

            if request.POST.get(delete_checkbox_name)=='on':
                image.Images.delete()
            else:
                replace_image_file = request.FILES.get(replace_file_name)
                if replace_image_file:
                    if not is_valid_image(replace_image_file):
                        validation_errors.append("Invalid image file format. Only image files are allowed.")
                    image.Images = replace_image_file
                    image.save()
        product.save()
        new_image_file = request.FILES.get('image_field')
        if new_image_file:
            if not is_valid_image(new_image_file):
                validation_errors.append("Invalid image file format. Only image files are allowed.")
            product.image = new_image_file
            product.save()


        additional_image_count = 5
        for i in range(1,additional_image_count+1):
            image_field = f'product_image{i}'
            image= request.FILES.get(image_field)
            if image:
                ProductImage.objects.create(product=product,Images=image)


        return redirect('adminside:product_list')

    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    characters = AnimeCharacter.objects.all()

    error_messages = validation_errors
    context = {
        'productt': product,
        'categories': categories,
        'animes': animes,
        'characters': characters,
        'additional_image_count':range(1,3),  
        'error_messages':error_messages,
        'existing_data': {
            'name': product.title,
            'describtion': product.descriptions,
            'old_price': product.old_price,
            'price': product.price,
            'category': product.category.title if product.category else '',
            'anime': product.anime.title if product.anime else '',
            'character': product.character.name if product.character else '',
            'fit': product.fit,
            'fabric': product.fabric,
            'care': product.care,
            'sleeve': product.sleeve,
            'collar': product.collar,
            'specifications': product.specifications,
            'p_image':p_image,
            
        }
    }

    return render(request, 'adminside/product_edit.html', context)

@login_required(login_url='adminside:admin_login')
def products_details(request, pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
   

    try:
        product = Product.objects.get(pid=pid)
        product_images = ProductImage.objects.filter(product=product)
        sizes = Variants.objects.filter(product=product)

        # Passing pid to is_size_out_of_stock function
        sizes_out_of_stock = {size.size: is_size_out_of_stock(pid, size.size) for size in sizes}
        all_sizes_out_of_stock = all(sizes_out_of_stock.values())
        offers = ProductOffer.objects.filter(product=product,start_date__lte = current_date,end_date__gte = current_date)
        # catoffers = CategoryOffer.objects.filter(category = product.anime,start_date__lte = current_date,end_date__gte = current_date)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)
    context = {
        'offers':offers,
        # 'catoffers':catoffers,
        'product': product,
        'product_images': product_images,
        'sizes_out_of_stock':sizes_out_of_stock,
        'all_sizes_out_of_stock':all_sizes_out_of_stock
    }
    return render(request, 'adminside/products_details.html', context)

def is_size_out_of_stock(pid, size):
    try:
        product = Product.objects.get(pid=pid)
        variant = Variants.objects.get(product=product, size=size)
        stock = Stock.objects.get(variant=variant)
        return stock.stock <= 0
    except (Product.DoesNotExist, Variants.DoesNotExist, Stock.DoesNotExist):
        return True


          #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT
          #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT
          #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT
          #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT #CATEGORYMANAGEMENT


@login_required(login_url='adminside:admin_login')
def add_category(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    if request.method == 'POST':
        cat_name = request.POST.get('category_name')
        validation_errors = [] 

        if Category.objects.filter(title=cat_name).exists():
            messages.error(request, 'Category with this name already exists.')

        if not cat_name.strip():
            validation_errors = ["Name is required."]
            context = {
            'messages':validation_errors,
            'category_image':request.FILES.get('category_image')

            }
            return render(request, 'adminside/categories_list.html',context)
        else:
            cat_data = Category(title=cat_name, image=request.FILES.get('category_image'))
            cat_data.save()
            print("yes")
            messages.success(request, 'Category added successfully.')

               
    else:
        
        return render(request, 'adminside/categories_list.html')
    
    return render(request, 'adminside/categories_list.html')


@login_required(login_url='adminside:admin_login')
def category_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    # categories = Category.objects.all()
    p=Paginator(Category.objects.all().order_by('-date'),10)
    page = request.GET.get('page')
    categories=p.get_page(page)
    
    context = {
        'categories':categories
    }   
    return render(request,'adminside/categories_list.html',context)



def category_edit(request,cid):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    categories = get_object_or_404(Category,cid=cid)


    if request.method == 'POST':
        cat_name = request.POST.get("category_name")
        cat_img = request.FILES.get('category_image')


        categories.title =cat_name
        if cat_img is not None:
             categories.image=cat_img 

        categories.save()

       
        return redirect('adminside:category_list')

    
    context = {
        "categories_title": categories.title,
        "categories_image": categories.image,
    }

    return render(request, 'adminside/categories_edit.html', context)


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_category(request,cid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        category = Category.objects.get(cid=cid)
    except ValueError:
        return redirect('adminside:category_list')
    category.delete()

    return redirect('adminside:category_list')
        

def available_category(request,cid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    category=get_object_or_404(Category,cid=cid)

    if category.is_blocked:
        category.is_blocked=False

    else:
        category.is_blocked=True
    category.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

              #ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY
              #ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY
              #ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY
              #ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY#ANIMECATEGORY

@login_required(login_url='adminside:admin_login')
def add_animecat(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    if request.method == 'POST':
        anime_name = request.POST.get('anime_name')


        if not anime_name.strip():
            validation_errors = ["Name is required."]
            p=Paginator(CategoryAnime.objects.all().order_by('-id'),10)
            page = request.GET.get('page')
            Animes=p.get_page(page)
            context = {
                'error_messages':validation_errors,
                'animes':Animes
            }
            return render(request, 'adminside/animecat_list.html',context)


        if CategoryAnime.objects.filter(title=anime_name).exists():
            messages.error(request, 'Category with this name already exists.')
        else:
            anime_data = CategoryAnime(title=anime_name, image=request.FILES.get('anime_image'))
            anime_data.save()
            print("yes")
            messages.success(request, 'Category added successfully.')       
    else:
        return redirect('adminside:animecat_list')
    
    return redirect('adminside:animecat_list')



def animecat_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    
    p=Paginator(CategoryAnime.objects.all().order_by('-id'),10)
    page = request.GET.get('page')
    Animes=p.get_page(page)

    
    context = {
        'animes':Animes
    }   
    return render(request,'adminside/animecat_list.html',context)



def animecat_edit(request,aid):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    animes = get_object_or_404(CategoryAnime,aid=aid)


    if request.method == 'POST':
        anime_name = request.POST.get("anime_name")
        anime_img = request.FILES.get('anime_image')


        animes.title =anime_name
        if anime_img is not None:
             animes.image=anime_img 

        animes.save()

       
        return redirect('adminside:category_list')

    
    context = {
        "categories_title": animes.title,
        "categories_image": animes.image,
    }

    return render(request, 'adminside/categories_edit.html', context)


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_animecat(request,aid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        anime = CategoryAnime.objects.get(aid=aid)
    except ValueError:
        return redirect('adminside:animecat_list')
    anime.delete()

    return redirect('adminside:animecat_list')
        

def available_animecat(request,aid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    anime=get_object_or_404(CategoryAnime,aid=aid)

    if anime.is_blocked:
        anime.is_blocked=False

    else:
        anime.is_blocked=True
    anime.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))




                 # CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER
                 # CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER
                 # CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER
                 # CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER# CATEGORYANIMECHARACTER


     
    


@login_required(login_url='adminside:admin_login')
def add_character(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
      
    
    animes = CategoryAnime.objects.all()
    # anime_instance = get_object_or_404(CategoryAnime, title=anime_name)
    

    if request.method == 'POST':
        
        anime_name = request.POST.get('anime')
        char_name = request.POST.get('char_name')
        if not char_name.strip():
            validation_errors = ["Name is required."]
            p=Paginator( AnimeCharacter.objects.all().order_by('-id'),10)
            page = request.GET.get('page')
            characters=p.get_page(page)
            context = {
                'error_messages':validation_errors,
                'characters':characters,
                'animes':animes,
            }
            return render(request, 'adminside/characters_list.html',context)
        if AnimeCharacter.objects.filter(name=char_name).exists():
            messages.error(request, 'Category with this name already exists.')
        
        else:
            anime_name = get_object_or_404(CategoryAnime, title=anime_name)
            char_data = AnimeCharacter(name=char_name,animename=anime_name ,image=request.FILES.get('char_image'))
            char_data.save()
            print("yes")
            messages.success(request, 'Category added successfully.') 
              
    else:
        
        return redirect('adminside:character_list')
    
    return redirect('adminside:character_list')



def character_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
   
    animes = CategoryAnime.objects.all()
    p=Paginator( AnimeCharacter.objects.all().order_by('-id'),10)
    page = request.GET.get('page')
    characters=p.get_page(page)

    
    context = {
        'characters':characters,
        'animes':animes
    }   
    return render(request,'adminside/characters_list.html',context)

       

def character_edit(request,lid):
    if not request.user.is_authenticated:
        return redirect('adminside:admin_login')
    
    characters = get_object_or_404(AnimeCharacter,lid=lid)


    if request.method == 'POST':
        char_img = request.FILES.get('char_image')
        char_name = request.POST.get("char_name")


        characters.name =char_name
        if char_img is not None:
             characters.image=char_img 

        characters.save()

       
        return redirect('adminside:characters_list')

    
    context = {
        "characters_name": characters.name,
        "characters_image": characters.image,
    }

    return render(request, 'adminside/characters_edit.html', context)


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_character(request,lid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
       character = get_object_or_404(AnimeCharacter, lid=lid)
    except ValueError:
        return redirect('adminside:character_list')
    character.delete()

    return redirect('adminside:character_list')
        

def available_characters(request,lid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    characters = get_object_or_404(AnimeCharacter,lid=lid)

    if characters.is_blocked:
        characters.is_blocked=False

    else:
        characters.is_blocked=True
    characters.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))





              #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS
              #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS
              #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS
              #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS #PRODUCTVARIENTS
                
@login_required(login_url='adminside:admin_login')
def add_newvariant(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    products = Product.objects.all()
    
    if request.method == 'POST':
        print('httttt')
        product_id = request.POST.get('product')  
        size = request.POST.get('size')
        print(product_id,'hyyyyyy')

        # Retrieve product by title
        product = get_object_or_404(Product, pid = product_id)

        if Variants.objects.filter(product=product, size=size).exists():
            messages.error(request, 'Size already exists.')
        else:
            variant = Variants(size=size, product=product)
            variant.save()
            messages.success(request, 'Size added successfully.')

    context = {
        'products': products,
    }
    return render(request, 'adminside/add_newvariant.html', context)


@login_required(login_url='adminside:admin_login')
def newvariant_list(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
        
    products = Product.objects.all()
    selected_product = None
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        selected_product = Product.objects.get(title=product_id)
        variants = Variants.objects.filter(product=selected_product)
    else:
        variants = Variants.objects.all()
        
    paginator = Paginator(variants, 10)
    page_number = request.GET.get('page')
    page_variants = paginator.get_page(page_number)

    context = {
        "products": products,
        "selected_product": selected_product,
        "page_variants": page_variants
    }

    return render(request, 'adminside/variant_list.html', context)


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_size(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        size = Variants.objects.get(id=id)
    except ValueError:
        return redirect('adminside:newvariant_list')
    size.delete()

    return redirect('adminside:newvariant_list')
        

def block_size(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    size=get_object_or_404(Variants,id=id)

    if size.is_active:
        size.is_active=False

    else:
        size.is_active=True
    size.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

 
def add_stock(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    if request.method == 'POST':
        product_id = request.POST.get('product')
        product = get_object_or_404(Product, id=product_id)

        for key, value in request.POST.items():
            if key.startswith('stock-'):
                variant_id = key.split('-')[1]  # Extract the variant ID from the input field name
                variant = get_object_or_404(Variants, id=variant_id, product=product)
                stock, created = Stock.objects.get_or_create(variant=variant)
                stock.stock += int(value)
                stock.save()

        messages.success(request, 'Stock updated successfully.')
        return redirect('adminside:stock_list')

    products = Product.objects.all()
    context = {'products': products}
    return render(request, 'adminside/add_stock.html', context)


def get_variants(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    product_id = request.GET.get('product_id')
    variants = Variants.objects.filter(product_id=product_id).values('id', 'size')
    return JsonResponse({'variants': list(variants)})


def stock_list(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    products = Product.objects.all()
    variants = Variants.objects.all()
  
    selected_product = None
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        selected_product = Product.objects.get(title=product_id)
        variants = Variants.objects.filter(product=selected_product)
    else:
        
        stocks = Stock.objects.all()
        
    paginator = Paginator(stocks, 10)
    page_number = request.GET.get('page')
    page_stocks = paginator.get_page(page_number)

    context = {
        "products": products,
        "selected_product": selected_product,
        "page_stocks": page_stocks
    }

    return render(request, 'adminside/stock_list.html', context)
       



                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT


def order_list(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    p=Paginator(Order.objects.all().order_by('-created_at'),10)
    page = request.GET.get('page')
    orders=p.get_page(page)


    context={
        'orders': orders,

    }
    return render(request, 'adminside/order_list.html',context)







def order_detail(request, order_id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    order = get_object_or_404(Order, id=order_id)
    order_products = OrderProduct.objects.filter(order=order)
    # coupon = Coupon.objects.filter(id=order.coupon_id)

    subtotal = 0
    for i in order_products:
            subtotal += i.product_price * i.quantity
    for item in order_products:
        item.total_price = item.product.price * item.quantity 
    coupon = None
    if order.coupon:
        try:
            coupon = Coupon.objects.get(id=order.coupon_id)
        except Coupon.DoesNotExist:
            pass
    context = {
        'order': order,
        'order_products': order_products,
        'subtotal':subtotal,
        'coupon':coupon,
    }

    return render(request, 'adminside/order_detail.html',context)


def update_order_status(request, order_id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        if not order.status == "Cancelled":
            new_status = request.POST.get('status')
            order.status = new_status
            order.save()
            if new_status == "Cancelled":
                admin_cancel_order(request,order_id)
            return redirect('adminside:order_detail', order_id=order_id)
        else:
            messages.error(request,"Order is already cancelled")
    return render(request, 'adminside/order_detail.html', {'order': order})

from django.core.exceptions import ObjectDoesNotExist

def admin_cancel_order(request, order_id):
    try:
        order = Order.objects.get(id=order_id)
        messages.success(request, 'Order has been cancelled successfully.')

        if order.payment:
            if (
                order.payment.payment_method == "Paypal"
                or order.payment.payment_method == "wallet payment"
            ):
                if not order.payment.status == "Payment pending":
                    amount = order.order_total
                    user = order.user

                    Transaction.objects.create(
                        user=user,
                        description="Cancelled Order " + str(order_id),
                        amount=amount,
                        transaction_type="Credit",
                    )
                else:
                    messages.error(request,"payment was not done")
    except ObjectDoesNotExist:
        messages.error(request, 'Order not found or has already been cancelled.')
    except Exception as e:
        messages.error(request, 'An error occurred while cancelling the order: {}'.format(str(e)))




                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT



def create_coupon(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    if request.method=='POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminside:admin_index')
    else:
        form = CouponForm()
    return render(request,'adminside/create_coupon.html',{'form':form})


def coupon_list(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')

    coupons = Coupon.objects.all().order_by('-id')
    p=Paginator(coupons,5)
    page = request.GET.get('page')
    couponss =p.get_page(page)

    context = {
        'coupons':couponss,
    }

    return render(request,'adminside/coupon_list.html',context)



@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_coupon(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        coupon = Coupon.objects.get(id=id)
    except ValueError:
        return redirect('adminside:coupon_list')
    coupon.delete()

    return redirect('adminside:coupon_list')
        

def available_coupon(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    coupon=get_object_or_404(Coupon,id=id)

    if coupon.active:
        coupon.active=False

    else:
        coupon.active=True
    coupon.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))

                        # OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT
                        # OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT
                        # OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT
                        # OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT# OFFER_MANAGEMENT

def offer_list(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')

    product_offer = ProductOffer.objects.filter(start_date__lte=date.today(),end_date__gte=date.today()).order_by('-id')
    category_offer = CategoryOffer.objects.filter(start_date__lte=date.today(),end_date__gte=date.today()).order_by('-id')

    p=Paginator(product_offer,5)
    page = request.GET.get('page')
    product_offers=p.get_page(page)

    p=Paginator(category_offer,5)
    page = request.GET.get('page')
    category_offers=p.get_page(page)

    return render(request,"adminside/offer_list.html",{'product_offers':product_offers,'category_offers':category_offers})

def create_product_offer(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    if request.method == 'POST':
        form = ProductOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminside:offer_list')
    else:
        form = ProductOfferForm()
    return render(request,"adminside/create_product_offer.html",{'form':form})


def create_category_offer(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    if request.method == 'POST':
        form = CategoryOfferForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminside:offer_list')
    else:
        form = CategoryOfferForm()
    return render(request,"adminside/create_category_offer.html",{'form':form})

                            # SALES_REPORT# SALES_REPORT# SALES_REPORT# SALES_REPORT
                            # SALES_REPORT# SALES_REPORT# SALES_REPORT# SALES_REPORT
                            # SALES_REPORT# SALES_REPORT# SALES_REPORT# SALES_REPORT
                            # SALES_REPORT# SALES_REPORT# SALES_REPORT# SALES_REPORT

def sales_report(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    start_date_value = ""
    end_date_value = ""
    grand_totall = 0
    orders = Order.objects.filter(is_ordered=True).order_by('-created_at').exclude(status='Cancelled')

    if request.method == 'POST':
        date_filter = request.POST.get('date_filter')
        if date_filter == 'daily':
            today = now().date()
            orders = Order.objects.filter(is_ordered=True, created_at__date=today).order_by('-created_at')
        elif date_filter == 'weekly':
            today = now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            orders = Order.objects.filter(is_ordered=True, created_at__date__range=[start_of_week, end_of_week]).order_by('-created_at')
        elif date_filter == 'yearly':
            today = now().date()
            start_of_year = today.replace(month=1, day=1)
            end_of_year = today.replace(month=12, day=31)
            orders = Order.objects.filter(is_ordered=True, created_at__date__range=[start_of_year, end_of_year]).order_by('-created_at')
        else:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            start_date_value = start_date
            end_date_value = end_date
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                orders = orders.filter(created_at__range=(start_date, end_date)).exclude(status='Cancelled')
    grand_totall = round(grand_total(orders),2)


    p=Paginator(orders,10)
    page = request.GET.get('page')
    orderss=p.get_page(page)

    context = {
        'orders': orderss,
        'start_date_value': start_date_value,
        'end_date_value': end_date_value,
        'grand_total':grand_totall
    }

    return render(request, 'adminside/sales_report.html', context)


def grand_total(orders):
    grand_total = 0

    for order in orders:
        grand_total += order.order_total

    return grand_total












































# @login_required(login_url='adminside:admin_login')
# def add_variant(request):
#     if not request.user.is_authenticated or not request.user.is_superadmin:
#         return redirect("adminside:admin_login")

#     products = Product.objects.all()

#     if request.method == 'POST':
#         form = ProductVariantForm(request.POST)
#         if form.is_valid():
#             product_title = form.cleaned_data['product']
#             product = get_object_or_404(Product, title=product_title)
#             stock_count_s = form.cleaned_data['stock_count_s']
#             stock_count_m = form.cleaned_data['stock_count_m']
#             stock_count_l = form.cleaned_data['stock_count_l']
#             stock_count_xl = form.cleaned_data['stock_count_xl']
#             stock_count_xxl = form.cleaned_data['stock_count_xxl']


#             # Create variants for each size
#             variant_s = product.variants.create(size='S', stock_count=stock_count_s)
#             variant_m = product.variants.create(size='M', stock_count=stock_count_m)
#             variant_l = product.variants.create(size='L', stock_count=stock_count_l)
#             variant_xl = product.variants.create(size='XL', stock_count=stock_count_xl)
#             variant_xxl = product.variants.create(size='XXL', stock_count=stock_count_xxl)


#             return redirect('adminside:variant_list')
#     else:
#         form = ProductVariantForm()      

#     context = {     
#         'form': form,
#         'products': products,
#     }

#     return render(request, 'adminside/add_variant.html', context)


# def variant_list(request):
#     if not request.user.is_authenticated or not request.user.is_superadmin:
#         return redirect("adminside:admin_login")
        
#     products = Product.objects.all()
#     selected_product = None
    
#     if request.method == 'POST':
#         product_id = request.POST.get('product')
#         selected_product = Product.objects.get(title=product_id)
#         variants = ProductVariants.objects.filter(product=selected_product)
#     else:
#         variants = ProductVariants.objects.all()
        
#     paginator = Paginator(variants, 10)
#     page_number = request.GET.get('page')
#     page_variants = paginator.get_page(page_number)

#     context = {
#         "products": products,
#         "selected_product": selected_product,
#         "page_variants": page_variants
#     }

#     return render(request, 'adminside/variant_list.html', context)


# def varient_edit(request,vid):
#     if not request.user.is_authenticated:
#         if not request.user.is_super_admin:
#             return redirect("adminside:admin_login")
        

#     varients = get_object_or_404(ProductVariants,vid=vid)
#     if request.method == 'POST':
#         var_size = request.POST.get("size") 
#         var_stock = request.POST.get("stock_count")
        

   
#     varients.size =var_size
#     varients.stock =var_stock
    

#     varients.save()

 