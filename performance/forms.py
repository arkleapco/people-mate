from django import forms
from .models import *
from datetime import date
from company.models import Department , Position , Job , Enterprise
from custom_user.models import User
from django.db.models import Q
from django.db import models




# gehad : createPerformance forms.
class PerformanceForm(forms.ModelForm):
    class Meta:
        model = Performance
        fields = '__all__'


    def __init__(self, company, *args, **kwargs):
        self.company = company
        super(PerformanceForm, self).__init__(*args, **kwargs)
        self.fields['start_date'].widget.input_type = 'date'
        self.fields['end_date'].widget.input_type = 'date'
        self.fields['department'].queryset = Department.objects.filter(enterprise=company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True))
        self.fields['job'].queryset = Job.objects.filter(enterprise=company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True))
        self.fields['position'].queryset = Position.objects.filter(department__enterprise=company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True))

        self.fields['department'].widget.attrs['onchange'] = 'get_department_id(this)'
     



        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'



class OverallRatingForm(forms.ModelForm):
    class Meta:
        model = PerformanceRating
        fields = ('score_key' , 'score_value')

    def __init__(self, *args, **kwargs):
        super(OverallRatingForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


OverallRatingFormSet = forms.modelformset_factory(PerformanceRating,extra=0,form=OverallRatingForm, can_delete=False)




class CoreRatingForm(forms.ModelForm):
    class Meta:
        model = PerformanceRating
        fields = ('score_key' , 'score_value')

    def __init__(self, *args, **kwargs):
        super(CoreRatingForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


CoreRatingFormSet = forms.modelformset_factory(PerformanceRating,extra=0,form=CoreRatingForm, can_delete=False)



class JobrollRatingForm(forms.ModelForm):
    class Meta:
        model = PerformanceRating
        fields = ('score_key' , 'score_value')

    def __init__(self, *args, **kwargs):
        super(JobrollRatingForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

JobrollRatingFormSet = forms.modelformset_factory(PerformanceRating, form=JobrollRatingForm, extra=0, can_delete=True)


class SegmentForm(forms.ModelForm):
    class Meta:
        model = Segment
        fields = ('title','desc')

    def __init__(self, *args, **kwargs):
        super(SegmentForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question','help_text','question_type')

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'

QuestionInline = forms.modelformset_factory(Question, form=QuestionForm, extra=1, can_delete=True)



class EmployeePerformanceForm(forms.ModelForm):
    class Meta:
        model = EmployeePerformance
        fields = ('overall_score','core_score','job_score','comment')

    def __init__(self, performance, *args, **kwargs):
        super(EmployeePerformanceForm, self).__init__(*args, **kwargs)
        self.fields['overall_score'].queryset = PerformanceRating.objects.filter(performance=performance, rating= 'Over all')
        self.fields['core_score'].queryset = PerformanceRating.objects.filter(performance=performance, rating= 'Core')
        self.fields['job_score'].queryset = PerformanceRating.objects.filter(performance=performance, rating= 'Job')
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'


class EmployeeRatingForm(forms.ModelForm):
    class Meta:
        model = EmployeeRating
        fields = ('text','score')

    def __init__(self, segment, *args, **kwargs):
        super(EmployeeRatingForm, self).__init__(*args, **kwargs)
        self.fields['score'].queryset = PerformanceRating.objects.filter(performance=segment.performance).filter(rating = segment.rating )
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
