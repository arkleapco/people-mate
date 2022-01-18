from django.urls import path
from manage_payroll import views

app_name ='manage_payroll'

urlpatterns=[
    ######################### AssignmentBatch URLs ###################################
    path('assignment/batch/new/', views.createAssignmentBatchView, name='assignBatch-create'),
    path('assignment/batch/list/', views.listAssignmentBatchView , name='list-assignBatch'),
    path('assignment/batch/update/<int:pk>/', views.updateAssignmentBatchView, name='update-assignBatch'),
    path('assignment/batch/delete/<int:pk>/', views.deleteAssignmentBatchView, name='delete-assignBatch'),
    ######################### Payment URLs ###################################
    path('payment/new/', views.createPaymentView, name='payment-type-create'),
    path('payment/list/', views.listPaymentView , name='list-payments'),
    path('payment/update/<int:pk>/', views.updatePaymentView , name='update-payment'),
    path('payment/correct/<int:pk>/', views.correctPaymentView , name='correct-payment'),
    path('payment/delete/<int:pk>/', views.deletePaymentView , name='delete-payment'),
    ######################### Bank&Bank_Branch URLs ###################################
    path('bank/new/', views.createBankAccountView, name='bank-create'),
    path('bank/list/', views.listBankAccountsView, name='list-banks'),
    path('bank/update/<int:pk>/', views.updateBankAccountView, name='update-bank'),
    path('bank/delete/<int:pk>/', views.deleteBankAccountView, name='delete-bank'),
    ######################### Bank&Bank_Branch Reports URLs ################################
    path('cash/', views.get_cash_report, name='get-cash-report'),
    path('report/cash/<int:month>/<int:year>/<int:from_emp>/<int:to_emp>/', views.export_cash_report, name='export-cash-report'),
    
    path('bank/', views.get_bank_report, name='get-bank-report'),
    path('export/bank/<int:bank_id>/<int:month>/<int:year>/<int:from_emp>/<int:to_emp>/', views.export_bank_report, name='export-bank-report'),

    path('hold/', views.get_hold_report, name='get-hold-report'),
    path('report/cash/<int:month>/<int:year>/<int:from_emp>/<int:to_emp>/', views.export_hold_report, name='export-hold-report'),
    


    ######################### Payroll URLs ###################################
    path('payroll/new/', views.createPayrollView, name='payroll-create'),
    path('payroll/list/', views.listPayrollView, name='list-payroll'),
    path('payroll/update/<int:pk>/', views.updatePayrollView, name='update-payroll'),
    path('payroll/delete/<int:pk>/', views.deletePayrollView, name='delete-payroll'),
]
