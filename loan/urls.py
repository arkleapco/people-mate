from django.urls import path, include
from loan import views

app_name= 'loan'

urlpatterns =[
    path('loan/', include([
            ######################### Loan Types URLs ###################################
          path('loan_type/list/', views.list_loan_types, name='loan-type-list'),
          path('loan_type/<int:pk>/', views.loan_type_view, name='get-loan-type'),
          path('loan_type/create/', views.create_loan_type, name='create-loan-type'),
          path('loan_type/update/<int:pk>/', views.update_loan_type, name='update-loan-type'),
          path('loan_type/delete/<int:pk>/', views.delete_loan_type, name='delete-loan-type'),
          ])),
]
