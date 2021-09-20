from import_export import resources, fields
from import_export.widgets import ForeignKeyWidget
from .models import EmployeesPayrollInformation




class EmployeesPayrollInformationResource(resources.ModelResource):
    class Meta:
        model = EmployeesPayrollInformation
        exclude = ('id','history_month','history_year','information_month','information_year')

