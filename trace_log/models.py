from django.db import models
from django.conf import settings
from datetime import datetime 
import getpass



# Create your models here.

class TraceLog(models.Model):
     entity = models.CharField(max_length=150, blank=True, null=True)
     trace_msg = models.CharField(max_length=500, blank=True, null=True)
     data = models.TextField(blank=True, null=True)
     url = models.CharField(max_length=500, blank=True, null=True)
     date_time=models.DateTimeField(default=datetime.now())
     user = models.ForeignKey(settings.AUTH_USER_MODEL , on_delete=models.PROTECT )
     os_user = models.CharField(max_length=150, default=getpass.getuser())

     def __str__(self):
          return self.trace_msg 
