from employee.models import Employee
from django.db import models
from django.conf import settings
from company.models import Enterprise
from datetime import date
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation


class LoanType(models.Model):
     name = models.CharField(max_length=200)
     company = models.ForeignKey(Enterprise,on_delete=models.CASCADE)
     start_date = models.DateField(auto_now=False, auto_now_add=False, default=date.today, verbose_name=_('Start Date'))
     end_date = models.DateField(auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name=_('End Date'))
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_type_created_by')
     creation_date = models.DateField(auto_now=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_type_last_updated_by')
     last_update_date = models.DateField(auto_now=True)

     class Meta:
          unique_together = ('company','name', 'end_date')


     def __str__(self):
         return self.name

class Loan(models.Model):
     MODE_OF_PAYMENT_LIST=[
          ("monthly" , "Monthly"),
          ("quarterly","Quarterly"),
          ("semi-annual","Semi-annual")
     ]
     employee = models.ForeignKey(Employee,on_delete=models.CASCADE)
     loan_type = models.ForeignKey(LoanType , on_delete=models.CASCADE , related_name="loan_type")
     amount = models.DecimalField(decimal_places=2,max_digits=20)
     number_of_installments = models.PositiveIntegerField()
     mode_of_payment = models.CharField(choices=MODE_OF_PAYMENT_LIST,default="monthly" , max_length=30)
     loan_required_date = models.DateField()
     status = models.CharField(max_length=20, default='pending')
     workflow = GenericRelation("workflow.ServiceRequestWorkflow" ,content_type_field='content_type',
        object_id_field='object_id', related_query_name='loan')
     version = models.IntegerField(default = 1 , help_text="version of loan request")
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_created_by')
     creation_date = models.DateField(auto_now=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_last_updated_by')
     last_update_date = models.DateField(auto_now=True)

     def __str__(self):
         return self.employee.emp_name +" "+ str(self.amount) + " EGP"


class LoanInstallment(models.Model):
     loan = models.ForeignKey(Loan,on_delete=models.CASCADE)
     installment_amount = models.DecimalField(decimal_places=5,max_digits=20)
     start_date = models.DateField()
     end_date = models.DateField(null=True,blank=True)
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_installment_created_by')
     creation_date = models.DateField(auto_now=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_installment_last_updated_by')
     last_update_date = models.DateField(auto_now=True)
     