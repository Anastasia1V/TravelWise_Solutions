from django.shortcuts import redirect


def home_redirect(request, *args, **kwargs):
    if request.user.is_authenticated:
        return redirect('accounts:welcome')
    return redirect('accounts:login')
