from django.urls import path
from . import views


urlpatterns = [
    path('',views.store_loginn,name='store_login'),
    path('store_dashboard/',views.store_dashboardd,name='store_dashboard'),
    path('store_billing/',views.store_billingg,name='store_billing'),
    path('store_items/',views.store_itemss,name='store_items'),
    path('store_report/',views.store_reportt,name='store_report'),

]