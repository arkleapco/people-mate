from rest_framework import  serializers
from .models import *
from datetime import date
import getpass
from django.db import IntegrityError
from .models import TraceLog
from company.models import Enterprise




class TraceLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = TraceLog
        fields = '__all__'

    def create(self, validated_data):
          user = self.context.get('user')
          entity = Enterprise.objects.get(id = user.compamy).name
          trace_log_obj = TraceLog(**validated_data)
          trace_log_obj.entity = entity
          trace_log_obj.user = user
          trace_log_obj.date_time = date.today()
          trace_log_obj.os_user = getpass.getuser()
          try:
               trace_log_obj.save()
               return trace_log_obj
          except IntegrityError:
               self.create(self, validated_data)   
          


    def update(self ,instance, validated_data,*args ,**kwargs):
          user = self.context.get('user')
          entity = Enterprise.objects.get(id = user.company).name
          instance.trace_msg = validated_data.get('trace_msg',instance.trace_msg)
          instance.url = validated_data.get('url',instance.url)
          instance.data = validated_data.get('data',instance.data)

          instance.entity = entity
          instance.user = user
          instance.date_time = date.today()
          instance.os_user = getpass.getuser()
          try:
               instance.save()
               return instance
          except IntegrityError:
               self.create(self, validated_data)

        
       
