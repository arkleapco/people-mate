from django.conf import settings
from django.db import models
from datetime import date
from django.db.models import Q
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from employee.models import Employee, JobRoll, Employee_Element, Employee_Element_History
from element_definition.models import Element_Batch
from manage_payroll.models import Assignment_Batch, Payroll_Master
from payroll_run.new_tax_rules import Tax_Deduction_Amount
from django.utils.translation import ugettext_lazy as _
from element_definition.models import Element

month_name_choises = [
    (1, _('January')), (2, _('February')), (3, _('March')), (4, _('April')),
    (5, _('May')), (6, _('June')), (7, _('July')), (8, _('August')),
    (9, _('September')), (10, _('October')
                          ), (11, _('November')), (12, _('December')),
]

elements_to_run_choices = [('appear', 'Payslip elements'), ('no_appear', 'Not payslip elements')]


class Salary_elements(models.Model):

    emp = models.ForeignKey(Employee, on_delete=models.CASCADE,
                            null=True, blank=True, verbose_name=_('Employee'))

    salary_month = models.IntegerField(choices=month_name_choises, validators=[
        MaxValueValidator(12), MinValueValidator(1)], verbose_name=_('Salary Month'))
    salary_year = models.IntegerField(verbose_name=_('Salary Year'))
    run_date = models.DateField(auto_now=False, auto_now_add=False,
                                default=date.today, blank=True, null=True, verbose_name=_('Run Date'))
    elements_type_to_run = models.CharField(max_length=50, verbose_name=_('Run on'), choices=elements_to_run_choices,
                                            default='appear',blank=True, null=True,)
    element = models.ForeignKey(
        Element, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Element')) # Not used now
    assignment_batch = models.ForeignKey(
        Assignment_Batch, on_delete=models.CASCADE, null=True, blank=True, verbose_name=_('Assignment Batch'))
    ################################### Incomes/ allowances ####################
    incomes = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Income'))
    ################################### Deductions #############################
    insurance_amount = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Insurance Amount'))  # Deductions
    company_insurance_amount = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Insurance Amount'))  # Deductions
    retirement_insurance_amount = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Insurance Amount'))  # Deductions
    tax_amount = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Tax Amount'))  # Deductions
    ############################################################################
    deductions = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Deduction'))
    penalties = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Penalties'))
    delays = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Delays'))
    ############################################################################
    gross_salary = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Gross Salary'))
    net_salary = models.FloatField(
        default=0.0, null=True, blank=True, verbose_name=_('Net Salary'))
    final_net_salary = models.FloatField(
        default=0.0, verbose_name=_('Final Net Salary'))
    attribute1 = models.FloatField(
        default=0.0, verbose_name=_('Attribute 1') , help_text="result of net salary * 1%"
    )
    is_final = models.BooleanField(
        default=False, blank=True, verbose_name=_('Salary is final'))
    start_date = models.DateField(
        auto_now=False, auto_now_add=False, default=date.today, verbose_name=_('Start Date'))
    end_date = models.DateField(
        auto_now=False, auto_now_add=False, blank=True, null=True, verbose_name=_('End Date'))
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, blank=False,
                                   on_delete=models.CASCADE, related_name="salary_created_by")
    creation_date = models.DateField(auto_now=True, auto_now_add=False)
    last_update_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.CASCADE, related_name="salary_last_update_by")
    last_update_date = models.DateField(auto_now=False, auto_now_add=True)

    def __str__(self):
        return self.emp.emp_name

    class Meta:
        unique_together = ('emp', 'salary_month', 'salary_year',)
    
    @property
    def num_days(self):
        if self.emp.employee_working_days_from_hiredate(self.salary_year, self.salary_month):
            return self.emp.employee_working_days_from_hiredate(self.salary_year, self.salary_month)
        elif self.emp.employee_working_days_from_terminationdate(self.salary_year,self.salary_month ):
            return self.emp.employee_working_days_from_terminationdate(self.salary_year,self.salary_month )
        else:
            return 30



class Taxes(models.Model):
    percent = models.FloatField(default=0.0, null=False, blank=False, verbose_name=_('percent'))
    start_range = models.IntegerField(default=0.0, null=False, blank=False, verbose_name=_('start'))
    end_range = models.IntegerField(default=0.0, null=False, blank=False, verbose_name=_('end'))
    diffrence = models.IntegerField(default=0.0, null=True, blank=True, verbose_name=_('diffrence'))
    tax = models.IntegerField(default=0.0, null=True, blank=True, verbose_name=_('tax'))








