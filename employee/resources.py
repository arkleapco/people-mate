from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import Employee , JobRoll , Employee_Element, UploadEmployeeElement , UploadEmployeeVariableElement_Industerial
from company.models import Position
from import_export.fields import Field
from company.models import Enterprise
from custom_user.models import User
from manage_payroll.models import (Bank_Master, Payroll_Master)
from defenition.models import LookupType, LookupDet




class EmployeeResource(resources.ModelResource): 
    class Meta:
        model = Employee

    user = fields.Field(
        column_name='user',
        attribute='user',
        widget=ForeignKeyWidget(User, 'pk'))

    enterprise = fields.Field(
        column_name='enterprise',
        attribute='enterprise',
        widget=ForeignKeyWidget(Enterprise, 'pk'))  

    
    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']

    





class JobRollResource(resources.ModelResource): 
    class Meta:
        model = JobRoll

    emp_id = fields.Field(
        column_name='emp_id',
        attribute='emp_id',
        widget=ForeignKeyWidget(Employee, 'pk'))

    manager = fields.Field(
        column_name='manager',
        attribute='manager',
        widget=ForeignKeyWidget(Employee, 'pk'))  

    position = fields.Field(
        column_name='position',
        attribute='position',
        widget=ForeignKeyWidget(Position, 'pk'))  
    


    contract_type = fields.Field(
        column_name='contract_type',
        attribute='contract_type',
        widget=ForeignKeyWidget(LookupDet, 'pk'))  
    

    payroll = fields.Field(
        column_name='payroll',
        attribute='payroll',
        widget=ForeignKeyWidget(Payroll_Master, 'pk'))  
    
    
    def after_import_instance(self, instance, new, **kwargs):
        if new or not instance.created_by:
            instance.created_by = kwargs['user']
        instance.last_update_by = kwargs['user']




# class Employee_ElementResource(resources.ModelResource):
    # emp_id = Field(attribute='emp_id',column_name='Code')
    # element_id = Field(attribute='element_id',column_name='Basic Salary')
    # element_value = Field(attribute='element_value',column_name='Bonus')
    # start_date = Field(attribute='start_date',column_name='increas')
    # end_date = Field(attribute='end_date',column_name='Housing Allowance')
    # created_by = Field(attribute='created_by',column_name='Other Allowances')
    # creation_date = Field(attribute='creation_date',column_name='Transportation Allowance')
    # last_update_by = Field(attribute='last_update_by',column_name='Insurance Salary')
    # last_update_date = Field(attribute='last_update_date',column_name='Insurance Salary Retirement')

    # class Meta:
    #     model = Employee_Element
    #     exclude = ('element_value','emp_id','id','element_id','start_date','end_date','created_by','creation_date','last_update_by','last_update_date')


        # def import_row(self, row, instance_loader, using_transactions=True, dry_run=False, raise_errors=False, **kwargs):
        #     print("**************************", row)

        # try:
        #     self.before_import_row(row, **kwargs)
        #     instance, new = self.get_or_init_instance(instance_loader, row)
        #     self.after_import_instance(instance, new, **kwargs)
        #     if new:
        #         return row_result
        #     else:
        #         row_result.import_type = RowResult.IMPORT_TYPE_UPDATE
        #     row_result.new_record = new
        #     original = deepcopy(instance)    

    # def before_import_row(self, row, row_number=None, **kwargs):
    #     print("**********************",row )
    #     print("**********************",row_number )
    #     print("**************************",row.get('increas'))



    # def before_save_instance(self, instance, using_transactions, dry_run):
    #     print("******************",instance )

class UploadEmployeeElementResource(resources.ModelResource):
    class Meta:
        model = UploadEmployeeElement
        exclude = ('enterprise',)
    



class UploadEmployeeVariableElement_IndusterialResource(resources.ModelResource):
    class Meta:
        model = UploadEmployeeVariableElement_Industerial
        exclude = ('enterprise')

        