from django.shortcuts import render
from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth import login as admin_login, logout as admin_logout
from django.contrib import messages

# Create your views here.
'''
Admin login logic implementation only
'''
def store_loginn(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('store_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        admin = authenticate(request, username=username,password=password)
        if admin is not None and admin.is_superuser:
            admin_login(request,admin)
            return redirect('store_admin')
        else:
            messages.error(request, "Username or Password incorrect")
            return redirect('store_login')
    else:
        return render(request, 'store_login.html') 