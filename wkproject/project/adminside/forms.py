from django import forms 
from app.models import Product,ProductImage,ProductVariants,ProductOffer,CategoryOffer
from django.core.exceptions import ValidationError
from decimal import Decimal
from app.models import ProductImage,SIZE_CHOICES,Coupon

class CreateProductForm(forms.ModelForm):
    new_image=forms.ImageField(required=False)

    class Meta:
        model = Product
        fields = ['title','category','old_price','price','descriptions','new_image','fit','fabric','care','sleeve','collar', 'specifications']

    def __init__(self,*args, **kwargs):
        super().__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class']='form-control'


    def clean_price(self):
        old_price  = self.cleaned_data.get('old_price')

        if old_price is not None and old_price < Decimal('0'):
            raise ValidationError("price cannot be negative.")
        return old_price
    
class ProductImageForm(forms.ModelForm):
    class Meta:
        model = ProductImage
        fields = ['Images']      

class ProductVariantForm(forms.Form):
    product = forms.CharField(label='Product', widget=forms.Select(choices=[]))
    stock_count_s = forms.IntegerField(label='Stock Count (S)', min_value=0, required=True)
    stock_count_m = forms.IntegerField(label='Stock Count (M)', min_value=0, required=True)
    stock_count_l = forms.IntegerField(label='Stock Count (L)', min_value=0, required=True)
    stock_count_xl = forms.IntegerField(label='Stock Count (XL)', min_value=0, required=True)
    stock_count_xxl = forms.IntegerField(label='Stock Count (XXL)', min_value=0, required=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['product'].widget.choices = [(product.title, product.title) for product in Product.objects.all()]



class CouponForm(forms.ModelForm):
    class Meta:
        model = Coupon 
        fields = ['code','discount','valid_from','valid_to','active']
        widgets = {
            'valid_from': forms.DateInput(attrs={'type': 'date','style': 'width: 150px;'}),
            'valid_to': forms.DateInput(attrs={'type': 'date','style':'width:150px;'})
        }
    def clean_discount(self):
        discount = self.cleaned_data.get('discount')
        if discount > 100:
            raise forms.ValidationError("Discount must be less that or equal to 100")
        return discount
    active = forms.BooleanField(widget=forms.CheckboxInput(attrs={'style': 'width: 20px; height: 20px;'}))
class ProductOfferForm(forms.ModelForm):
    class Meta:
        model = ProductOffer
        fields = ['product','discount','start_date','end_date']
        widgets = {
            'start_date': forms.DateInput(attrs={'type':'date','style':'width:150px;'}),
            'end_date': forms.DateInput(attrs={'type':'date','style':'width:150px;'}),
        }

class CategoryOfferForm(forms.ModelForm):
    class Meta:
        model = CategoryOffer
        fields = ['category','discount','start_date','end_date']
        widgets = {
            'start_date': forms.DateInput(attrs ={'type':'date','style':'width:150px;'}),
            'end_date':forms.DateInput(attrs={'type':'date','style':'width:150px;'}),
        }