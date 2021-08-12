from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

class RegistrationForm(forms.Form):
    user_login = forms.CharField(label='Login', max_length=30)
    user_password = forms.CharField(label='Password', min_length=8, widget=forms.PasswordInput())
    confirm_password = forms.CharField(label='Confirm password', min_length=8, widget=forms.PasswordInput())
    user_name = forms.CharField(label='Your name', max_length=30)
    user_surname = forms.CharField(label='Your surname', max_length=30  )
    user_email = forms.EmailField(label="E-mail")

    def clean(self):
        username = self.cleaned_data.get('user_login')
        email = self.cleaned_data.get('user_email')
        if User.objects.filter(username=username).exists():
            raise ValidationError("Login exists")
        elif User.objects.filter(email=email).exists():
            raise ValidationError("Email exists")
        return self.cleaned_data