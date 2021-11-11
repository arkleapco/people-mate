from django.urls import path, include
from company.api import views

app_name = 'api_company'

urlpatterns = [
    ######################### API URLs ###################################
    path('list/company', views.list_company, name='list-company'),
    # path('list/department', views.get_department_response, name='import-department'),
    # path('list/job', views.list_job, name='import-job'),   
    # path('list/grade', views.list_grade, name='import-grade'),   
    # path('list/position', views.list_position, name='import-position'),   

   
    
]