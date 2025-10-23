from django import forms
from .models import Product
from orders.models import ProductRating

class ProductRatingForm(forms.ModelForm):
    class Meta:
        model = ProductRating
        fields = ['rating', 'review']
        widgets = {
            'rating': forms.Select(choices=[(i, f'{i} star{"s" if i > 1 else ""}') for i in range(1, 6)]),
            'review': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Write your review here...'})
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['rating'].widget.attrs.update({'class': 'form-control'})
        self.fields['review'].widget.attrs.update({'class': 'form-control'})
