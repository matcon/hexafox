from django.shortcuts import render, redirect
from django.contrib.auth import logout

def user_login(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'login.html')

def user_logout(request):
    logout(request)
    return redirect('login')
