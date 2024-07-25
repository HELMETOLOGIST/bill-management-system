from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth import login as admin_login, logout as admin_logout
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import user_passes_test
from .models import Product
from .forms import ProductForm
from django.core.exceptions import ObjectDoesNotExist



# Create your views here.
'''
Admin login logic implementation only
'''
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def store_loginn(request):
    if request.user.is_authenticated and request.user.is_superuser:
        return redirect('store_dashboard')
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        admin = authenticate(request, username=username,password=password)
        if admin is not None and admin.is_superuser:
            admin_login(request,admin)
            return redirect('store_dashboard')
        else:
            messages.error(request, "Username or Password incorrect")
            return redirect('store_login')
    else:
        return render(request, 'store_login.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def admin_logoutt(request):
    admin_logout(request)
    return redirect('store_login')
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_dashboardd(request):
    return render(request, 'store_dashboard.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_billingg(request):
    return render(request, 'store_billing.html')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_itemss(request):
    products = Product.objects.all()
    return render(request, 'store_items.html', {'products': products})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_items_addd(request):
    if request.method == 'POST':
        product_name = request.POST.get('product_name')
        stock = request.POST.get('stock')
        price = request.POST.get('price')
        try:
            existing_product = Product.objects.get(name__iexact=product_name)
            messages.error(request, 'This product already added')
            return redirect("store_items_add")
        except ObjectDoesNotExist:
            pass

        product = Product(
            name=product_name,
            stock=stock,
            price=price,
        )
        product.save()
        messages.success(request, 'Product added successfully')
        return redirect("store_items_add")
    else:
        return render(request, 'store_items_add.html')
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_items_editt(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        edit_name = request.POST.get('product_name')
        edit_stock = request.POST.get('stock')
        edit_price = request.POST.get('price')

        product.name = edit_name
        product.stock = edit_stock
        product.price = edit_price
        product.save()
        return redirect('store_items')
    return render(request, 'store_items_edit.html', {'product': product})


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_items_delete(request, id):
    product = get_object_or_404(Product, id=id)
    product.delete()
    messages.success(request, 'Product deleted successfully')
    return redirect('store_items')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_reportt(request):
    return render(request, 'store_report.html')