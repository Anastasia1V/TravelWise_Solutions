from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import RegistrationForm, LoginForm


def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Пользователь зарегестрирован.")
            return redirect('accounts:login')
    else:
        form = RegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})


def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            login(request, form.user)
            return redirect('accounts:welcome')
    else:
        form = LoginForm()
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def welcome_view(request):
    return render(request, 'accounts/welcome.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('accounts:login')


def home_redirect_view(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return redirect('accounts:login')
