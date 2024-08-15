from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth import login as admin_login, logout as admin_logout
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import user_passes_test
from .models import Product
from .forms import ProductForm
from django.core.exceptions import ObjectDoesNotExist
import uuid
from .models import Customer, Product, Order, OrderItem, Cart
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from decimal import Decimal



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


@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_billingg(request):
    product_list = Product.objects.all()
    order_id = str(uuid.uuid4().hex)[:15]

    if request.method == 'POST':
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':  # Check if request is AJAX
            data = json.loads(request.body)
            action = data.get('action')

            if action == 'add_to_cart':
                product_id = data.get('product_id')
                quantity = int(data.get('quantity'))
                tax = float(data.get('tax'))
                discount = float(data.get('discount'))
                product = Product.objects.get(id=product_id)

                # Convert values to Decimal for calculation
                price = Decimal(product.price)
                quantity = Decimal(quantity)
                tax = Decimal(tax)
                discount = Decimal(discount)

                # Calculate total amount for the cart item
                total_amount = (price * quantity) + (price * quantity * (tax / Decimal('100'))) - (price * quantity * (discount / Decimal('100')))

                # Add or update the cart item
                cart_item, created = Cart.objects.update_or_create(
                    product=product,
                    defaults={'quantity': quantity, 'price': price, 'tax': tax, 'discount': discount, 'total_amount': total_amount},
                )

                return JsonResponse({'status': 'success', 'message': 'Item added to cart successfully'})

        else:
            # Handle the final order confirmation
            name = request.POST.get('name')
            phone = request.POST.get('number')
            order_id = request.POST.get('order_id')
            date = request.POST.get('date')
            product_data = json.loads(request.POST.get('product_data', '[]'))

            # Save Customer
            customer = Customer(name=name, number=phone, order_id=order_id, date=date)
            customer.save()

            # Calculate the total amount from product_data before saving the order
            total_amount = Decimal('0.00')
            for product in product_data:
                product_id = product['id']
                quantity = Decimal(product['quantity'])
                tax = Decimal(product['tax'])
                discount = Decimal(product['discount'])
                
                product_instance = Product.objects.get(id=product_id)
                price = Decimal(product_instance.price)

                # Calculate item total
                item_total = (price * quantity) + (price * quantity * (tax / Decimal('100'))) - (price * quantity * (discount / Decimal('100')))
                total_amount += item_total

            # Save Order with the calculated total amount
            order = Order(customer=customer, total_amount=total_amount, order_id=order_id, date=date)
            order.save()

            # Store the order ID in the session
            request.session['order_id'] = order_id

            # Move items from product_data to OrderItem and update product quantities
            for product in product_data:
                product_id = product['id']
                quantity = Decimal(product['quantity'])
                tax = Decimal(product['tax'])
                discount = Decimal(product['discount'])
                
                product_instance = Product.objects.get(id=product_id)
                price = Decimal(product_instance.price)

                # Calculate item total
                item_total = (price * quantity) + (price * quantity * (tax / Decimal('100'))) - (price * quantity * (discount / Decimal('100')))
                
                order_item = OrderItem(
                    order=order,
                    product=product_instance,
                    quantity=quantity,
                    price=price,
                    tax=tax,
                    discount=discount,
                    total_amount=item_total
                )
                order_item.save()

                # Update product stock
                product_instance.stock -= quantity
                product_instance.save()

            # Clear the Cart after saving the order
            Cart.objects.all().delete()

            # Redirect to store_pdf after successful order
            return redirect('store_pdf')

    return render(request, 'store_billing.html', {'product_list': product_list, 'order_id': order_id})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_pdff(request):
    order_id = request.session.get('order_id')
    if not order_id:
        # Handle the case where no order ID is found in the session
        return redirect('store_billing')  # Redirect or show an error

    try:
        order = Order.objects.get(order_id=order_id)
        order_items = OrderItem.objects.filter(order=order)
        # Prepare data for PDF generation here
        
        # Clear the order ID from the session after use
        del request.session['order_id']

        return render(request, 'store_pdf.html', {'order': order, 'order_items': order_items})
    except Order.DoesNotExist:
        # Handle the case where the order does not exist
        return render(request, 'store_pdf.html', {'error_message': 'Order does not exist. Please try again.'})


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