from django.db import models
from userauth.models import User
from userauth.models import Address
from app.models import Product,Variants,Coupon,ProductOffer,CategoryOffer  

# Create your models here.




class Payment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    payment_id = models.CharField(max_length=100)
    payment_method=models.CharField(max_length=100)
    amount_paid=models.CharField(max_length=100)
    status=models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)


    def __str__(self):
        return self.payment_id  
    

class Order(models.Model):
    STATUS = (
        ('New','New'),
        ('Order placed','Order placed'),
        ('Order confirmed','Order confirmed'),
        ('Order processing','Order processing'),
        ('Shipped','Shipped'),
        ('Delivered','Delivered'),
        ('Cancelled','Cancelled'),
    )

    user = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL,blank=True,null=True)
    billing_address = models.ForeignKey(Address, related_name='billing_orders', on_delete=models.CASCADE, null=True)
    shipping_address = models.ForeignKey(Address, related_name='shipping_orders', on_delete=models.CASCADE, null=True)
    offer_price = models.FloatField(blank=True,default=0)
    order_number = models.CharField(max_length=20)
    order_note = models.CharField(max_length=100,blank=True)
    order_total = models.FloatField()
    coupon = models.ForeignKey(Coupon,on_delete=models.SET_NULL,null=True,blank=True)
    shipping = models.FloatField(blank=True,default=0)
    status = models.CharField(max_length=100,choices=STATUS,default='New')
    ip = models.CharField(blank=True,max_length=20)
    is_ordered = models.BooleanField(default=False)
    refund_status = models.CharField(max_length=20, choices=[
        ('none', 'No Refund'),
        ('partial', 'Partial Refund'),
        ('full', 'Full Refund'),
    ], default='none')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField(auto_now=True)



    def __str__(self):
        return self.user.username

class OrderProduct(models.Model):
    ITEM_STATUS_CHOICES = (
        ('Ordered', 'Ordered'),
        ('Cancelled', 'Cancelled'),
        ('Returned', 'Returned'),
    )
    
    order = models.ForeignKey(Order,on_delete=models.CASCADE)
    payment = models.ForeignKey(Payment,on_delete=models.SET_NULL,blank=True,null=True)
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, blank=True, null=True)
    product = models.ForeignKey(Product,on_delete=models.CASCADE)
    variations = models.ManyToManyField(Variants,blank=True)
    size = models.CharField(max_length=50)
    quantity = models.IntegerField()
    product_price = models.FloatField()
    ordered = models.BooleanField(default=False)
    item_status = models.CharField(max_length=20, choices=ITEM_STATUS_CHOICES, default='Ordered')
    refunded = models.BooleanField(default=False)  # Track if this item has been refunded
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product.title
    


class ProductRating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='ratings')
    order_product = models.ForeignKey('OrderProduct', on_delete=models.CASCADE, null=True, blank=True)
    rating = models.PositiveIntegerField(default=0)  # 1 to 5
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'product')  # One rating per user per product

    def __str__(self):
        return f"{self.product.title} - {self.rating} stars"


