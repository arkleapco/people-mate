from employee.models import Employee
from django.db import models
from django.conf import settings


class LoanType(models.Model):
     name = models.CharField(max_length=200)
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_type_created_by')
     creation_date = models.DateField(auto_now_add=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_type_last_updated_by')
     last_update_date = models.DateField(auto_now=True)

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
