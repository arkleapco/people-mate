from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import EmployeesPayrollInformation, EmployeePayrollElements2, EmployeePayrollElements3, EmployeePayrollElements4
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
    history_month = Field(attribute='history_month', column_name='Month 1')
    information_month = Field(attribute='information_month', column_name='Month 2')

    class Meta:
        model = EmployeesPayrollInformation
        exclude = ('id','history_year','information_year','incomes')



class EmployeePayrollElements2Resource(resources.ModelResource):
    emp_number	=	Field(attribute=	'emp_number'	, column_name=	'Employee Number')
    emp_name	=	Field(attribute=	'emp_name'	, column_name=	'Employee Name')
    agazat_days	=	Field(attribute=	'attribute_1'	, column_name=	'عدد ايام الاجازات')
    penalities	=	Field(attribute=	'attribute_2'	, column_name=	'Penalities')
    benefit_now_pay	=	Field(attribute=	'attribute_3'	, column_name=	'Benefit Now Pay')
    loan	=	Field(attribute=	'attribute_4'	, column_name=	'Loan')
    basic_salary	=	Field(attribute=	'attribute_5'	, column_name=	'Basic Salary')
    incentives	=	Field(attribute=	'attribute_6'	, column_name=	'incentives')
    other_allowances	=	Field(attribute=	'attribute_7'	, column_name=	'Other Allowances')
    housing_allowance	=	Field(attribute=	'attribute_8'	, column_name=	'Housing Allowance')

    class Meta:
        model = EmployeePayrollElements2
        exclude = ()


class EmployeePayrollElements3Resource(resources.ModelResource):
    class Meta:
        model = EmployeePayrollElements3
        exclude = ()


class EmployeePayrollElements4Resource(resources.ModelResource):
    class Meta:
        model = EmployeePayrollElements4
        exclude = ()