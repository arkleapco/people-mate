from django.urls import path, include
from django.contrib.auth.decorators import login_required
from employee import views
from urllib.parse import quote
from django.utils.encoding import iri_to_uri, uri_to_iri

app_name= 'employee'

urlpatterns =[
    path('employee/', include([
            ######################### Employee URLs ###################################
            path('new/', views.createEmployeeView, name='employee-create'),
            path('element/', views.copy_element_values, name='element-create'),
            path('information/listT/', views.listEmployeeView , name='list-employee'),
            path('information/listC/', views.listEmployeeCardView , name='list-employee-card'),
            path('information/list-terminated/', views.list_terminated_employees , name='list-terminated-employees'),
            path('correct/<int:pk>/', views.correctEmployeeView, name='correct-employee'),
             path('update/<int:pk>/', views.updateEmployeeView, name='update-employee'),
            path('view/<int:pk>/', views.viewEmployeeView, name='view-employee'),
            path('delete/<int:pk>/', views.deleteEmployeeView, name='delete-employee'),
            path('delete/forever/<int:pk>/', views.deleteEmployeePermanently, name='delete-employee-permanently'),
            path('terminat/<int:job_roll_id>/',views.terminat_employee , name='terminat-employee'),


            path('link/employee/<int:pk>/structure/', views.create_link_employee_structure, name='link-structure-create'),
            path('update/link/employee/<int:pk>/structure/', views.update_link_employee_structure, name='link-structure-update'),
            path('ajax/', views.change_element_value, name='change-element-value'),
            path('ajax/delete_element/', views.deleteElementView, name='delete-element'),
            path('employee/export/', views.export_employee_data, name='employee-export'),
            path('termination/employee/export/', views.export_termination_employee_data, name='export-termination-employee'),

            path('jobroll/new/<int:job_id>', views.createJobROll, name='new-jobroll'),
            path('leaves-history/' , views.list_employee_leave_requests , name='leaves-history'),
            path('element/new/<int:job_id>', views.create_employee_element, name='new-employee-element'),
            path('calc/formulas/<int:where_flag>/<int:job_id>',views.calc_formula , name='calc-formulas'),
            # path('insert/employee/elements',views.insert_employee_elements , name='insert-employee-elements'),
            path('upload/employee/elements',views.upload_employee_elements_excel , name='upload-employee-elements'),
            path('upload/employee/elements/confirm',views.confirm_xls_upload , name='confirm-employee-elements'),


            path('upload/employee/variable/elements',views.upload_employee_variable_element_industerial_excel , name='upload-employee-variable-elements'),
            path('upload/employee/elements/variable/confirm',views.confirm_xls_employee_variable_elements_upload , name='confirm-employee-variable-elements'),

            path('terminated/print',views.print_terminated_employees , name='print-terminated-employees'),
            path('rehire/employee/<int:emp_id>',views.rehire_employee, name='rehire-employee'),


    ])),

]
