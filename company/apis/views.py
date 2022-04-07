from datetime import date
from xml.parsers import expat
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
#from rest_framework.permissions import IsAuthenticated
from .Serializers import Enterprise, Enterpriseserializers


# list data => GET
@api_view(['GET'])
def list_enterprise(request):
    try:
        enterprise = Enterprise.objects.all()
        serializer = Enterpriseserializers(enterprise, many=True)
        return Response(serializer.data)
    except:
        return Response("somthing wrong")


# Create data => POST

@api_view(['POST'])
def create_enterprise(request):
    serializer = Enterpriseserializers(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# delete data => delete

@api_view(['GET'])
def delete_enterprise(request, pk):
    try:
        enterprise = Enterprise.objects.get(pk=pk)
        enterprise.end_date = date.today()
        enterprise.save()
        serializer = Enterpriseserializers(enterprise)
        return Response("You delete that enterprise", status=status.HTTP_204_NO_CONTENT)
    except Enterprise.DoesNotExist:
        return Response(status=status.HTTP_404_NOT_FOUND)
