from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User  

class RegisterForm(UserCreationForm):
    name = forms.CharField(max_length=150, required=True)
    email = forms.EmailField(required=True)
    
    class Meta:
        model = User
        fields = ['name', 'email', 'password1', 'password2']