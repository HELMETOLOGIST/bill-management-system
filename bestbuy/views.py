from django.shortcuts import render,redirect,get_object_or_404
from django.contrib.auth import authenticate
from django.contrib.auth import login as admin_login, logout as admin_logout
from django.contrib import messages
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import user_passes_test
from .models import Product
import uuid
from .models import Customer, Product, Order, OrderItem, Cart, CustomerTransaction, Supplier
from django.contrib.auth.decorators import login_required
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
from django.db.models import Sum
import json
from datetime import datetime, timedelta, date
from django.http import JsonResponse
from django.contrib import messages
from django.http import HttpResponseForbidden
import logging


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
    recent_customers = Customer.objects.all().order_by('-date')[:15]

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

    # Check if the generated order_id already exists in the Order model
    while Order.objects.filter(order_id=order_id).exists():
        order_id = str(uuid.uuid4().hex)[:15]  # Regenerate the order_id if it already exists

    gst_applied = False  # Default to False

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

                # Check if the product is in stock
                if product.stock <= 0:
                    return JsonResponse({'status': 'error', 'message': 'Product is out of stock'})

                # Check if the requested quantity is available
                if product.stock < quantity:
                    return JsonResponse({'status': 'error', 'message': 'Not enough stock available'})

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

            # Set gst_applied based on POST data (expected to be 'true' or 'false' as string)
            gst_applied = request.POST.get('gst_applied', 'false') == 'true'

            # Check if the order_id already exists in the database
            if Order.objects.filter(order_id=order_id).exists():
                return JsonResponse({'status': 'error', 'message': 'Order ID already exists'})

            # Save Customer
            customer = Customer(name=name, number=phone, order_id=order_id, date=date)
            customer.save()

            # Calculate the total amount from product_data before saving the order
            total_amount = Decimal('0.00')
            subTotal = Decimal('0.00')  # Initialize subTotal
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
                subTotal += item_total  # Accumulate subTotal

            subAmount = float(subTotal)
            if gst_applied:
                gst_rate = Decimal('18.00')  # 18% GST
                gst_amount = total_amount * (gst_rate / Decimal('100'))
                total_amount += gst_amount

            # Save Order with the calculated total amount
            order = Order(customer=customer, total_amount=total_amount, order_id=order_id, date=date)
            order.save()

            # Store the order ID in the session
            request.session['order_id'] = order_id
            request.session['subAmount'] = subAmount
            request.session['gst_applied'] = gst_applied  # Store gst_applied in session

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

    in_stock_products = product_list.filter(stock__gt=0)

    return render(request, 'store_billing.html', {'product_list': in_stock_products, 'order_id': order_id})

@csrf_exempt
@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def check_stock(request):
    if request.method == 'GET':
        product_id = request.GET.get('product_id')
        quantity = int(request.GET.get('quantity'))
        product = Product.objects.get(id=product_id)

        if product.stock >= quantity:
            return JsonResponse({'in_stock': True})
        else:
            return JsonResponse({'in_stock': False})




