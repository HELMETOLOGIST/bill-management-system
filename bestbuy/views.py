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
import xlwt
from datetime import date, datetime
import datetime
from datetime import timedelta
from django.http import HttpResponse
from io import BytesIO
from xhtml2pdf import pisa
from django.template.loader import get_template
from django.views import View
from .utils import render_to_pdf
from django.utils.decorators import method_decorator
from django.db.models import Sum, Count
import json
from datetime import datetime, timedelta, date
from django.utils import timezone



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
    filter_value = request.GET.get('filter_value')  # 'today', 'this_month', or 'this_year'
    end_time = datetime.now()

    if filter_value == 'today':
        start_time = end_time - timedelta(days=1)
    elif filter_value == 'this_month':
        start_time = end_time.replace(day=1)
    elif filter_value == 'this_year':
        start_time = end_time.replace(month=1, day=1)
    else:
        start_time = end_time - timedelta(days=1)

    # Adjusting for `DateField`
    orders = Order.objects.filter(date__range=[start_time, end_time])
    revenue = orders.aggregate(total_revenue=Sum('total_amount'))['total_revenue']
    customers = Customer.objects.filter(order__in=orders).distinct().count()

    # Recent activity: fetch the latest customers
    recent_customers = Customer.objects.all().order_by('-date')[:5]

    # Line chart data for the last 7 days
    chart_end_time = datetime.now()
    weekday_orders = []

    for days_ago in range(6, -1, -1):
        start_date = chart_end_time - timedelta(days=days_ago + 1)
        end_date = start_date + timedelta(days=1)
        day_orders = OrderItem.objects.filter(order__date__range=(start_date, end_date)).count()
        weekday_orders.append({'date': start_date.strftime("%A"), 'count': day_orders})

    # Monthly and yearly data
    month_orders = []
    for month in range(1, 13):
        start_date = date(chart_end_time.year, month, 1)
        if month == 12:
            end_date = date(chart_end_time.year + 1, 1, 1)
        else:
            end_date = date(chart_end_time.year, month + 1, 1)
        month_orders.append({'date': start_date.strftime("%B"), 'count': OrderItem.objects.filter(order__date__range=(start_date, end_date)).count()})
    month_orders.reverse()

    year_orders = []
    for year in range(2024, 2018, -1):
        year_orders.append({'date': year, 'count': OrderItem.objects.filter(order__date__year=year).count()})
    year_orders.reverse()

    # Order counts for the selected time range
    orders_chart = Order.objects.filter(date__range=[start_time, end_time])
    order_counts = {
        'day': orders_chart.filter(date=end_time.date()).count(),
        'month': orders_chart.filter(date__month=end_time.month).count(),
        'year': orders_chart.filter(date__year=end_time.year).count(),
    }

    # Payment method and category data for charts

    context = {
        'revenue': revenue,
        'customers': customers,
        'orders': orders.count(),
        'recent_customers': recent_customers,
        'order_counts': order_counts,
        'weekday_orders_json': json.dumps(weekday_orders),
        'month_orders_json': json.dumps(month_orders),
        'year_orders_json': json.dumps(year_orders),
    }

    return render(request, 'store_dashboard.html', context)


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
@user_passes_test(lambda u: u.is_superuser, login_url="admin_login")
def store_reportt(request):
    # Get start_date and end_date from request parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize a queryset with all OrderItems
    items = OrderItem.objects.all().order_by("-order__date")

    # Check if start_date and end_date are provided for filtering
    if start_date and end_date:
        # Filter orders based on the provided date range
        items = items.filter(order__date__range=[start_date, end_date])

    context = {
        'items': items,
    }

    return render(request, 'store_report.html', context)



def excel_report(request):
    response = HttpResponse(content_type="application/ms-excel")
    response["Content-Disposition"] = (
        "attachment; filename=SalesReport-" + str(datetime.now().strftime('%Y-%m-%d_%H-%M-%S')) + ".xls"
    )
    
    work_b = xlwt.Workbook(encoding="utf-8")
    work_s = work_b.add_sheet("SalesReport")
    
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    
    # Define the columns for the Excel report
    columns = [
        "Order ID",
        "Customer Name",
        "Order Date",
        "Product Name",
        "Quantity",
        "Unit Price",
        "Tax",
        "Discount",
        "Total Amount",
    ]
    
    # Write the column headers
    for column_num in range(len(columns)):
        work_s.write(row_num, column_num, columns[column_num], font_style)
    
    font_style = xlwt.XFStyle()

    # Date filters
    start_date = request.GET.get("start_date")
    end_date = request.GET.get("end_date")

    if not start_date:
        start_date = datetime.now() - timedelta(days=3 * 365)  # Default to 3 years ago

    if not end_date:
        end_date = datetime.now()

    # Query orders and related data
    orders = (
        Order.objects.filter(date__range=[start_date, end_date])
        .select_related("customer")
        .prefetch_related("items__product")
        .order_by("-date")
    )
    
    total_sum = 0  # Variable to hold the total amount sum

    # Iterate over orders and write data to the Excel sheet
    for order in orders:
        for item in order.items.all():
            row_num += 1
            work_s.write(row_num, 0, order.order_id, font_style)
            work_s.write(row_num, 1, order.customer.name, font_style)
            work_s.write(row_num, 2, order.date.strftime('%Y-%m-%d'), font_style)
            work_s.write(row_num, 3, item.product.name, font_style)
            work_s.write(row_num, 4, item.quantity, font_style)
            work_s.write(row_num, 5, item.price, font_style)
            work_s.write(row_num, 6, item.tax, font_style)
            work_s.write(row_num, 7, item.discount, font_style)
            work_s.write(row_num, 8, item.total_amount, font_style)
            
            total_sum += item.total_amount  # Add the total amount to the sum
    
    # Write the total amount sum to a new row
    row_num += 1
    work_s.write(row_num, 8, 'Total Sum', font_style)  # Label for the sum
    work_s.write(row_num, 9, total_sum, font_style)  # Total amount sum
    
    # Save the workbook
    work_b.save(response)

    return response



class DownloadPDF(View):
    def get(self, request, *args, **kwargs):
        start_date = request.GET.get("start_date")
        end_date = request.GET.get("end_date")
        now = datetime.now()

        if not start_date:
            start_date = now - timedelta(days=3 * 365)  # Default to 3 years ago

        if not end_date:
            end_date = now

        # Query orders and related data
        orders = Order.objects.filter(date__range=[start_date, end_date]).order_by("-date")
        order_items = OrderItem.objects.filter(order__in=orders)

        # Calculate the total amount for all order items
        total_price = sum(item.total_amount for item in order_items)

        # Prepare context data
        data = {
            "company": "Best Buy",
            "address": "Address Placeholder",  # Update with actual data if needed
            "city": "Palakkad",
            "state": "Kerala",
            "zipcode": "673006",
            "orders": orders,
            "order_items": order_items,
            "phone": "Phone Placeholder",  # Update with actual data if needed
            "email": "example@mail.com",
            "website": "example.com",
            "total_price": total_price,  # Total amount for the PDF
        }

        pdf = render_to_pdf("store_report_pdf.html", data)

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            filename = f"Sales_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            content = f"attachment; filename={filename}"
            response["Content-Disposition"] = content
            return response

        return HttpResponse("Error generating PDF", status=500)