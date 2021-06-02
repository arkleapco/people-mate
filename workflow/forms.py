from .models import *
from django import forms
from employee.models import JobRoll
from django.db.models import Q
from datetime import date
from company.models import Position

"""
By Gehad, amira
date: 30/3/2021
"""


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super(ServiceForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class WorkflowForm(forms.ModelForm):
    EXCLUDE_FROM_CLASS_STYLE = ['is_manager', 'is_action', 'is_notify']

    class Meta:
        model = Workflow
        exclude = ('service', 'workflow_created_by', 'workflow_update_by')

    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user')
        super(WorkflowForm, self).__init__(*args, **kwargs)
        self.fields['position'].queryset = Position.objects.filter(department__enterprise=user.company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True))

        self.fields['is_manager'].widget.attrs['onchange'] = 'change_is_manager_value(this)'
        self.fields['is_action'].widget.attrs['onchange'] = 'change_is_action(this)'
        self.fields['is_notify'].widget.attrs['onchange'] = 'change_is_notify(this)'
        self.fields['position'].widget.attrs['onchange'] = 'select_position_employees(this)'
        # self.fields['employee'].queryset = Employee.objects.none()
        # print('self.data ', self.data)
        # print('***** ', self.data)
        #
        # if 'workflow_set-0-position' in self.data:
        #     print('yes')
        #     try:
        #
        #         position = int(self.data.get('workflow_set-0-position'))
        #
        #         job_roll = JobRoll.objects.filter(position=position).values('emp_id')
        #         self.fields['employee'].queryset = Employee.objects.filter(id__in=job_roll)
        #         print('try done successfully')
        #     except Exception as e:
        #         print('exception occurred ', e)


        for field in self.fields:
            if field not in self.EXCLUDE_FROM_CLASS_STYLE:
                self.fields[field].widget.attrs['class'] = 'form-control'






WorkflowInlineFormset = forms.inlineformset_factory(Service, Workflow,
                                                    form=WorkflowForm, can_delete=True, extra=1)

class ServiceRequestWorkflowForm(forms.ModelForm):
    class Meta:
        model = ServiceRequestWorkflow
        fields = ('reason',)

    def __init__(self, *args, **kwargs):
        super(ServiceRequestWorkflowForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
