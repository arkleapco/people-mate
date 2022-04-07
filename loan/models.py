from employee.models import Employee
from django.db import models
from django.conf import settings
from company.models import Enterprise
from datetime import date, datetime ,timedelta
from django.utils.translation import ugettext_lazy as _
from django.contrib.contenttypes.fields import GenericRelation
from django.db.models.signals import pre_save, post_save, post_init
from django.dispatch import receiver
from dateutil.relativedelta import relativedelta

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
     number_of_installment_months = models.PositiveIntegerField()
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
     installment_amount = models.DecimalField(decimal_places=2,max_digits=20)
     start_date = models.DateField()
     end_date = models.DateField(null=True,blank=True)
     created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='loan_installment_created_by')
     creation_date = models.DateField(auto_now=True)
     last_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                        blank=True, null=True, related_name='loan_installment_last_updated_by')
     last_update_date = models.DateField(auto_now=True)

     def __str__(self):
         return self.loan.employee.emp_name + " " + str(self.installment_amount)
     

def create_new_isntallment(loan , installment_amount , start_date):
     loan_installment= LoanInstallment.objects.create(
                         loan = loan,
                         installment_amount = installment_amount,
                         start_date = start_date
                    )
     return loan_installment


@receiver(post_save, sender=Loan)
def create_loan_installments(sender , instance, *args , **kwargs):
     if instance.status == "Approved":
          installment_amount = round(instance.amount / instance.number_of_installment_months,2)  
                  
          if instance.mode_of_payment == "monthly":
               payment_month_number = 1

          elif instance.mode_of_payment == "quarterly":
               payment_month_number = 3
              
          
          elif instance.mode_of_payment == "semi-annual":
               payment_month_number = 6
               
          number_of_isntallments = int(instance.number_of_installment_months / payment_month_number)
          first_installment_pay_date = datetime.now()+relativedelta(months=+1)
          installment_amount = installment_amount*payment_month_number
          pay_date = first_installment_pay_date
          for installment in range(number_of_isntallments):
               loan_installment = create_new_isntallment(instance , installment_amount ,pay_date)
               pay_date = pay_date + relativedelta(months=+payment_month_number)
          if instance.number_of_installment_months % payment_month_number != 0:
               rest_of_installments = instance.amount - (number_of_isntallments * installment_amount)
               create_new_isntallment(instance , rest_of_installments ,pay_date)