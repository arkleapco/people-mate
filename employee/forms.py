from django import forms
from crispy_forms.helper import FormHelper
from django.db.models import Q
from company.models import Department, Job, Grade, Position
from manage_payroll.models import Payroll_Master, Payment_Method
from employee.models import Employee, JobRoll, Payment, Employee_Element, EmployeeStructureLink, Employee_File , Employee_Depandance , Employee_Element_History, XX_EMP_CONTRACT_LOV
from defenition.models import LookupType, LookupDet
from element_definition.models import SalaryStructure
from django.shortcuts import get_object_or_404, get_list_or_404
from datetime import date
from django.forms import BaseInlineFormSet
from element_definition.models import Element
import os


common_items_to_execlude = (
    'enterprise',
    'created_by', 'creation_date',
    'last_update_by', 'last_update_date',
    'attribute1', 'attribute2', 'attribute3',
    'attribute4', 'attribute5', 'attribute6',
    'attribute7', 'attribute8', 'attribute9',
    'attribute10', 'attribute11', 'attribute12',
    'attribute13', 'attribute14', 'attribute15',
)


###############################################################################

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = '__all__'
        widgets = {
            'insured': forms.CheckboxInput(attrs={
                'style': 'padding: 25px; margin:25px;'
            }),
            'has_medical': forms.CheckboxInput(attrs={
                'style': 'padding: 25px; margin:25px;'
            }),
            'is_active': forms.CheckboxInput(attrs={
                'style': 'padding: 25px; margin:25px;'
            }),
        }
        exclude = common_items_to_execlude

    def __init__(self, *args, **kwargs):
        super(EmployeeForm, self).__init__(*args, **kwargs)
        self.fields['date_of_birth'].widget.input_type = 'date'
        self.fields['hiredate'].widget.input_type = 'date'
        self.fields['terminationdate'].widget.input_type = 'date'
        self.fields['emp_start_date'].widget.input_type = 'date'
        self.fields['emp_end_date'].widget.input_type = 'date'
        self.fields['insurance_date'].widget.input_type = 'date'
        self.fields['medical_date'].widget.input_type = 'date'
        for field in self.fields:
            if self.fields[field].widget.input_type == 'checkbox':
                self.fields[field].widget.attrs['class'] = ''
            else:
                self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True


class JobRollForm(forms.ModelForm):
    class Meta:
        model = JobRoll
        fields = '__all__'
        exclude = common_items_to_execlude

    def __init__(self, user_v, *args, **kwargs):
        super(JobRollForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True
        # self.fields['contract_type'].queryset = LookupDet.objects.filter(lookup_type_fk__lookup_type_name='EMPLOYEE_TYPE', lookup_type_fk__enterprise=user_v.company)
        lookup_type_queryset = XX_EMP_CONTRACT_LOV.objects.filter(enterprise_id=user_v.company.id) # view from DB
        print("***************", lookup_type_queryset)
        self.fields['contract_type'].queryset = LookupDet.objects.filter(id__in='lookup_type_queryset')



        self.fields['position'].queryset = Position.objects.filter((Q(enterprise=user_v.company)), (
                Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        self.fields['payroll'].queryset = Payroll_Master.objects.filter((Q(enterprise=user_v.company)), (
                Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        self.fields['manager'].queryset = Employee.objects.filter(enterprise=user_v.company, emp_end_date__isnull=True)


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = "__all__"
        exclude = common_items_to_execlude

    def __init__(self, *args, **kwargs):
        super(PaymentForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True


# class PaymentTotalCheckFormSet(BaseInlineFormSet):
#     def clean(self):
#         super().clean()
#         total_percentage = sum(f.cleaned_data['percentage'] for f in self.forms)
#         if total_percentage != 100:
#             raise forms.ValidationError("Total percentage must be 100")

Employee_Payment_formset = forms.inlineformset_factory(Employee, Payment, form=PaymentForm, can_delete=True)


class EmployeeElementForm(forms.ModelForm):
    class Meta:
        model = Employee_Element
        fields = "__all__"
        exclude = ('emp_id','element_value') + common_items_to_execlude

    def __init__(self, user , *args, **kwargs):
        super(EmployeeElementForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'
        self.fields['element_id'].queryset = Element.objects.filter(enterprise=user.company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True))
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True


Employee_Element_Inline = forms.inlineformset_factory(Employee, Employee_Element, form=EmployeeElementForm,
                                                      can_delete=False, extra=8)


class EmployeeStructureLinkForm(forms.ModelForm):
    class Meta:
        model = EmployeeStructureLink
        fields = "__all__"
        exclude = common_items_to_execlude + ('employee',)

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(EmployeeStructureLinkForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'
        self.fields['salary_structure'].queryset = SalaryStructure.objects.filter(
            Q(end_date__isnull=True) | Q(end_date__gt=date.today()),enterprise=self.user.company)

        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True

class EmployeeFileForm(forms.ModelForm):
    class Meta:
        model = Employee_File
        fields = "__all__"
        exclude = common_items_to_execlude

    def __init__(self , *args, **kwargs):
        super(EmployeeFileForm , self).__init__(*args , **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True

Employee_Files_inline = forms.inlineformset_factory(Employee, Employee_File, form=EmployeeFileForm, extra=1)


class EmployeeDepandanceForm(forms.ModelForm):
    class Meta:
        model = Employee_Depandance
        fields = "__all__"
        exclude = ('emp_id', 'last_updated_at' ,'created_by','last_updated_by')
    def __init__(self , *args, **kwargs):
        super(EmployeeDepandanceForm , self).__init__(*args , **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True

Employee_depandance_inline = forms.inlineformset_factory(Employee, Employee_Depandance, form=EmployeeDepandanceForm, extra=0)




class Employee_Element_HistoryForm(forms.ModelForm):
    class Meta:
        model = Employee_Element_History
        fields = "__all__"
     
     
    def __init__(self, *args, **kwargs):
        super(Employee_Element_HistoryForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control parsley-validated'
        self.helper = FormHelper()
        self.helper.form_show_labels = True
    


class ConfirmImportForm(forms.Form):
    import_file_name = forms.CharField(widget=forms.HiddenInput())
    original_file_name = forms.CharField(widget=forms.HiddenInput())

    def clean_import_file_name(self):
        data = self.cleaned_data['import_file_name']
        data = os.path.basename(data)
        return data
