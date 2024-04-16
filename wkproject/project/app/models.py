from django.db import models
from shortuuid.django_fields import ShortUUIDField
from django.conf import settings
from django.shortcuts import reverse
from decimal import Decimal
# from .utils import generate_ref_code
from django.utils.html import mark_safe
from userauth.models import User
from django.utils import timezone
from django.core.validators import MaxValueValidator

# Create your models here.
STATUS_CHOICE = (
     ("process","Processing"),
     ("shipped","Shipped"),
     ("delivered","Delivered"),
 )

Status = (
    ("draft","Draft"),
    ("disabled","Disabled"),
    ("rejected","Rejected"),
    ("in_review","In Review"),
    ("published","Published")
)


RATING= (
    (1, "⭐☆☆☆☆"),
    (2, "⭐⭐☆☆☆"),
    (3, "⭐⭐⭐☆☆"),
    (4, "⭐⭐⭐⭐☆"),
    (5, "⭐⭐⭐⭐⭐")
      
      
)


SIZE_CHOICES = (
        ('S', 'S'),
        ('M', 'M'),
        ('L', 'L'), 
        ('XL','XL'),
        ('XXL','XXL'),
    )


def user_directory_path(instance,filename):
    return 'user_{0}/{1}'.format(instance.user.id,filename)

class Size(models.Model):
    sizename = models.CharField(max_length=100)
    def __str__(self)->str:
        return self.sizename
    
    

class Category(models.Model):
    cid = ShortUUIDField(unique=True,max_length=50,prefix='zoro',alphabet='abc12345')
    title = models.CharField(max_length=100,default="Merch")
    image=models.ImageField(upload_to='category',default='category.jpg',null=True,blank=True)
    is_blocked=models.BooleanField(default=False)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural ="Categories"

    def category_image(self):
        return mark_safe('<img src="%s" width="50" height="50"/>'% (self.image.url))
    
    def __str__(self): 
        return self.title
    


class CategoryAnime(models.Model):
    aid = ShortUUIDField(unique=True,max_length=50,prefix='anime',alphabet='abc12345')
    title = models.CharField(max_length=100,default="anime")
    image=models.ImageField(upload_to='anime',default='anime.jpg',null=True,blank=True)
    is_blocked=models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural ="Anime"

    def Anime_image(self):
        return mark_safe('<img src="%s" width="50" height="50"/>'% (self.image.url))
    
    def __str__(self): 
        return self.title



class AnimeCharacter(models.Model):
    lid = ShortUUIDField(unique=True,max_length=50,prefix='anichar',alphabet='abc12345')
    name = models.CharField(max_length=100,default="tokyo")
    animename = models.ForeignKey(CategoryAnime,on_delete=models.SET_NULL,null=True,related_name='chracter')
    image=models.ImageField(upload_to='character',default='char.jpg',null=True,blank=True)
    is_blocked=models.BooleanField(default=False)
    
    class Meta:
        verbose_name_plural ="AnimeCharacter"

    def Character_image(self):
        return mark_safe('<img src="%s" width="50" height="50"/>'% (self.image.url))
    
    def __str__(self): 
        return self.name






    


class Product(models.Model):
    pid = ShortUUIDField(unique=True,length=10,max_length=20,alphabet='abcdefghi1234567')

    # user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True)
    category= models.ForeignKey(Category,on_delete=models.SET_NULL, null=True, related_name='category')
    anime= models.ForeignKey(CategoryAnime,on_delete=models.SET_NULL, null=True)
    character= models.ForeignKey(AnimeCharacter,on_delete=models.SET_NULL, null=True, related_name='character')
    title = models.CharField(max_length=100,default="hoodie")
    image = models.ImageField(upload_to="user_images", default="product.jpg", null=True, blank=True)
    descriptions = models.TextField(null=True,blank=True,default="this is a good hoodie") 

    price = models.DecimalField(max_digits=10, decimal_places=2, default='749.99')
    old_price = models.DecimalField(max_digits=10,decimal_places=2,default="799.43")

    specifications=models.TextField(null=True,blank=True,default="This hoodie has a roundneck")
    

    # product_status = models.CharField(choices=STATUS,max_length=10,default="in_review")
    status = models.BooleanField(default=True)
    in_stock = models.BooleanField(default=True)
    featured = models.BooleanField(default=True)
    fit = models.CharField(max_length=100,default="oversized")
    fabric = models.CharField(max_length=100,default="cotton")
    care = models.CharField(max_length=100,default="machinewash")
    sleeve = models.CharField(max_length=100,default="full sleeve")
    collar = models.CharField(max_length=100,default="collarles")



    

    sku= ShortUUIDField(unique=True,length=4,max_length=10, prefix="sku", alphabet='abcdefghi1234567')
    date = models.DateTimeField(auto_now_add=True)
    updated=models.DateTimeField(null=True,blank=True)
     

    class Meta:
        verbose_name_plural ="Products"

    def product_image(self):
        return mark_safe('<img src="%s" width="50" height="50"/>'% (self.image.url))
    
    def __str__(self): 
        return self.title
    
     
    def get_percentage(self):
        new_price = (self.price/self.old_price)*100
        return new_price 
        
    


