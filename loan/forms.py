from datetime import date
from django import forms
from employee.models import Employee
from.models import *
from custom_user.models import User


class Loan_Type_Form(forms.ModelForm):
    class Meta():
          model = LoanType
          exclude = ['created_by', 'creation_date','last_update_by', 'last_update_date','start_date','end_date','company']
    def __init__(self, *args, **kwargs):
        super(Loan_Type_Form, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'



class Loan_Form(forms.ModelForm):
    class Meta():
        model = Loan
        fields ="__all__"
