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
from orders.models import Order,OrderProduct,Payment,ProductRating
from datetime import datetime,date,timedelta
from django.utils import timezone
import os
from django.conf import settings
from django.db.models import Sum
from django.utils.timezone import now
import logging

# Set up logging
logger = logging.getLogger(__name__)
from django.db.models import Count
from django.db.models.functions import TruncMonth,TruncYear
from django.core.exceptions import ObjectDoesNotExist
from userauth.views import canceladd_stock
import imghdr
import base64
from django.core.files.base import ContentFile
from decimal import Decimal
from django.db.models import Avg, Count


current_date = timezone.now()   


def admin_login(request):
    if request.user.is_authenticated:
        if request.user.is_superadmin:
            return redirect('adminside:admin_index')
    if request.method == "POST":
        email = request.POST['email']
        password = request.POST['password']
        user = authenticate(request,email=email,password=password)
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
def admin_index(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    best_selling_products = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__title').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]

    best_selling_categories = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__category__title').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]
    
    best_selling_characters = OrderProduct.objects.filter(ordered=True).exclude(order__status='Cancelled').values('product__character__name').annotate(total_quantity=Count('product')).order_by('-total_quantity')[:10]
    

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
            .values('created_at__date')
            .annotate(order_count=Count('id'))
            .order_by('created_at__date')
        )
    dates = [entry['created_at__date'].strftime('%Y-%m-%d') for entry in daily_order_counts]
    counts = [entry['order_count'] for entry in daily_order_counts]

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
            # Only count revenue for items that haven't been refunded
            if not item.refunded:
                revenue += item.product_price * item.quantity
    return revenue


def calculate_monthly_revenue(year, month):
    total_earnings = 0
    orders = Order.objects.filter(created_at__year = year,created_at__month = month).exclude(status = 'Cancelled').exclude(status = 'Returned')
    for order in orders:
        order_products = OrderProduct.objects.filter(order = order)
        for item in order_products:
            # Only count revenue for items that haven't been refunded
            if not item.refunded:
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
    if not request.user.is_authenticated or not request.user.is_superadmin:
    #     return redirect("adminside:admin_login")
    # if not request.user.is_authenticated:
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




def is_valid_image(file):
    """Validate uploaded file type"""
    valid_extensions = ['jpeg', 'jpg', 'png', 'gif', 'webp']
    file_type = imghdr.what(file)
    return file_type in valid_extensions



def decode_cropped_image(data, name):
    if not data:
        return None
    format, imgstr = data.split(';base64,') 
    ext = format.split('/')[-1] 
    return ContentFile(base64.b64decode(imgstr), name=f"{name}.{ext}")


