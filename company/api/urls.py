from django.urls import path, include
from company.api import views

app_name = 'company'

urlpatterns = [
    ######################### API URLs ###################################
    path('test', views.test, name='test'),   
]