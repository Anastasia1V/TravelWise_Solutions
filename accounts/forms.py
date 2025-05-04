from django import forms
import hashlib
from django.contrib.auth import authenticate
from .models import CustomUser


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=100)
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput)

    def clean_name(self):
        n = self.cleaned_data['name']
        h = hashlib.sha256(n.encode()).hexdigest()
        if CustomUser.objects.filter(name_hash=h).exists():
            raise forms.ValidationError("Это имя уже занято.")
        return n

    def clean_email(self):
        e = self.cleaned_data['email']
        h = hashlib.sha256(e.encode()).hexdigest()
        if CustomUser.objects.filter(email_hash=h).exists():
            raise forms.ValidationError("Этот email уже зарегистрирован.")
        return e

    def save(self):
        name = self.cleaned_data['name']
        email = self.cleaned_data['email']
        password = self.cleaned_data['password']
        CustomUser.objects.create_user(email, name, password)


class LoginForm(forms.Form):
    name = forms.CharField(max_length=100)
    password = forms.CharField(widget=forms.PasswordInput)

    def clean(self):
        n = self.cleaned_data.get('name')
        p = self.cleaned_data.get('password')
        h_name = hashlib.sha256(n.encode()).hexdigest()
        user = authenticate(username=h_name, password=p)
        if user is None:
            raise forms.ValidationError("Неверно введён логин или пароль")
        self.user = user
        return self.cleaned_data
