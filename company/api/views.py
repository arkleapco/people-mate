from rest_framework.decorators import api_view 
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from company.api.serializer import *
import requests



@api_view(['GET',])
def test(request):
     url = 'https://en.wikipedia.org/wiki/Django_(web_framework)'
     response = requests.get(url).json()
     return Response(response)
          




