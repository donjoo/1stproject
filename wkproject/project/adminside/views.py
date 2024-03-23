from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages
from userauth.models import User
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponse,HttpResponseRedirect
from django.views.decorators.cache import cache_control
from app.models import Product,Category,ProductImage,ProductVariants,CategoryAnime,AnimeCharacter,Variants,Stock,Coupon
from django.core.paginator import Paginator
from adminside.forms import CreateProductForm,ProductVariantForm,CouponForm
from django.http import Http404
from django.http import JsonResponse
from orders.models import Order,OrderProduct,Payment
from datetime import datetime


# from orders.models import Order,Payement
# Create your views here.


def new(request):
    return render(request,'adminside/new.html')


@login_required(login_url='adminside:admin_login')
def admin_index(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")
    return render(request,'adminside/admin_index.html')


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
        data = User.objects.filter(
            Q(username__icontains=query)|Q(email__icontains=query)
        )
    else:
        data = User.objects.all()
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
                'characters':character,
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




def delete_product(request,pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
    try:
        product=Product.objects.get(pid=pid)
        product.delete()
        return redirect('adminside:product_list')
    except Product.DoesNotExist:
        return HttpResponse("product not Found",status=404)
    
   
@login_required(login_url='adminside:admin_login')
def product_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    products = Product.objects.all().order_by('-date') 
    p=Paginator(Product.objects.all(),10)
    page = request.GET.get('page')
    productss=p.get_page(page)

    context = {
        "products":products,
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



def product_edit(request,pid):
    if not request.user.is_superadmin:
       
            return redirect('adminside:admin_login')



    categories = Category.objects.all()
    animes = CategoryAnime.objects.all()
    characters = AnimeCharacter.objects.all()
    productt = get_object_or_404(Product,pid=pid)

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
            return render(request,'adminside/product_edit.html',content)
        

        
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

   
    try:
        product = get_object_or_404(Product,pid=pid)
    except product.DoesNotExist:
        product = None
    try:
       anime = get_object_or_404(CategoryAnime,title=productt.anime)
    except CategoryAnime.DoesNotExist:
        anime = None
    try:
       category = get_object_or_404(Category,title=productt.category)
    except Category.DoesNotExist:
        category = None
    try:
       character = get_object_or_404(AnimeCharacter,name=productt.character)
    except AnimeCharacter.DoesNotExist:
        character = None

    
    context = {
        'productt': product,
        'animes':animes,
        'category':category,
        'characters':characters,
        
    }

    return render(request, 'adminside/product_edit.html', context)

@login_required(login_url='adminside:admin_login')
def products_details(request, pid):
    if not request.user.is_superadmin:
        return redirect('adminside:admin_login')
   

    try:
        product = Product.objects.get(pid=pid)
        product_images = ProductImage.objects.filter(product=product)
    except Product.DoesNotExist:
        return HttpResponse("Product not found", status=404)

    if request.method == 'POST':
        form = CreateProductForm(request.POST, request.FILES, instance=product)
        if form.is_valid():
           
            product = form.save(commit=False)
            product_image = form.cleaned_data['new_image']
            if product_image is not None:
                product.image = product_image
            product.save()

          
            for i in product_images:
                image_field_name = f'product_image{i.id}'
                image = request.FILES.get(image_field_name)

                if image:
                    i.Images = image
                    i.save()

            return redirect('adminside:product_list')
        else:
            print(form.errors)
            context = {
                'form': form,
                'product': product,
                'product_images': product_images,
            }
            return render(request, 'adminside/products_details.html', context)
    else:
        initial_data = {'new_image': product.image.url if product.image else ''}
        form = CreateProductForm(instance=product, initial=initial_data)

    context = {
        'form': form,
        'product': product,
        'product_images': product_images,
    }
    return render(request, 'adminside/products_details.html', context)



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
        if Category.objects.filter(title=cat_name).exists():
            messages.error(request, 'Category with this name already exists.')
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
    
    categories = Category.objects.all()
    
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
        if CategoryAnime.objects.filter(title=anime_name).exists():
            messages.error(request, 'Category with this name already exists.')
        else:
            anime_data = CategoryAnime(title=anime_name, image=request.FILES.get('anime_image'))
            anime_data.save()
            print("yes")
            messages.success(request, 'Category added successfully.')       
    else:
        return render(request, 'adminside/animecat_list.html')
    
    return render(request, 'adminside/animecat_list.html')



def animecat_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    Animes = CategoryAnime.objects.all()
    
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
        if AnimeCharacter.objects.filter(name=char_name).exists():
            messages.error(request, 'Category with this name already exists.')
        else:
            anime_name = get_object_or_404(CategoryAnime, title=anime_name)
            char_data = AnimeCharacter(name=char_name,animename=anime_name ,image=request.FILES.get('char_image'))
            char_data.save()
            print("yes")
            messages.success(request, 'Category added successfully.') 
              
    else:
        context={
            'animes':animes
        }
        return render(request, 'adminside/characters_list.html',context)
    
    return render(request, 'adminside/characters_list.html')



def character_list(request):
    if request.user.is_authenticated:
        if not request.user.is_superadmin:
            return redirect('adminside:admin_login')
    
    characters = AnimeCharacter.objects.all()
    animes = CategoryAnime.objects.all()
    
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
        character = AnimeCharacter.objects.get(lid=lid)
    except ValueError:
        return redirect('adminside:characters_list')
    character.delete()

    return redirect('adminside:characters_list')
        

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
        product_title = request.POST.get('product')  # Assuming this is a title
        size = request.POST.get('size')

        # Retrieve product by title
        product = get_object_or_404(Product, title=product_title)

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
        "page_variants": page_stocks
    }

    return render(request, 'adminside/stock_list.html', context)
       



                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT
                            # ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT# ORDER MANAGMENT


def order_list(request):
    orders = Order.objects.all()

    context={
        'orders': orders,

    }
    return render(request, 'adminside/order_list.html',context)







def order_detail(request, order_id):
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
    order = get_object_or_404(Order, id=order_id)
    if request.method == 'POST':
        new_status = request.POST.get('status')
        order.status = new_status
        order.save()
        return redirect('adminside:order_detail', order_id=order_id)
    return render(request, 'update_order_status.html', {'order': order})





                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT
                # COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT# COUPON_MANAGEMENT



def create_coupon(request):
    if request.method=='POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('adminside:admin_index')
    else:
        form = CouponForm()
    return render(request,'adminside/create_coupon.html',{'form':form})


def coupon_list(request):

    coupons = Coupon.objects.all()

    context = {
        'coupons':coupons,
    }

    return render(request,'adminside/coupon_list.html',context)


def sales_report(request):
    if not request.user.is_authenticated or not request.user.is_superadmin:
        return redirect("adminside:admin_login")

    start_date_value = ""
    end_date_value = ""
    try:

        orders=Order.objects.filter(is_ordered = True).order_by('-created_at')
    
    except:
        pass
    if request.method == 'POST':
       
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        start_date_value = start_date
        end_date_value = end_date
        if start_date and end_date:
          
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

           
            orders = orders.filter(created_at__range=(start_date, end_date))
   
    context={
        'orders':orders,
        'start_date_value':start_date_value,
        'end_date_value':end_date_value
    }

    return render(request,'adminside/sales_report.html',context)
















































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

 