@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_pdff(request):
    order_id = request.session.get('order_id')
    subAmount = request.session.get('subAmount')
    gst_applied = request.session.get('gst_applied')

    if not order_id:
        # Handle the case where no order ID is found in the session
        return redirect('store_billing')  # Redirect or show an error

    try:
        order = Order.objects.get(order_id=order_id)
        order_items = OrderItem.objects.filter(order=order)

        # Clear the order ID from the session after use
        del request.session['order_id']
        del request.session['subAmount']
        del request.session['gst_applied']

        # Prepare data for PDF generation (if required)
        # For example, you could create a PDF file here or just render the HTML
        
        return render(request, 'store_pdf.html', {'order': order, 'order_items': order_items, 'subAmount': subAmount, 'gst_applied': gst_applied})
    except Order.DoesNotExist:
        # Handle the case where the order does not exist
        return render(request, 'store_pdf.html', {'error_message': 'Order does not exist. Please try again.'})
    except Exception as e:
        # Handle unexpected exceptions
        return render(request, 'store_pdf.html', {'error_message': 'An error occurred while generating the invoice.'})


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
        product_cost = request.POST.get('product_cost')
        price = request.POST.get('price')
        
        # Check if a product with the same name already exists
        if Product.objects.filter(name__iexact=product_name).exists():
            return JsonResponse({'duplicate': True})

        # Add the new product
        product = Product(
            name=product_name,
            stock=stock,
            product_cost=product_cost,
            price=price,
        )
        product.save()
        return JsonResponse({'success': True})

    return render(request, 'store_items_add.html')
    

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_items_editt(request, id):
    product = get_object_or_404(Product, id=id)
    if request.method == 'POST':
        edit_name = request.POST.get('product_name')
        edit_stock = request.POST.get('stock')
        edit_product_cost = request.POST.get('product_cost')
        edit_price = request.POST.get('price')

        # Validation logic
        if not (edit_name and len(edit_name) >= 3):
            return JsonResponse({'success': False, 'message': 'Product name must be at least 3 characters long'})
        if not edit_stock.isdigit():
            return JsonResponse({'success': False, 'message': 'Stock must be an integer'})
        if not edit_price.isdigit():
            return JsonResponse({'success': False, 'message': 'Price must be an integer'})
        if not edit_product_cost.isdigit():
            return JsonResponse({'success': False, 'message': 'Product Cost must be an integer'})

        # Update the product
        product.name = edit_name
        product.stock = int(edit_stock)
        product.product_cost = int(edit_product_cost)
        product.price = int(edit_price)
        product.save()
        return JsonResponse({'success': True, 'message': 'Product updated successfully'})
    
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
    # Get start_date and end_date from request parameters
    start_date = request.GET.get('start_date')
    end_date = request.GET.get('end_date')

    # Initialize a queryset with all OrderItems
    items = OrderItem.objects.all().order_by("-order__date")

    # Check if start_date and end_date are provided for filtering
    if start_date and end_date:
        # Filter orders based on the provided date range
        items = items.filter(order__date__range=[start_date, end_date])
    
    total_profit = sum(item.profit for item in items)  # Calculate total profit

    context = {
        'items': items,
        'total_profit': total_profit,
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
        "Profit",
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
    total_profit = 0

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
            work_s.write(row_num, 9, item.profit, font_style)
            
            total_sum += item.total_amount  # Add the total amount to the sum
            total_profit += item.profit
    
    # Write the total amount sum to a new row
    row_num += 1
    work_s.write(row_num, 8, 'Total Sum', font_style)  # Label for the sum
    work_s.write(row_num, 9, total_sum, font_style)  # Total amount sum

    row_num += 1
    work_s.write(row_num, 8, 'Total Profit', font_style)  # Label for total profit
    work_s.write(row_num, 9, total_profit, font_style)  # Total profit sum
    
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
        total_profit = sum(item.profit for item in order_items)  # Calculate total profit


        # Prepare context data
        data = {
            "company": "Best Buy",
            "address": "KOTHAKURUSSI, Ottapalam - Cherppulassery Rd, near SBI ATM, Kerala 679503",  # Update with actual data if needed
            "city": "Palakkad",
            "state": "Kerala",
            "zipcode": "679503",
            "orders": orders,
            "order_items": order_items,
            "phone": "+917907970271",  # Update with actual data if needed
            "email": "nafsalbabunkm@gmail.com",
            "website": "bestbuy.in",
            "total_price": total_price,  # Total amount for the PDF
            "total_profit": total_profit,  # Include total profit in the PDF
        }

        pdf = render_to_pdf("store_report_pdf.html", data)

        if pdf:
            response = HttpResponse(pdf, content_type="application/pdf")
            filename = f"Sales_report_{datetime.now().strftime('%Y-%m-%d_%H-%M-%S')}.pdf"
            content = f"attachment; filename={filename}"
            response["Content-Disposition"] = content
            return response

        return HttpResponse("Error generating PDF", status=500)
    

def render_to_pdf(template_src, context_dict={}):
    template = get_template(template_src)
    html = template.render(context_dict)
    result = BytesIO()
    
    # Ensure that utf-8 encoding is used
    pdf = pisa.pisaDocument(BytesIO(html.encode('UTF-8')), result, encoding='UTF-8')
    
    if not pdf.err:
        return HttpResponse(result.getvalue(), content_type='application/pdf')
    return None


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_supplierr(request):
    suppliers = Supplier.objects.all()
    return render(request, 'store_supplier.html', {'suppliers': suppliers})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_supplier_addd(request):
    if request.method == 'POST':
        name = request.POST.get('supplier_name')
        phone_number = request.POST.get('phone_number')
        product_name = request.POST.get('product_name')
        quantity = request.POST.get('quantity')
        credit = request.POST.get('credit')
        debit = request.POST.get('debit')

        supplier = Supplier(
            name=name,
            phone_number=phone_number,
            product_name=product_name,
            quantity=quantity,
            credit=credit,
            debit=debit
        )
        supplier.save()
        return JsonResponse({'success':True})

    return render(request, 'store_supplier_add.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_supplier_editt(request,id):
    supplier = get_object_or_404(Supplier, id=id)
    if request.method == 'POST':
        name = request.POST.get('supplier_name')
        phone_number = request.POST.get('phone_number')
        product_name = request.POST.get('product_name')
        quantity = request.POST.get('quantity')
        credit = request.POST.get('credit')
        debit = request.POST.get('debit')

         # Validation logic
        if not (name and len(name) >= 3):
            return JsonResponse({'success': False, 'message': 'Supplier name must be at least 3 characters long'})
        if not phone_number.isdigit():
            return JsonResponse({'success': False, 'message': 'Phone number must be an integer'})
        if not (product_name and len(product_name) >= 3):
            return JsonResponse({'success': False, 'message': 'Product name must be at least 3 characters long'})
        if not quantity.isdigit():
            return JsonResponse({'success': False, 'message': 'Quantity must be an integer'})
        if not credit.isdigit():
            return JsonResponse({'success': False, 'message': 'Credit must be an integer'})
        if not debit.isdigit():
            return JsonResponse({'success': False, 'message': 'Debit must be an integer'})
        
        supplier.name = name
        supplier.phone_number = phone_number
        supplier.product_name = product_name
        supplier.quantity = quantity
        supplier.credit = credit
        supplier.debit = debit
        supplier.save()
        return JsonResponse({'success': True, 'message': 'Supplier details updated successfully'})

    return render(request, 'store_supplier_edit.html', {'supplier': supplier})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_supplier_delete(request, id):
    supplier = get_object_or_404(Supplier, id=id)
    supplier.delete()
    messages.success(request, 'Supplier deleted successfully')
    return redirect('store_supplier')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_customerr(request):
    customers = CustomerTransaction.objects.all()
    return render(request, 'store_customer.html', {'customers': customers})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_customer_addd(request):
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        credit = request.POST.get('credit')
        debit = request.POST.get('debit')

        customer = CustomerTransaction(
            customer_name=customer_name,
            phone_number=phone_number,
            credit=credit,
            debit=debit
        )
        customer.save()
        return JsonResponse({'success':True})

    return render(request, 'store_customer_add.html')

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_customer_editt(request,id):
    customer = get_object_or_404(CustomerTransaction, id=id)
    if request.method == 'POST':
        customer_name = request.POST.get('customer_name')
        phone_number = request.POST.get('phone_number')
        credit = request.POST.get('credit')
        debit = request.POST.get('debit')

        if not (customer_name and len(customer_name) >= 3):
            return JsonResponse({'success': False, 'message': 'Customer name must be at least 3 characters long'})
        if not phone_number.isdigit():
            return JsonResponse({'success': False, 'message': 'Phone number must be an integer'})
        if not credit.isdigit():
            return JsonResponse({'success': False, 'message': 'Credit must be an integer'})
        if not debit.isdigit():
            return JsonResponse({'success': False, 'message': 'Debit must be an integer'})
        
        customer.customer_name = customer_name
        customer.phone_number = phone_number
        customer.credit = int(credit)
        customer.debit = int(debit)
        customer.save()
        return JsonResponse({'success': True, 'message': 'Customer details updated successfully'})

    return render(request, 'store_customer_edit.html', {'customer': customer})

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def store_customer_delete(request, id):
    customer = get_object_or_404(CustomerTransaction, id=id)
    customer.delete()
    messages.success(request, 'Customer Transaction deleted successfully')
    return redirect('store_customer')


@cache_control(no_cache=True, must_revalidate=True, no_store=True)
@user_passes_test(lambda u: u.is_superuser, login_url="store_login")
def splashh(request):
    return render(request, 'splash.html')