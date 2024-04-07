from django import forms
from .models import Order
from django.core.exceptions import ValidationError



# class OrderForm()


class OrderForm(forms.ModelForm):
    class Meta:
        model = Order
        fields = ['billing_address', 'shipping_address', 'order_note','shipping']


    
    def clean(self):
        cleaned_data = super().clean()
        billing_address = cleaned_data.get('billing_address')
        shipping_address = cleaned_data.get('shipping_address')

        if not billing_address and not shipping_address:
            raise ValidationError("Please provide at least one address (billing or shipping)")

        return cleaned_data