class EmployeesPayrollInformation(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_number= models.CharField(max_length=200)
    emp_name = models.CharField(max_length=200)
    element_value= models.DecimalField(decimal_places=2,max_digits=20)
    allowances= models.DecimalField(decimal_places=2,max_digits=20)
    insurance_amount= models.DecimalField(decimal_places=2,max_digits=20)
    gross_salary= models.DecimalField(decimal_places=2,max_digits=20)
    tax_amount= models.DecimalField(decimal_places=2,max_digits=20)
    deductions= models.DecimalField(decimal_places=2,max_digits=20)
    net_salary= models.DecimalField(decimal_places=2,max_digits=20)
    incomes = models.DecimalField(decimal_places=2,max_digits=20)
    history_month = models.IntegerField()
    history_year = models.IntegerField()
    information_month = models.IntegerField()
    information_year= models.IntegerField()
    company = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'employees_payroll_information'   




class EmployeeElementBeforeRun(models.Model):
    emp_name = models.CharField(max_length=200)
    element_name = models.CharField(max_length=200)
    element_value = models.DecimalField(decimal_places=2,max_digits=20)
    company = models.IntegerField()
    class Meta:
        managed = False
        db_table = 'employee_element_before_run'  



class EmployeePayrollElements2(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_number= models.CharField(max_length=200)
    emp_name = models.CharField(max_length=200)
    payroll_month = models.IntegerField()
    payroll_year= models.IntegerField()
    enterprise_id = models.IntegerField() 
    attribute_1	 =	 models.CharField(max_length=200) 
    attribute_2	 =	 models.CharField(max_length=200)
    attribute_3	 =	 models.CharField(max_length=200)
    attribute_4	 =	 models.CharField(max_length=200)
    attribute_5	 =	 models.CharField(max_length=200)
    attribute_6	 =	 models.CharField(max_length=200)
    attribute_7	 =	 models.CharField(max_length=200)
    attribute_8	 =	 models.CharField(max_length=200)
    attribute_9	 =	 models.CharField(max_length=200)
    attribute_10	 =	 models.CharField(max_length=200)
    attribute_11	 =	 models.CharField(max_length=200)
    attribute_12	 =	 models.CharField(max_length=200)
    attribute_13	 =	 models.CharField(max_length=200)
    attribute_14	 =	 models.CharField(max_length=200)
    attribute_15	 =	 models.CharField(max_length=200)
    attribute_16	 =	 models.CharField(max_length=200)
    attribute_17	 =	 models.CharField(max_length=200)
    attribute_18	 =	 models.CharField(max_length=200)
    attribute_19	 =	 models.CharField(max_length=200)
    attribute_20	 =	 models.CharField(max_length=200)
    attribute_21	 =	 models.CharField(max_length=200)
    attribute_22	 =	 models.CharField(max_length=200)
    attribute_23	 =	 models.CharField(max_length=200)
    attribute_24	 =	 models.CharField(max_length=200)
    attribute_25	 =	 models.CharField(max_length=200)
    attribute_26	 =	 models.CharField(max_length=200)
    attribute_27	 =	 models.CharField(max_length=200)
    attribute_28	 =	 models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'employee_payroll_elements_2'



class EmployeePayrollElements3(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_number= models.CharField(max_length=200)
    emp_name = models.CharField(max_length=200)
    payroll_month = models.IntegerField()
    payroll_year= models.IntegerField()
    enterprise_id = models.IntegerField() 
    attribute_1	 =	 models.CharField(max_length=200)
    attribute_2	 =	 models.CharField(max_length=200)
    attribute_3	 =	 models.CharField(max_length=200)
    attribute_4	 =	 models.CharField(max_length=200)
    attribute_5	 =	 models.CharField(max_length=200)
    attribute_6	 =	 models.CharField(max_length=200)
    attribute_7	 =	 models.CharField(max_length=200)
    attribute_8	 =	 models.CharField(max_length=200)
    attribute_9	 =	 models.CharField(max_length=200)
    attribute_10	 =	 models.CharField(max_length=200)
    attribute_11	 =	 models.CharField(max_length=200)
    attribute_12	 =	 models.CharField(max_length=200)
    attribute_13	 =	 models.CharField(max_length=200)
    attribute_14	 =	 models.CharField(max_length=200)
    attribute_15	 =	 models.CharField(max_length=200)
    attribute_16	 =	 models.CharField(max_length=200)
    attribute_17	 =	 models.CharField(max_length=200)
    attribute_18	 =	 models.CharField(max_length=200)
    attribute_19	 =	 models.CharField(max_length=200)
    attribute_20	 =	 models.CharField(max_length=200)
    attribute_21	 =	 models.CharField(max_length=200)
    attribute_22	 =	 models.CharField(max_length=200)
    attribute_23	 =	 models.CharField(max_length=200)
    attribute_24	 =	 models.CharField(max_length=200)
    attribute_25	 =	 models.CharField(max_length=200)
    attribute_26	 =	 models.CharField(max_length=200)
    attribute_27	 =	 models.CharField(max_length=200)
    attribute_28	 =	 models.CharField(max_length=200)
    attribute_29	 =	 models.CharField(max_length=200)
    attribute_30	 =	 models.CharField(max_length=200)
    attribute_31	 =	 models.CharField(max_length=200)
    attribute_32	 =	 models.CharField(max_length=200)
    attribute_33	 =	 models.CharField(max_length=200)
    attribute_34	 =	 models.CharField(max_length=200)
    attribute_35	 =	 models.CharField(max_length=200)
    attribute_36	 =	 models.CharField(max_length=200)
    attribute_37	 =	 models.CharField(max_length=200)
    attribute_38	 =	 models.CharField(max_length=200)
    attribute_39	 =	 models.CharField(max_length=200)
    attribute_40	 =	 models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'employee_payroll_elements_3'  


class EmployeePayrollElements4(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_number= models.CharField(max_length=200)
    emp_name = models.CharField(max_length=200)
    payroll_month = models.IntegerField()
    payroll_year= models.IntegerField()
    enterprise_id = models.IntegerField() 
    attribute_1	 =	 models.CharField(max_length=200)
    attribute_2	 =	 models.CharField(max_length=200)
    attribute_3	 =	 models.CharField(max_length=200)
    attribute_4	 =	 models.CharField(max_length=200)
    attribute_5	 =	 models.CharField(max_length=200)
    attribute_6	 =	 models.CharField(max_length=200)
    attribute_7	 =	 models.CharField(max_length=200)
    attribute_8	 =	 models.CharField(max_length=200)
    attribute_9	 =	 models.CharField(max_length=200)
    attribute_10	 =	 models.CharField(max_length=200)
    attribute_11	 =	 models.CharField(max_length=200)
    attribute_12	 =	 models.CharField(max_length=200)
    attribute_13	 =	 models.CharField(max_length=200)
    attribute_14	 =	 models.CharField(max_length=200)
    attribute_15	 =	 models.CharField(max_length=200)
    attribute_16	 =	 models.CharField(max_length=200)
    attribute_17	 =	 models.CharField(max_length=200)
    attribute_18	 =	 models.CharField(max_length=200)
    attribute_19	 =	 models.CharField(max_length=200)
    attribute_20	 =	 models.CharField(max_length=200)
    attribute_21	 =	 models.CharField(max_length=200)
    attribute_22	 =	 models.CharField(max_length=200)
    attribute_23	 =	 models.CharField(max_length=200)
    attribute_24	 =	 models.CharField(max_length=200)
    attribute_25	 =	 models.CharField(max_length=200)
    attribute_26	 =	 models.CharField(max_length=200)
    attribute_27	 =	 models.CharField(max_length=200)

    class Meta:
        managed = False
        db_table = 'employee_payroll_elements_4'


@receiver(pre_save, sender=Salary_elements)
def employee_elements_history(sender, instance, *args, **kwargs):
    employee_old_elements = Employee_Element.objects.filter(emp_id=instance.emp).exclude(element_id__classification__code='info')
    check_for_same_element = Employee_Element_History.objects.filter(emp_id=instance.emp_id,
                                                                     salary_month=instance.salary_month,
                                         
                                                                     salary_year=instance.salary_year)
    if check_for_same_element:
        for record in check_for_same_element:
            record.delete()
    # for only earning elements not deductions
    for element in employee_old_elements:
        if element.element_id.classification.code == 'earn':
            if element.element_id.is_fixed == True :
                working_days_newhire=element.emp_id.employee_working_days_from_hiredate(instance.salary_year, instance.salary_month)
                working_days_retirement=element.emp_id.employee_working_days_from_terminationdate(instance.salary_year,instance.salary_month )
                
                element_value_v = 0
                if working_days_newhire  and element.emp_id.hiredate.month == instance.salary_month and element.emp_id.hiredate.year == instance.salary_year:
                    element_value_v = element.element_value * working_days_newhire / 30
                elif working_days_retirement:
                    if element.emp_id.terminationdate is not None:
                        if element.emp_id.terminationdate.month == instance.salary_month and element.emp_id.terminationdate.year == instance.salary_year:
                            element_value_v = element.element_value * working_days_retirement / 30
        else:
            element_value_v = element.element_value
        
        element_history = Employee_Element_History(
            emp_id=element.emp_id,
            element_id=element.element_id,
            element_value=round(element_value_v,2),
            salary_month=instance.salary_month,
            salary_year=instance.salary_year,
            creation_date=date.today(),
        )
        element_history.save()







class EmployeeCompanyInsuranceShare(models.Model):
    id = models.IntegerField(primary_key=True)
    emp_number= models.CharField(max_length=200)
    emp_name = models.CharField(max_length=200)
    insurance_amount= models.DecimalField(decimal_places=2,max_digits=20)
    company_insurance_amount= models.DecimalField(decimal_places=2,max_digits=20)
    company_id = models.IntegerField()
    salary_month = models.IntegerField()
    salary_year = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'employee_company_insurance_share'   