class ProductImage(models.Model):
    Images = models.ImageField(upload_to="products-images", default = "product.jpg")
    product = models.ForeignKey(Product, related_name='p_images',on_delete = models.SET_NULL,null =True)
    date = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name_plural ="Product images"
   
    
class Variants(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    size = models.CharField(max_length=100)
    is_active = models.BooleanField(default = True)
    created_date = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.size
      
class Stock(models.Model):
    variant = models.ForeignKey(Variants, on_delete=models.CASCADE)
    stock =models.IntegerField(default=0)

    def __str__(self):
       return f"Variant: {self.variant}, Stock: {self.stock}"




class ProductVariants(models.Model):
    vid = ShortUUIDField(unique=True, length=10, max_length=20, alphabet='abcdefghi1234567')
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variantss')
    size = models.CharField(max_length=3, choices=SIZE_CHOICES)
    stock_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = "Productt variants"

    def __str__(self):
        return f"{self.product.title} - {self.get_size_display()}"
    
# class SizeStockCount(models.Model):
#      varient = models.ForeignKey(ProductVarients,on_delete=models.CASCADE)
#     #   size = models.ForeignKey(Size,on_delete=models.CASCADE,primary_key=True)
#      stock_count = models.IntegerField(default=0)
    
    
class UserDetails(models.Model):
  user=models.OneToOneField(User, on_delete=models.CASCADE)
  image=models.ImageField(upload_to='userimage')
  full_name=models.CharField(max_length=200, null=True,blank=True)
  bio = models.CharField(max_length=200, null=True, blank=True)
  phone =models.CharField(max_length=15, null=True,blank=True)
  verified =models.BooleanField(default=False)      
  code=models.CharField(max_length=12, blank=True, null=True)
  recommended_by=models.ForeignKey(User, on_delete=models.CASCADE, blank=True, null =True,related_name='recommended_userdetails')
  updated=models.DateTimeField(auto_now=True)
  created=models.DateTimeField(auto_now=True)
  
  def __str__(self):   
      return f"{self.user.username}---{self.code}"
    
  def get_recommend_profiles(self):
    pass
  
  def save(self, *args, **kwargs):
        # if self.code is None:
        #     self.code = generate_ref_code()

            super().save(*args, **kwargs)




class WishList(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wishlist')
    products = models.ManyToManyField(Product)

    def __str__(self):
        return f"Wish List of {self.user.username}"

   




class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    discount = models.PositiveIntegerField(validators=[MaxValueValidator(100)])
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    active = models.BooleanField(default=True)


    def is_valid(self):
        now = timezone.now()
        return self.valid_from <= now <= self.valid_to and self.active
    

    def __str__(self):
        return self.code





                        # wallet#wallet#wallet#wallet# wallet# wallet# wallet
                        # wallet#wallet#wallet#wallet# wallet# wallet# wallet
                        # wallet#wallet#wallet#wallet# wallet# wallet# wallet
                        # wallet#wallet#wallet#wallet# wallet# wallet# wallet


# class Wallet(models.Model):
#     user = models.OneToOneField(User, on_delete=models.CASCADE)
#     balance = models.DecimalField(max_digits=10, decimal_places=2, default=0)

# class Transaction(models.Model):  
#     wallet = models.ForeignKey(Wallet, on_delete=models.CASCADE)
#     amount = models.DecimalField(max_digits=10, decimal_places=2)
#     timestamp = models.DateTimeField(auto_now_add=True)



class Transaction(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, default=1)
    date = models.DateTimeField(auto_now_add=True)
    description = models.TextField(null=False,default='hey')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    transaction_type = models.CharField(max_length=50,default ='credit')






                        # OFFERSMODEL# OFFERSMODEL# OFFERSMODEL# OFFERSMODEL
                        # OFFERSMODEL# OFFERSMODEL# OFFERSMODEL# OFFERSMODEL
                        # OFFERSMODEL# OFFERSMODEL# OFFERSMODEL# OFFERSMODEL
                        # OFFERSMODEL# OFFERSMODEL# OFFERSMODEL# OFFERSMODEL



class ProductOffer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

class CategoryOffer(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

class ReferralOffer(models.Model):
    referrer = models.ForeignKey(User, related_name='referral_offers', on_delete=models.CASCADE)
    discount = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()