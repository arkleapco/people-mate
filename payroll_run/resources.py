from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import EmployeesPayrollInformation
from import_export.fields import Field




class EmployeesPayrollInformationResource(resources.ModelResource):
    emp_number = Field(attribute='emp_number', column_name='Employee Number')
    emp_name = Field(attribute='emp_name', column_name='Employee Name')
    element_value = Field(attribute='element_value', column_name='Basic Salary')
    allowances = Field(attribute='allowances', column_name='Allowances')
    gross_salary = Field(attribute='gross_salary', column_name='Gross Salary')
    tax_amount = Field(attribute='tax_amount', column_name='Income Tax')
    insurance_amount = Field(attribute='insurance_amount', column_name='Social Insurance')
    deductions = Field(attribute='deductions', column_name='Deductions')
    net_salary = Field(attribute='net_salary', column_name='Net Salary')
    class Meta:
        model = EmployeesPayrollInformation
        exclude = ('id','history_month','history_year','information_month','information_year','incomes')



