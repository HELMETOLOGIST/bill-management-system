from django.urls import path
from . import views


urlpatterns = [
    path('',views.store_loginn,name='store_login'),
]