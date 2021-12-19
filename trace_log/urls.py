from django.urls import path
from trace_log import views


app_name= 'trace_log'

urlpatterns =[
          path('list', views.list_trace_log, name='list-trace-log'),
          path('create', views.create_trace_log, name='create-trace-log'),
          path('search', views.search_trace_log, name='search-trace-log'),
          path('api/create', views.create_trace_log_api, name='create-trace-log-api'),
          path('api/search', views.search_trace_log_api, name='search-trace-log-api'),
     
]