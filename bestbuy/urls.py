from django.urls import path
from . import views

urlpatterns = [
    path('', views.store_loginn, name='store_login'),
    path('store_dashboard/', views.store_dashboardd, name='store_dashboard'),
    path('store_billing/', views.store_billingg, name='store_billing'),
    path('store_items/', views.store_itemss, name='store_items'),
    path('store_items_add/', views.store_items_addd, name='store_items_add'),
    path('store_items/store_items_edit/<str:id>/', views.store_items_editt, name='store_items_edit'),
    path('store_items/store_items_delete/<str:id>/', views.store_items_delete, name='store_items_delete'),
    path('store_report/', views.store_reportt, name='store_report'),
    path('admin_logout', views.admin_logoutt, name='admin_logout'),
    path('store_pdf/', views.store_pdff, name='store_pdf'),
    path('download_exel/', views.excel_report, name="download_exel"), 
    path('pdf_download/', views.DownloadPDF.as_view(), name='pdf_download'),
]
