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
    payroll_month = Field(attribute='payroll_month', column_name='Payroll Month ')
    payroll_year= Field(attribute='payroll_year', column_name='Payroll Year ')
    attribute_1	=	Field(attribute=	'attribute_1'	, column_name=	'عدد ايام الاجازات')
    attribute_2	=	Field(attribute=	'attribute_2'	, column_name=	'Penalities')
    attribute_3	=	Field(attribute=	'attribute_3'	, column_name=	'Benefit Now Pay')
    attribute_4	=	Field(attribute=	'attribute_4'	, column_name=	'Loan')
    attribute_5	=	Field(attribute=	'attribute_5'	, column_name=	'Basic Salary')
    attribute_6	=	Field(attribute=	'attribute_6'	, column_name=	'incentives')
    attribute_7	=	Field(attribute=	'attribute_7'	, column_name=	'Other Allowances')
    attribute_8	=	Field(attribute=	'attribute_8'	, column_name=	'Housing Allowance')


    class Meta:
        model = EmployeePayrollElements2
        exclude = ()


class EmployeePayrollElements3Resource(resources.ModelResource):
    emp_number	=	Field(attribute=	'emp_number'	, column_name=	'Employee Number')
    emp_name	=	Field(attribute=	'emp_name'	, column_name=	'Employee Name')
    payroll_month = Field(attribute='payroll_month', column_name='Payroll Month ')
    payroll_year= Field(attribute='payroll_year', column_name='Payroll Year ')
    attribute_1	=	Field(attribute=	'	attribute_1	'	, column_name=	'	Basic salary	')
    attribute_2	=	Field(attribute=	'	attribute_2	'	, column_name=	'	Basic salary increase	')
    attribute_3	=	Field(attribute=	'	attribute_3	'	, column_name=	'	Total Baisc Salary	')
    attribute_4	=	Field(attribute=	'	attribute_4	'	, column_name=	'	سعر الساعة	')
    attribute_5	=	Field(attribute=	'	attribute_5	'	, column_name=	'	سعر اليوم	')
    attribute_6	=	Field(attribute=	'	attribute_6	'	, column_name=	'	عدد ساعات السهرالنهاري	')
    attribute_7	=	Field(attribute=	'	attribute_7	'	, column_name=	'	عدد ساعات السهرالليلي	')
    attribute_8	=	Field(attribute=	'	attribute_8	'	, column_name=	'	عدد ساعات السهرالعطلات	')
    attribute_9	=	Field(attribute=	'	attribute_9	'	, column_name=	'	ساعة سهر ليلي	')
    attribute_10	=	Field(attribute=	'	attribute_10	'	, column_name=	'	ساعة سهر نهاري	')
    attribute_11	=	Field(attribute=	'	attribute_11	'	, column_name=	'	ساعة سهر عطلات	')
    attribute_12	=	Field(attribute=	'	attribute_12	'	, column_name=	'	قيمة بدل السهر الليلي	')
    attribute_13	=	Field(attribute=	'	attribute_13	'	, column_name=	'	قيمة بدل السهر النهاري	')
    attribute_14	=	Field(attribute=	'	attribute_14	'	, column_name=	'	قيمة بدل السهر اجازات	')
    attribute_15	=	Field(attribute=	'	attribute_15	'	, column_name=	'	الراتب الكلي	')
    attribute_16	=	Field(attribute=	'	attribute_16	'	, column_name=	'	الراتب الصافي	')
    attribute_17	=	Field(attribute=	'	attribute_17	'	, column_name=	'	عدد أيام الجزاءات	')
    attribute_18	=	Field(attribute=	'	attribute_18	'	, column_name=	'	عدد أيام الاجازات	')
    attribute_19	=	Field(attribute=	'	attribute_19	'	, column_name=	'	عدد أيام الاجازات بدون إذن	')
    attribute_20	=	Field(attribute=	'	attribute_20	'	, column_name=	'	جزاءات	')
    attribute_21	=	Field(attribute=	'	attribute_21	'	, column_name=	'	خصومات أخري	')
    attribute_22	=	Field(attribute=	'	attribute_22	'	, column_name=	'	Benefit Now Pay	')
    attribute_23	=	Field(attribute=	'	attribute_23	'	, column_name=	'	عدد ايام الاجازات المرضي	')
    attribute_24	=	Field(attribute=	'	attribute_24	'	, column_name=	'	incentives	')
    attribute_25	=	Field(attribute=	'	attribute_25	'	, column_name=	'	Bonus	')
    attribute_26	=	Field(attribute=	'	attribute_26	'	, column_name=	'	Mobile Allowance	')
    attribute_27	=	Field(attribute=	'	attribute_27	'	, column_name=	'	performance Incentive	')
    attribute_28	=	Field(attribute=	'	attribute_28	'	, column_name=	'	Transportation Allowance	')
    attribute_29	=	Field(attribute=	'	attribute_29	'	, column_name=	'	Other Allowances	')
    attribute_30	=	Field(attribute=	'	attribute_30	'	, column_name=	'	Housing Allowance	')
    attribute_31	=	Field(attribute=	'	attribute_31	'	, column_name=	'	MealRate	')
    attribute_32	=	Field(attribute=	'	attribute_32	'	, column_name=	'	MealNumber	')
    attribute_33	=	Field(attribute=	'	attribute_33	'	, column_name=	'	meal Allowance	')
    attribute_34	=	Field(attribute=	'	attribute_34	'	, column_name=	'	TotalFixedelements	')
    attribute_35	=	Field(attribute=	'	attribute_35	'	, column_name=	'	Vacations balance allowance	')
    attribute_36	=	Field(attribute=	'	attribute_36	'	, column_name=	'	وقت اضافى ثابت	')
    attribute_37	=	Field(attribute=	'	attribute_37	'	, column_name=	'	وقت اضافى	')
    attribute_38	=	Field(attribute=	'	attribute_38	'	, column_name=	'	Absent	')
    attribute_39	=	Field(attribute=	'	attribute_39	'	, column_name=	'	Sick Leave	')
    attribute_40	=	Field(attribute=	'	attribute_40	'	, column_name=	'	جزاءات غياب بدون إذن	')
    attribute_41	=	Field(attribute=	'	attribute_41	'	, column_name=	'	سلف	')

    class Meta:
        model = EmployeePayrollElements3
        exclude = ()


