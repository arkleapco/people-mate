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
        path('creat/employee/company/insurance/report/',views.get_month_year_employee_company_insurance_report, name='creat-employee-company-insurance-report'), 
        
        path('payroll/export/information/<int:from_month>/<int:to_month>/<int:year>/<int:from_emp>/<int:to_emp>',views.export_employees_information, name='export-payroll_information'),
        path('payroll/print/<int:from_month>/<int:to_month>/<int:year>/<int:from_emp>/<int:to_emp>',views.get_employees_information, name='print-payroll'),
        path('payroll/export/<int:from_month>/<int:to_month>/<int:year>/<int:from_emp>/<int:to_emp>',views.export_employees_payroll_elements, name='export-payroll'), 
        
        path('payroll/print/employees/company/insurance/share/<int:from_month>/<int:to_month>/<int:year>/<int:from_emp>/<int:to_emp>',views.print_employees_company_insurance_share, name='print-employees-company-insurance-share'),
        path('payroll/export/employees/company/insurance/share/<int:from_month>/<int:to_month>/<int:year>/<int:from_emp>/<int:to_emp>',views.export_employees_company_insurance_share, name='export-export-employees-company-insurance-share'),
        path('get/bank/',views.get_bank_report, name='bank-report'),
        path('payroll/bank/export/<int:bank_id>/',views.export_bank_report, name='export-bank-report'),

        path('export/deduction/report',views.export_deduction_report, name='deduction-report'),
        path('export/total_elements/report',views.export_total_elements_report, name='total_elements-report'),




        
        
        
        
        
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
        path('payslip/create/<int:month>/<int:year>/<int:batch>',
             views.render_all_payslip, name='all-emp-payslip'),
    ])),
]