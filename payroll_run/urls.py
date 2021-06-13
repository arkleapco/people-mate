from django.urls import path, include

from payroll_run import views

app_name = 'payroll_run'

urlpatterns = [
    path('salary/', include([
        path('list/', views.listSalaryView, name='list-salary'),
        path('month/list/<int:month>/<int:year>/<int:batch_id>',
             views.listSalaryFromMonth, name='list-month-salary'),
        path('finalize/<int:month>/<int:year>/',
             views.changeSalaryToFinal, name='finalize-salary'),
        path('delete/<int:month>/<int:year>/',
             views.delete_salary_view, name='delete-salary'),
        path('delete/<int:pk>/',views.deleteSalaryFromMonth, name='delete-salary-month'),  
        path('creat/report/',views.get_month_year_to_payslip_report, name='creat-report'), 
        path('payroll/print/<int:month>/<int:year>/',views.get_employees_information, name='print-payroll'), 
        path('payroll/print/<int:month_number>/<int:salary_year>/<int:salary_id>/<int:emp_id>',views.render_payslip_report, name='payslip-report'), 
        path('month/emp/<int:month_number>/<int:salary_year>/<int:salary_id>/<int:emp_id>/', include([
            path('<slug:tmp_format>',
                 views.userSalaryInformation, name='emp-payslip'),
            path('<slug:tmp_format>', views.userSalaryInformation,
                 name='emp-payslip-report'),
        ])),
        path('create/', views.createSalaryView, name='create-salary'),
        path('ajax/validate_payslip/', views.ValidatePayslip, name='validate-payslip'),
        path('ajax/delete_old_payslip/', views.DeleteOldPayslip, name='delete-old-payslip'),
        path('payslip/create/<int:month>/<int:year>/<int:salary_id>/<int:emp_id>/',
             views.render_emp_payslip, name='genereate-salary'),
        path('payslip/create/<int:month>/<int:year>/',
             views.render_all_payslip, name='all-emp-payslip'),
    ])),
]
