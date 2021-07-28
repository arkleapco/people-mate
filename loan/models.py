from employee.models import Employee
from django.db import models
from django.conf import settings
from company.models import Enterprise
from datetime import date
from django.utils.translation import ugettext_lazy as _



class LoanType(models.Model):
     name = models.CharField(max_length=200)
     company = models.ForeignKey(Enterprise,on_delete=models.CASCADE)
     start_date = models.DateField(auto_now=False, auto_now_add=False, default=date.today, verbose_name=_('Start Date'))
     end_date = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name=_('End Date'))
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_type_created_by')
     creation_date = models.DateField(auto_now_add=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_type_last_updated_by')
     last_update_date = models.DateField(auto_now=True)

     class Meta:
          unique_together = ('company','name')


    
     

class Loan(models.Model):
     MODE_OF_PAYMENT_LIST=[
          ("monthly" , "Monthly"),
          ("quarterly","Quarterly"),
          ("semi-annual","Semi-annual")
     ]
     employee = models.ForeignKey(Employee,on_delete=models.CASCADE)
     loan_type = models.ForeignKey(LoanType , on_delete=models.CASCADE)
     amount = models.DecimalField(decimal_places=2,max_digits=20)
     number_of_installments = models.IntegerField()
     mode_of_payment = models.CharField(choices=MODE_OF_PAYMENT_LIST,default="monthly" , max_length=30)
     loan_required_date = models.DateField()
