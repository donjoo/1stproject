from django import forms
from .models import Order



# class OrderForm()


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['billing_address', 'shipping_address', 'order_note','shipping']