class EmployeePayrollElements4Resource(resources.ModelResource):
    emp_number	=	Field(attribute=	'emp_number'	, column_name=	'Employee Number')
    emp_name	=	Field(attribute=	'emp_name'	, column_name=	'Employee Name')
    payroll_month = Field(attribute='payroll_month', column_name='Payroll Month ')
    payroll_year= Field(attribute='payroll_year', column_name='Payroll Year ')
    attribute_1	=	Field(attribute=	'	attribute_1	'	, column_name=	'	Basic salary	')
    attribute_2	=	Field(attribute=	'	attribute_2	'	, column_name=	'	Basic salary increase	')
    attribute_3	=	Field(attribute=	'	attribute_3	'	, column_name=	'	Total Baisc Salary	')
    attribute_4	=	Field(attribute=	'	attribute_4	'	, column_name=	'	Bonus	')
    attribute_5	=	Field(attribute=	'	attribute_5	'	, column_name=	'	TravelAllowances	')
    attribute_6	=	Field(attribute=	'	attribute_6	'	, column_name=	'	Other Allowances	')
    attribute_7	=	Field(attribute=	'	attribute_7	'	, column_name=	'	سعر الساعة	')
    attribute_8	=	Field(attribute=	'	attribute_8	'	, column_name=	'	سعر اليوم	')
    attribute_9	=	Field(attribute=	'	attribute_9	'	, column_name=	'	MealRate	')
    attribute_10	=	Field(attribute=	'	attribute_10	'	, column_name=	'	MealNumber	')
    attribute_11	=	Field(attribute=	'	attribute_11	'	, column_name=	'	meal Allowance	')
    attribute_12	=	Field(attribute=	'	attribute_12	'	, column_name=	'	Loan	')
    attribute_13	=	Field(attribute=	'	attribute_13	'	, column_name=	'	Other Deductions	')
    attribute_14	=	Field(attribute=	'	attribute_14	'	, column_name=	'	Benefit Now Pay	')
    attribute_15	=	Field(attribute=	'	attribute_15	'	, column_name=	'	عدد أيام الجزاءات	')
    attribute_16	=	Field(attribute=	'	attribute_16	'	, column_name=	'	عدد أيام الاجازات	')
    attribute_17	=	Field(attribute=	'	attribute_17	'	, column_name=	'	Penalties	')
    attribute_18	=	Field(attribute=	'	attribute_18	'	, column_name=	'	TotalFixedelements	')
    attribute_19	=	Field(attribute=	'	attribute_19	'	, column_name=	'	Absent	')
    attribute_20	=	Field(attribute=	'	attribute_20	'	, column_name=	'	عدد أيام الاجازات بدون إذن	')
    attribute_21	=	Field(attribute=	'	attribute_21	'	, column_name=	'	Unpaid Days	')
    attribute_22	=	Field(attribute=	'	attribute_22	'	, column_name=	'	SickLeave Days	')
    attribute_23	=	Field(attribute=	'	attribute_23	'	, column_name=	'	Sick Leave	')

    class Meta:
        model = EmployeePayrollElements4
        exclude = ()