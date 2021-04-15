from django.urls import path, include
from django.contrib.auth.decorators import login_required
from performance import views

# gehad : createPerformance urls.
app_name= 'performance'

urlpatterns =[
    path('performance/', include([
            ######################### Performance URLs ###################################
            path('create/', views.createPerformance, name='performance-create'),
            path('edit/<int:pk>/', views.updatePerformance, name='performance-edit'),
            path('delete/<int:pk>/', views.deletePerformance, name='performance-delete'),
            path('list/', views.listPerformance, name='performance-list'),
            path('performance/<int:pk>/', views.performanceView, name='performance'),
            #performanceRating
            path('create/rating/<int:per_id>/', views.createPerformanceRating, name='rating-create'),
            path('update/rating/<int:pk>/', views.updatePerformanceRating, name='rating-update'),
            #management
            path('management/<int:pk>/', views.performanceManagement, name='management'),
            #segments
            path('segments/<int:pk>/<int:ret_id>/', views.listSegment, name='segments'),
            path('create/segment/<int:per_id>/<int:ret_id>/', views.createSegment, name='segment-create'),
            path('edit/segment/<int:pk>/<int:ret_id>/', views.updateSegment, name='segment-edit'),
            path('delete/segment/<int:pk>/<int:ret_id>/', views.deleteSegment, name='segment-delete'),
            #employeeRate
            path('employees/', views.list_employees_performances_for_manager, name='employees'),
            path('performances/', views.employeePerformances), #ajax
            path('employee/<int:pk>/<int:emp_id>/', views.employee_rates, name='employee-rate'),
            path('employee/overview/<int:per_id>/<int:emp_id>/create/', views.create_employee_overview_rate, name='create-employee-overview'),
            path('employee/overview/<int:per_id>/<int:emp_id>/update/', views.update_employee_overview_rate, name='update-employee-overview'),
            path('employee/segment/questions/<int:pk>/<int:emp_id>/', views.employee_segment_questions, name='employee-segment-questions'),
            path('employee/segment/question/<int:pk>/<int:emp_id>/create/', views.create_employee_question_rate, name='create-employee-question-rate'),
            path('employee/segment/question/<int:pk>/<int:emp_id>/update/', views.update_employee_question_rate, name='update-employee-question-rate'),
            path('emp/performances/<int:pk>/', views.employee_performances, name='employee-performances'),
              ])),
]
