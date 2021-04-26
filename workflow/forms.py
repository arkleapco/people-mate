from .models import *
from django import forms

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
        exclude = ('service',)

    def __init__(self, *args, **kwargs):
        super(WorkflowForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            if field not in self.EXCLUDE_FROM_CLASS_STYLE:
                self.fields[field].widget.attrs['class'] = 'form-control'
            self.fields['is_manager'].required = True
            self.fields['is_manager'].widget.attrs['onchange'] = 'change_is_manager_value(this)'


WorkflowInlineFormset = forms.inlineformset_factory(Service, Workflow,
                                                    form=WorkflowForm, can_delete=True, extra=1)
