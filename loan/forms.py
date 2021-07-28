from datetime import date
from django import forms
from employee.models import Employee
from.models import *
from custom_user.models import User


class Loan_Type_Form(forms.ModelForm):
     class Meta():
          model = LoanType
          exclude = ['created_by', 'creation_date','last_update_by', 'last_update_date','start_date','end_date','company']


class Loan_Form(forms.ModelForm):
     def __init__(self, *args, **kwargs):
          super(Loan_Form, self).__init__(*args, **kwargs)
          for field in self.fields:
               self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'


     class Meta():
          model = Loan
          exclude = ['employee','status','created_by', 'creation_date','last_update_by', 'last_update_date',]
          widgets = {
            'loan_required_date': forms.DateInput(attrs={'class': 'form-control',
                                                'data-provide': "datepicker",
                                                 'wtx-context': "2A377B0C-58AD-4885-B9FB-B5AC9788D0F2"})}