@login_required(login_url='adminside:admin_login')
def add_product(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')

    categories = Category.objects.filter(delete='False')
    animes = CategoryAnime.objects.filter(delete='False')
    characters = AnimeCharacter.objects.filter(delete='False')

    if request.method == 'POST':
        # Collect form data
        product_name = request.POST.get('name', '').strip()
        descriptions = request.POST.get('descriptions', '').strip()
        specifications = request.POST.get('specifications', '').strip()
        max_price = request.POST.get('old_price')
        sale_price = request.POST.get('price')
        category_name = request.POST.get('category')
        anime_name = request.POST.get('anime')
        character_name = request.POST.get('character')
        fit = request.POST.get('fit', '').strip()
        fabric = request.POST.get('fabric', '').strip()
        care = request.POST.get('care', '').strip()
        sleeve = request.POST.get('sleeve', '').strip()
        collar = request.POST.get('collar', '').strip()
        cropped_main = request.POST.get('cropped_image_main')
        image_file = decode_cropped_image(cropped_main, product_name) or request.FILES.get('image_field')



        validation_errors = []

        # --- 1️⃣ Basic Required Field Validation ---
        if not product_name:
            validation_errors.append("Product name is required.")
        if not descriptions:
            validation_errors.append("Description is required.")
        if not specifications:
            validation_errors.append("Specifications are required.")
        if not fit:
            validation_errors.append("Fit style is required.")
        if not fabric:
            validation_errors.append("Fabric type is required.")
        if not care:
            validation_errors.append("Care instructions are required.")
        if not sleeve:
            validation_errors.append("Sleeve type is required.")
        if not collar:
            validation_errors.append("Collar type is required.")
        if not category_name:
            validation_errors.append("Please select a category.")
        if not anime_name:
            validation_errors.append("Please select an anime.")
        if not character_name:
            validation_errors.append("Please select a character.")
        if not image_file:
            validation_errors.append("Main product image is required.")

        # --- 2️⃣ Validate Image File ---
        if image_file and not is_valid_image(image_file):
            validation_errors.append("Invalid image file format. Only JPG, PNG, GIF, or WEBP allowed.")

        # --- 3️⃣ Validate Prices ---
        try:
            max_price = float(max_price)
            if max_price <= 0:
                validation_errors.append("Max price must be greater than 0.")
        except (ValueError, TypeError):
            validation_errors.append("Enter a valid number for Max price.")

        try:
            sale_price = float(sale_price)
            if sale_price <= 0:
                validation_errors.append("Sale price must be greater than 0.")
            elif 'max_price' in locals() and sale_price > max_price:
                validation_errors.append("Sale price cannot be greater than Max price.")
        except (ValueError, TypeError):
            validation_errors.append("Enter a valid number for Sale price.")


        text_fields = {
                "Fit style": fit,
                "Fabric": fabric,
                "Care": care,
                "Sleeve type": sleeve,
                "Collar style": collar
            }

        for field_name, value in text_fields.items():
            if not value.strip():
                validation_errors.append(f"{field_name} is required.")
            elif value.strip().isdigit():
                validation_errors.append(f"{field_name} cannot be a number.")
            elif len(value.strip()) < 2:
                validation_errors.append(f"{field_name} must contain at least 2 characters.")
        # --- 4️⃣ If Validation Fails ---
        if validation_errors:
            form_data = {
                'name': product_name,
                'descriptions': descriptions,
                'specifications': specifications,
                'old_price': max_price,
                'price': sale_price,
                'category': category_name,
                'anime': anime_name,
                'character': character_name,
                'fit': fit,
                'fabric': fabric,
                'care': care,
                'sleeve': sleeve,
                'collar': collar,
            }
            content = {
                'categories': categories,
                'animes': animes,
                'characters': characters,
                'additional_image_count': range(1, 4),
                'error_messages': validation_errors,
                'form_data': form_data,
            }
            return render(request, 'adminside/add_product.html', content)

        # --- 5️⃣ If Valid, Save Product ---
        category = get_object_or_404(Category, title=category_name)
        anime = get_object_or_404(CategoryAnime, title=anime_name)
        character = get_object_or_404(AnimeCharacter, name=character_name)

        product = Product.objects.create(
            title=product_name,
            category=category,
            anime=anime,
            character=character,
            descriptions=descriptions,
            specifications=specifications,
            old_price=max_price,
            price=sale_price,
            fit=fit,
            fabric=fabric,
            care=care,
            sleeve=sleeve,
            collar=collar,
            image=image_file
        )

        # --- 6️⃣ Save Additional Images ---
        for i in range(1, 5):
            image_field = f'product_image{i}'
            img = request.FILES.get(image_field)
            if img and is_valid_image(img):
                ProductImage.objects.create(product=product, Images=img)

        messages.success(request, "Product added successfully.")
        return redirect('adminside:product_list')

    # --- GET request ---
    form_data = {
        'name': '', 'descriptions': '', 'specifications': '', 'old_price': '',
        'price': '', 'category': '', 'anime': '', 'character': '',
        'fit': '', 'fabric': '', 'care': '', 'sleeve': '', 'collar': ''
    }
    context = {
        'characters': characters,
        'animes': animes,
        'categories': categories,
        'additional_image_count': range(1, 4),
        'form_data': form_data,
    }
    return render(request, 'adminside/add_product.html', context)


def delete_product(request,pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    try:  
        product=Product.objects.get(pid=pid)
        product.delete = True
        product.save()  
        return redirect('adminside:product_list')
    except Product.DoesNotExist:
        return HttpResponse("product not Found",status=404)


# def is_valid_image(file):
#     valid_extensions = ['.jpg', '.jpeg', '.png', '.gif']
#     ext = os.path.splitext(file.name)[1]
#     return ext.lower() in valid_extensions
   
@login_required(login_url='adminside:admin_login')
def product_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    p=Paginator(Product.objects.filter(delete='False').order_by('-date'),10)
    page = request.GET.get('page')
    productss=p.get_page(page)

    context = {
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
        product.descriptions = request.POST.get('descriptions')
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

    categories = Category.objects.filter(delete='False')
    animes = CategoryAnime.objects.filter(delete='False')
    characters = AnimeCharacter.objects.filter(delete='False')

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
            'descriptions': product.descriptions,
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
        p_image = product.p_images.all()
        # Passing pid to is_size_out_of_stock function
        sizes_out_of_stock = {size.size: is_size_out_of_stock(pid, size.size) for size in sizes}
        all_sizes_out_of_stock = all(sizes_out_of_stock.values())
        offers = ProductOffer.objects.filter(product=product,start_date__lte = current_date,end_date__gte = current_date)
        catoffers = CategoryOffer.objects.filter(category = product.category,start_date__lte = current_date,end_date__gte = current_date)
        avg_rating = ProductRating.objects.filter(product=product).aggregate(avg=Avg('rating'))['avg'] or 0
        rounded_rating = round(avg_rating)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)
    context = {
        'offers':offers,
        'p_image':p_image,
        'catoffers':catoffers,
        'product': product,
        'product_images': product_images,
        'sizes_out_of_stock':sizes_out_of_stock,
        'all_sizes_out_of_stock':all_sizes_out_of_stock,
        "avg_rating": rounded_rating,

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
        cat_name = request.POST.get('category_name', '').strip()
        cropped_data = request.POST.get('cropped_image_data')
        cat_image = decode_cropped_image(cropped_data, cat_name) or request.FILES.get('category_image')
        validation_errors = []

        # Load existing categories for re-rendering the page on error
        p = Paginator(Category.objects.filter(delete='False').order_by('-date'), 10)
        page = request.GET.get('page')
        categories = p.get_page(page)

        # 1️⃣ Validate empty category name
        if not cat_name:
            validation_errors.append("Category name is required.")

        # 2️⃣ Validate duplicate category name (case-insensitive)
        elif Category.objects.filter(title__iexact=cat_name, delete='False').exists():
            validation_errors.append("A category with this name already exists.")

        # If any validation errors, re-render page with error messages
        if validation_errors:
            for error in validation_errors:
                messages.error(request, error)
            return render(request, 'adminside/categories_list.html', {
                'categories': categories
            })

        # 3️⃣ If valid, create new category
        Category.objects.create(title=cat_name, image=cat_image)
        messages.success(request, "Category added successfully.")
        return redirect('adminside:category_list')

    # GET request
    return redirect('adminside:category_list')



@login_required(login_url='adminside:admin_login')
def category_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    p=Paginator(Category.objects.filter(delete='False').order_by('-date'),10)
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
    
    category = get_object_or_404(Category, cid=cid)

    if request.method == 'POST':
        name = request.POST.get('category_name', '').strip()
        cropped_data = request.POST.get('cropped_image_data')
        image = decode_cropped_image(cropped_data, name) or request.FILES.get('category_image')

        # Update category fields
        category.title = name
        if image:
            category.image = image
        category.save()

        messages.success(request, "Category updated successfully.")
        return redirect('adminside:category_list')

    context = {
        'categories_title': category.title,
        'categories_image': category.image,
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
    category.delete=True
    category.save()

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
        cropped_data = request.POST.get('cropped_image_data')
        cat_image = decode_cropped_image(cropped_data, anime_name) or request.FILES.get('category_image')
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
            anime_data = CategoryAnime(title=anime_name, image=cat_image)
            anime_data.save()
            messages.success(request, 'Category added successfully.')       
    else:
        return redirect('adminside:animecat_list')
    
    return redirect('adminside:animecat_list')



def animecat_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    p=Paginator(CategoryAnime.objects.filter(delete='False').order_by('-id'),10)
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

        anime_name = request.POST.get("anime_name",'').strip()
        # if not anime_name:  # Validate title
        #     messages.error(request, "Anime name is required.")
        #     return redirect(request.path)
        cropped_data = request.POST.get('cropped_image_data')
        anime_img = decode_cropped_image(cropped_data, anime_name) or request.FILES.get('category_image')
        
        animes.title =anime_name
        if anime_img is not None:
             animes.image=anime_img 
        animes.save()

        return redirect('adminside:animecat_list')

    context = {
        "categories_title": animes.title,
        "categories_image": animes.image,
    }

    return render(request, 'adminside/animecat_edit.html', context)


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_animecat(request,aid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        anime = CategoryAnime.objects.get(aid=aid)
    except ValueError:
        return redirect('adminside:animecat_list')
    anime.delete = True
    anime.save()

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

    if request.method == 'POST':
        
        anime_name = request.POST.get('anime')
        char_name = request.POST.get('char_name')
        cropped_data = request.POST.get('cropped_image_data')
        cat_image = decode_cropped_image(cropped_data, char_name) or request.FILES.get('category_image')

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
            char_data = AnimeCharacter(name=char_name,animename=anime_name ,image=cat_image)
            char_data.save()
            messages.success(request, 'Category added successfully.') 
              
    else:
        
        return redirect('adminside:character_list')
    
    return redirect('adminside:character_list')


def character_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
   
    animes = CategoryAnime.objects.filter(delete='False')
    p=Paginator( AnimeCharacter.objects.filter(delete = 'False').order_by('-id'),10)
    page = request.GET.get('page')
    characters=p.get_page(page)

    
    context = {
        'characters':characters,
        'animes':animes
    }   
    return render(request,'adminside/characters_list.html',context)

       
def character_edit(request,lid):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    # if not request.user.is_authenticated:
    #     return redirect('adminside:admin_login')
    
    characters = get_object_or_404(AnimeCharacter,lid=lid)


    if request.method == 'POST':
        # char_img = request.FILES.get('char_image')
        char_name = request.POST.get("char_name")
        cropped_data = request.POST.get('cropped_image_data')
        char_img = decode_cropped_image(cropped_data, char_name) or request.FILES.get('category_image')


        characters.name =char_name
        if char_img is not None:
             characters.image=char_img 

        characters.save()

       
        return redirect('adminside:character_list')

    
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
    character.delete = True
    character.save()

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

    products = Product.objects.filter(delete='False')
    
    if request.method == 'POST':
        product_id = request.POST.get('product')  
        size = request.POST.get('size')

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
        
    products = Product.objects.filter(delete='False')
    selected_product = None
    
    if request.method == 'POST':
        product_id = request.POST.get('product')
        selected_product = Product.objects.get(title=product_id)
        variants = Variants.objects.filter(product=selected_product,delete='False')
    else:
        variants = Variants.objects.filter(delete='False')
        
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
    size.delete = True                                      
    size.save()  

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

    products = Product.objects.filter(delete = 'False')
    context = {'products': products}
    return render(request, 'adminside/add_stock.html', context)


def get_variants(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    product_id = request.GET.get('product_id')
    variants = Variants.objects.filter(product_id=product_id,delete='False').values('id', 'size')
    return JsonResponse({'variants': list(variants)})


def stock_list(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    products = Product.objects.filter(delete = 'False')
    variants = Variants.objects.filter(delete='False')
  
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

    subtotal = 0
    for i in order_products:
            subtotal += i.product_price * i.quantity
    for item in order_products:
        item.total_price = item.product.price * item.quantity 
    coupon = None
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
    context = {
        'order': order,
        'order_products': order_products,
        'subtotal':subtotal,
        'coupon':coupon,
        'coupon_discount': coupon_discount,
    }

    return render(request, 'adminside/order_detail.html',context)


def update_order_status(request, order_id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        if not order.status == "Cancelled":
            if not order.status == "Returned":
                new_status = request.POST.get('status')
                order.status = new_status
                order.save()
                if new_status == "Cancelled":
                    admin_cancel_order(request,order_id)
                return redirect('adminside:order_detail', order_id=order_id)
            else:
                 messages.error(request,"Order is already Returned")
        else:
            messages.error(request,"Order is already cancelled")
    return render(request, 'adminside/order_detail.html', {'order': order})


def admin_cancel_order(request, order_id):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    try:
        order = Order.objects.get(id=order_id)
        canceladd_stock(request,order)
        messages.success(request, 'Order has been cancelled successfully.')
        if order.payment:
            if (
                order.payment.payment_method == "Paypal"
                or order.payment.payment_method == "wallet payment"
            ):
                if not order.payment.status == "Payment pending":
                    # Get all order products that haven't been refunded yet
                    non_refunded_items = OrderProduct.objects.filter(order=order, refunded=False)
                    
                    if non_refunded_items.exists():
                        # Import the refund function from orders views
                        from orders.views import process_refund_for_items
                        refunded_amount = process_refund_for_items(order, non_refunded_items, "Admin Cancelled", single_transaction=True)
                        
                        if refunded_amount > 0:
                            messages.success(request, f'Order has been cancelled successfully. Refund of ₹{refunded_amount:.2f} has been credited to user wallet.')
                        else:
                            messages.success(request, 'Order has been cancelled successfully.')
                    else:
                        messages.success(request, 'Order has been cancelled successfully.')
                else:
                    messages.error(request,"payment was not done")
    except ObjectDoesNotExist:
        messages.error(request, 'Order not found or has already been cancelled.')
    except Exception as e:
        messages.error(request, 'An error occurred while cancelling the order: {}'.format(str(e)))


@login_required(login_url='adminside:admin_login')
def admin_cancel_order_item(request, order_product_id):
    """Admin function to cancel a specific product in an order"""
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    
    if request.method == "POST":
        try:
            order_product = get_object_or_404(OrderProduct, id=order_product_id)
            
            # Check if item can be cancelled
            if order_product.item_status != 'Ordered':
                messages.warning(request, f'This item is already {order_product.item_status.lower()}.')
                return redirect('adminside:order_detail', order_product.order.id)
            
            # Check if order is in a cancellable state
            if order_product.order.status in ['Delivered', 'Cancelled', 'Returned']:
                messages.warning(request, 'This order cannot be cancelled.')
                return redirect('adminside:order_detail', order_product.order.id)
            
            # Update item status
            order_product.item_status = 'Cancelled'
            order_product.save()
            
            # Add stock back for this specific item
            canceladd_stock_for_item(request, order_product)
            
            # Process refund for this specific item (only if not already refunded)
            if order_product.order.payment and not order_product.refunded:
                if (order_product.order.payment.payment_method == "Paypal" or 
                    order_product.order.payment.payment_method == "Wallet"):
                    
                    # Import the refund function from orders views
                    from orders.views import calculate_proportional_refund
                    refund_amount = calculate_proportional_refund(order_product.order, [order_product])
                    
                    if refund_amount > 0:
                        Transaction.objects.create(
                            user=order_product.order.user,
                            description=f"Admin Cancelled Item: {order_product.product.title} from Order {order_product.order.order_number}",
                            amount=refund_amount,
                            transaction_type="Credit",
                        )
                        
                        # Mark as refunded to prevent duplicate refunds
                        order_product.refunded = True
                        order_product.save()
            
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
            
            return redirect('adminside:order_detail', order_product.order.id)
            
        except Exception as e:
            messages.error(request, f'An error occurred while cancelling the item: {str(e)}')
            return redirect('adminside:order_detail', order_product.order.id)
    
    return redirect('adminside:order_list')


@login_required(login_url='adminside:admin_login')
def admin_return_order(request, order_id):
    """Admin function to return an entire order"""
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    
    try:
        order = Order.objects.get(id=order_id)
        order.status = "Returned"
        order.save()
        canceladd_stock(request, order)
        
        # Process refund for all non-refunded items only
        if order.payment:
            if (
                order.payment.payment_method == "Paypal"
                or order.payment.payment_method == "Wallet"
            ):
                if not order.payment.status == "Payment pending":
                    # Get all order products that haven't been refunded yet
                    non_refunded_items = OrderProduct.objects.filter(order=order, refunded=False)
                    
                    if non_refunded_items.exists():
                        # Import the refund function from orders views
                        from orders.views import process_refund_for_items
                        refunded_amount = process_refund_for_items(order, non_refunded_items, "Admin Returned", single_transaction=True)
                        
                        if refunded_amount > 0:
                            messages.success(request, f'Order has been returned successfully. Refund of ₹{refunded_amount:.2f} has been credited to user wallet.')
                        else:
                            messages.success(request, 'Order has been returned successfully.')
                    else:
                        messages.success(request, 'Order has been returned successfully.')
                else:
                    messages.error(request, "Payment was not done")
        else:
            messages.success(request, 'Order has been returned successfully.')
            
    except Order.DoesNotExist:
        messages.error(request, 'Order not found or has already been returned.')
    except Exception as e:
        messages.error(request, f'An error occurred while returning the order: {str(e)}')
    
    return redirect('adminside:order_detail', order_id=order_id)


@login_required(login_url='adminside:admin_login')
def admin_return_order_item(request, order_product_id):
    """Admin function to return a specific product in an order"""
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    
    if request.method == "POST":
        try:
            order_product = get_object_or_404(OrderProduct, id=order_product_id)
            
            # Check if item can be returned
            if order_product.item_status != 'Ordered':
                messages.warning(request, f'This item is already {order_product.item_status.lower()}.')
                return redirect('adminside:order_detail', order_product.order.id)
            
            # Check if order is delivered
            if order_product.order.status != 'Delivered':
                messages.warning(request, 'Items can only be returned after delivery.')
                return redirect('adminside:order_detail', order_product.order.id)
            
            # Update item status
            order_product.item_status = 'Returned'
            order_product.save()
            
            # Add stock back for this specific item
            canceladd_stock_for_item(request, order_product)
            
            # Process refund for this specific item (only if not already refunded)
            if order_product.order.payment and not order_product.refunded:
                # Import the refund function from orders views
                from orders.views import calculate_proportional_refund
                refund_amount = calculate_proportional_refund(order_product.order, [order_product])
                
                if refund_amount > 0:
                    Transaction.objects.create(
                        user=order_product.order.user,
                        description=f"Admin Returned Item: {order_product.product.title} from Order {order_product.order.order_number}",
                        amount=refund_amount,
                        transaction_type="Credit",
                    )
                    
                    # Mark as refunded to prevent duplicate refunds
                    order_product.refunded = True
                    order_product.save()
            
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
            
            return redirect('adminside:order_detail', order_product.order.id)
            
        except Exception as e:
            messages.error(request, f'An error occurred while returning the item: {str(e)}')
            return redirect('adminside:order_detail', order_product.order.id)
    
    return redirect('adminside:order_list')


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
            discount = form.cleaned_data['discount']
            if 1 <= discount <= 100:
                form.save()
                messages.success(request, "Coupon created successfully!")
                return redirect('adminside:coupon_list')
            else:
                messages.error(request, "Discount must be between 1% and 100%.")
    else:
        form = CouponForm()
    return render(request,'adminside/create_coupon.html',{'form':form})


def coupon_list(request):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')

    coupons = Coupon.objects.filter(delete='False').order_by('-id')
    p=Paginator(coupons,5)
    page = request.GET.get('page')
    couponss =p.get_page(page)

    context = {
        'coupons':couponss,
    }
    return render(request,'adminside/coupon_list.html',context)



def edit_coupon(request, coupon_id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    coupon = Coupon.objects.filter(id=coupon_id, delete=False).first()
    if not coupon:
        messages.error(request, "Coupon not found.")
        return redirect('adminside:coupon_list')

    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            discount = form.cleaned_data['discount']
            if 1 <= discount <= 100:
                form.save()
                messages.success(request, "Coupon updated successfully!")
                return redirect('adminside:coupon_list')
            else:
                messages.error(request, "Discount must be between 1% and 100%.")
    else:
        form = CouponForm(instance=coupon)

    return render(request, 'adminside/edit_coupon.html', {'form': form, 'coupon': coupon})



@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_coupon(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        coupon = Coupon.objects.get(id=id)
    except ValueError:
        return redirect('adminside:coupon_list')
    coupon.delete = True
    coupon.active = False
    coupon.save()

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

    product_offer = ProductOffer.objects.filter(delete='False',start_date__lte=date.today(),end_date__gte=date.today()).order_by('-id')
    category_offer = CategoryOffer.objects.filter(delete = 'False',start_date__lte=date.today(),end_date__gte=date.today()).order_by('-id')

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


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_product_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        offer = ProductOffer.objects.get(id=id)
    except ValueError:
        return redirect('adminside:offer_list')
    offer.delete = True
    offer.save()

    return redirect('adminside:offer_list')
        

def block_product_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    offer=get_object_or_404(ProductOffer,id=id)

    if offer.active:
        offer.active=False

    else:
        offer.active=True
    offer.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))


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


@login_required(login_url='adminside:admin_login')
@cache_control(no_cache=True,must_revalidaate=True,no_store=True)
def delete_category_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
        
    try:
        offer = CategoryOffer.objects.get(id=id)
    except ValueError:
        return redirect('adminside:offer_list')
    offer.delete = True
    offer.save()

    return redirect('adminside:offer_list')
        

def block_category_offer(request,id):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    
    offer=get_object_or_404(CategoryOffer,id=id)
    if offer.active:
        offer.active=False
    else:
        offer.active=True
    offer.save()

    return HttpResponseRedirect(request.META.get('HTTP_REFERER','/'))


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
    orders = Order.objects.filter(is_ordered=True).order_by('-created_at').exclude(status='Cancelled').exclude(status='Returned')

    if request.method == 'POST':
        date_filter = request.POST.get('date_filter')
        if date_filter == 'daily':
            today = now().date()
            orders = Order.objects.filter(is_ordered=True, created_at__date=today).order_by('-created_at').exclude(status='Cancelled').exclude(status='Returned')
        elif date_filter == 'weekly':
            today = now().date()
            start_of_week = today - timedelta(days=today.weekday())
            end_of_week = start_of_week + timedelta(days=6)
            orders = Order.objects.filter(is_ordered=True, created_at__date__range=[start_of_week, end_of_week]).order_by('-created_at').exclude(status='Cancelled').exclude(status='Returned')
        elif date_filter == 'yearly':
            today = now().date()
            start_of_year = today.replace(month=1, day=1)
            end_of_year = today.replace(month=12, day=31)
            orders = Order.objects.filter(is_ordered=True, created_at__date__range=[start_of_year, end_of_year]).order_by('-created_at').exclude(status='Cancelled').exclude(status='Returned')
        else:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            start_date_value = start_date
            end_date_value = end_date
            if start_date and end_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d')
                end_date = datetime.strptime(end_date, '%Y-%m-%d')
                orders = orders.filter(created_at__range=(start_date, end_date),status='Delivered').exclude(status='Cancelled').exclude(status='Returned')
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


