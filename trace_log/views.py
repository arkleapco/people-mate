from django.db.models.query_utils import Q
from trace_log.models import TraceLog
import getpass
from rest_framework.permissions import IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from .serializers import TraceLogSerializer
from rest_framework.response import Response
from .models import TraceLog
from company.models import Enterprise




# Create your views here.

@api_view(['POST', ])
@permission_classes([IsAuthenticated])
def list_trace_log(request): 
     """
     Purpose: get all trace log  ,
     param : request
     by: gehad,
     date: 13/09/2021,
     """
     try :
          logs = TraceLog.objects.all()
          if logs:
               serializer = TraceLogSerializer(logs, many=True)
               data = {"response_id": '0' ,"data":serializer.data}
          else:
               data = {"response_id": '3',"data":[]}
     except Exception as e:  
          create_trace_log(Enterprise.objects.get(id = request.user.company).name,"exception in list trace log",e,'trace_log/list',request.user)     
          data = {"response_id": '-1', "error": e}  
     return Response(data)   
    






def create_trace_log(entity,trace_msg,data,url,user):
     trace_log_obj = TraceLog(
          entity = entity,
          trace_msg = trace_msg,
          data = data,
          url = url,
          user = user,
          os_user = getpass.getuser()
     )
     try:
          trace_log_obj.save()
          return True
     except Exception as e:
          create_trace_log(entity,trace_msg,data,url,user)
          return False



def search_trace_log(request):
     search_by = request.data['search_by']
     trace_logs = TraceLog.objects.filter(
          Q(entity__icontains = search_by) 
     | Q(trace_msg__icontains = search_by)
     | Q(data__icontains = search_by)
     | Q(user__username__icontains = search_by)
     )
     return trace_logs




@api_view(['POST',])
@permission_classes([IsAuthenticated])
def create_trace_log_api(request):
     """
     Purpose: create new trace log ,
     param : request,
     by: gehad,
     date: 31/08/2021,
     """
     if request.method == 'POST':
          trace_log_serializer = TraceLogSerializer(data=request.data , context={'user':request.user})
          if trace_log_serializer.is_valid():
               trace_log_serializer.save()
               data = {"response_id": '0',"data": trace_log_serializer.data}
               return Response(data)
          else:
               data = { "response_id": '1',"error":trace_log_serializer.errors}
               return Response(data)


@api_view(['POST',])
@permission_classes([IsAuthenticated])
def search_trace_log_api(request):
     """
     Purpose: search in trace log by entity, trace_msg, data, user
     param : request,
     by: gehad,
     date: 1/09/2021,
     """
     if request.method == 'POST':
          search_by = request.data['search_by']
          trace_logs = TraceLog.objects.filter(
          Q(entity__icontains = search_by) 
               | Q(trace_msg__icontains = search_by)
               | Q(data__icontains = search_by)
               | Q(user__username__icontains = search_by)
                                                  )
          trace_log_serializer = TraceLogSerializer(trace_logs , many=True)
          if trace_log_serializer:
               data = {"response_id": '0' ,"data": trace_log_serializer.data}
          else:
               data = {"response_id": '3' ,"data": []}
          return Response(data)

