from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_loginn, name='store_login'),
    path('store_dashboard/', views.store_dashboardd, name='store_dashboard'),
    path('store_billing/', views.store_billingg, name='store_billing'),
    path('store_items/', views.store_itemss, name='store_items'),
    path('store_items_add/', views.store_items_addd, name='store_items_add'),
    path('store_items/store_items_edit/<str:id>/', views.store_items_editt, name='store_items_edit'),  # Update this line
    path('store_items_delete/<str:id>/', views.store_items_delete, name='store_items_delete'),
    path('store_report/', views.store_reportt, name='store_report'),
    path('admin_logout/', views.admin_logoutt, name='admin_logout'),
    path('store_pdf/', views.store_pdff, name='store_pdf'),
    path('download_exel/', views.excel_report, name='download_exel'),
    path('pdf_download/', views.DownloadPDF.as_view(), name='pdf_download'),
    path('check_stock/', views.check_stock, name='check_stock'),
    path('store_supplier/', views.store_supplierr, name='store_supplier'),
    path('store_supplier_add/', views.store_supplier_addd, name='store_supplier_add'),
    path('store_supplier_edit/<str:id>/', views.store_supplier_editt, name='store_supplier_edit'),  # Update this line
    path('store_supplier_delete/<str:id>/', views.store_supplier_delete, name='store_supplier_delete'),

    path('store_customer/', views.store_customerr, name='store_customer'),
    path('store_customer_add/', views.store_customer_addd, name='store_customer_add'),
    path('store_customer_edit/<str:id>/', views.store_customer_editt, name='store_customer_edit'),  # Update this line
    path('store_customer_delete/<str:id>/', views.store_customer_delete, name='store_customer_delete'),

]
