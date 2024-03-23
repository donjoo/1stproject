from django.forms import ModelForm
from django import forms
from django.contrib.auth.forms import UserCreationForm
# from django.contrib.auth.models import User as AuthUser
from userauth.models import User,Address
from app.models import UserDetails





class CreateUserForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs= { "placeholder": "First Name" }), required=True, help_text= 'Required.30 characters or fewer.')
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs= { "placeholder": "Last Name" }), required=True, help_text= 'Required.30 characters or fewer.')
    email = forms.EmailField(max_length=245, widget=forms.EmailInput(attrs= { "placeholder": "Email" }), required=True, help_text= 'Required.Enter a vailed email address.')
    password1=forms.CharField(max_length=30, widget=forms.PasswordInput(attrs= { "placeholder": "Password" }), required=True, help_text= 'Required.30 characters or fewer.')
    password2=forms.CharField(max_length=30, widget=forms.PasswordInput(attrs= { "placeholder": " Confirm Password" }), required=True, help_text= 'Required. 30 characters or fewer.')
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs= { "placeholder": "Username" }), required=True, help_text= 'Required. 30 characters or fewer.')
    class Meta:
        model = User
        fields = ['username','first_name','last_name','email','password1','password2']


class Profileform(forms.ModelForm):
    full_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder":"Full Name"}))
    bio = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder":"Bio"}))
    phone = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder":"phone"}))

    class Meta:
        model = UserDetails
        fields = ['full_name','image','bio','phone']




class PasswordChangeForm(UserCreationForm):
    password1 = forms.CharField(max_length=30,widget=forms.PasswordInput(attrs={"placeholder":"New Password"}),required=True, help_text='Required. 30 characters or fewer.')
    password2 = forms.CharField(max_length=30,widget=forms.PasswordInput(attrs = {"placeholder":"Confirm Password"}), required=True, help_text='Required. 30 characters or fewer.')

    class Meta:
        model = User
        fields = ['password1','password2']


    

class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = ['user', 'house', 'street', 'landmark', 'pincode', 'town', 'state', 'status']



class AddFundsForm(forms.Form):
    amount = forms.DecimalField(max_digits=10, decimal_places=2, min_value=0)
