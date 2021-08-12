from django import forms

class LoginForm(forms.Form):
    username= forms.CharField(label='Login', min_length=3)
    password = forms.CharField(label='Password', widget=forms.PasswordInput())