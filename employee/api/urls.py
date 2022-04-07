from django.urls import path, include
from employee.api import views
from employee.api import import_temp

app_name = 'api_employee'

urlpatterns = [
    ######################### API URLs ###################################
    path('import/employees', views.list_employees, name='import-employees'),
    path('import/temp', import_temp.list_employees, name='temp-employees'),


]