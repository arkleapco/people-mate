from django.urls import path
from workflow import views

# TEMPLATE TAGGING
app_name = 'workflow'
urlpatterns = [
    path('list/', views.list_service, name='list_workflow'),
    path('view/<int:service_id>', views.view_structure, name='view_structure'),
    path('create/', views.create_service_and_work_flow, name='create_structure'),
    path('update/<int:service_id>', views.update_service_workflow, name='update_structure'),
    path('delete/<int:service_id>', views.delete_service_workflow, name='delete_structure'),
    path('render-action/<int:id>/<slug:type>', views.render_action, name='render-action'),
    path('take-action-travel/<int:id>/<slug:type>', views.take_action_travel, name='take-action-travel'),
    path('take-action-leave/<int:id>/<slug:type>', views.take_action_leave, name='take-action-leave'),
    path('take-action-purchase/<int:id>/<slug:type>', views.take_action_purchase, name='take-action-purcahse'),

    path('ajax/load-employees', views.load_employees, name='load_employees'),
]
