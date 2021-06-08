from django.shortcuts import render, redirect, get_object_or_404, HttpResponse , reverse
from django.db import IntegrityError
from django.utils import translation
from django.utils.translation import to_locale, get_language
from django.contrib import messages
from datetime import date
from django.http import HttpResponseRedirect
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.contrib.auth.decorators import login_required
from django.views.generic.detail import *
from .models import *
from .forms import *
from django.db.models import Q
from company.models import *
from custom_user.models import User
from django.core.exceptions import ObjectDoesNotExist
from employee.models import Employee, JobRoll
from django.http import JsonResponse
import numpy as np
from django.db.models import Count
from manage_payroll.models import *
from manage_payroll.forms import *
from django.utils.translation import ugettext_lazy as _




################## Messages ##########################################
def success(message_type, obj_type):
    user_lang = to_locale(get_language())
    if message_type == "create":
        if user_lang == 'ar':
            success_msg = '  تم التعديل' + _('obj_type')
        else:
            success_msg = obj_type + ' Created successfully'
    else:
        if user_lang == 'ar':
            success_msg = '  تم الإنشاء' + _('obj_type')
        else:
            success_msg = obj_type +' Updated successfully'

    return success_msg


def fail(message_type,obj_type):
    user_lang = to_locale(get_language())
    if message_type == "create":
        if user_lang == 'ar':
            error_msg = ' لم يتم إنشاء ' + _('obj_type')
        else:
            error_msg = obj_type + ' Cannot be created '
    else:
        if user_lang == 'ar':
            error_msg = ' لم يتم تعديل '  + _('obj_type')
        else:
            error_msg = obj_type + ' Cannot be updated '
    return error_msg

def deleted(message_type ,  obj_type):
    user_lang = to_locale(get_language())
    if message_type == "success":
        if user_lang == 'ar':
            msg = 'تم لحذف  ' + _('obj_type')
        else:
            msg = obj_type + ' Deleted successfully'
    else:
        if user_lang == 'ar':
            msg = ' لم يتم حذف ' + _('obj_type')
        else:
            msg = obj_type + ' Cannot be deletd '
    return msg


################## Performance ##########################################

@login_required(login_url='home:user-login')
def listPerformance(request):
    performances_list = Performance.objects.filter(company=request.user.company, end_date__isnull=True)
    context = {
        'page_title': _('Performances List'),
        'performances_list': performances_list,
    }
    return render(request, 'performance-list.html', context)


@login_required(login_url='home:user-login')
def performanceView(request,pk):
    try:
        performance = Performance.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return False
    page_title = ''
    overall_segments = Segment.objects.filter(performance = performance ,rating= 'Over all')
    core_segments = Segment.objects.filter(performance = performance ,rating= 'Core')
    job_segments = Segment.objects.filter(performance = performance ,rating= 'Job')


    context = {
        'page_title': 'Performance Overview',
        'performance' :performance,
        'overall_segments': overall_segments,
        'core_segments' : core_segments,
        'job_segments' : job_segments,
    }
    return render(request, 'performances.html', context)


@login_required(login_url='home:user-login')
def createPerformance(request):
    user = User.objects.get(id=request.user.id)
    company = user.company
    performance_form = PerformanceForm(company)
    if request.method == 'POST':
        performance_form = PerformanceForm(company, request.POST)
        if performance_form.is_valid():
            performance_obj = performance_form.save(commit=False)
            performance_obj.company = company
            performance_obj.performance_created_by = request.user
            performance_obj.save()

            success_msg = success('create', 'performance')
            messages.success(request, success_msg)

            if 'Save and exit' in request.POST:
                    return redirect('performance:performance-list')
            elif 'Save and add' in request.POST:
                    return redirect('performance:create-performance-reate',
                        per_id = performance_obj.id)
        else:
            error_msg = fail('create','performance')
            messages.error(request, error_msg)

            print(performance_form.errors)
            return redirect('performance:performance-list')
    else:
        myContext = {
        "page_title": _("create performance"),
        "performance_form": performance_form,
        "company":company,
    }
    return render(request, 'create-performance.html', myContext)

@login_required(login_url='home:user-login')
def updatePerformance(request, pk):
    performance = Performance.objects.get(id=pk)
    user = User.objects.get(id=request.user.id)
    company = user.company
    performance_form = PerformanceForm(company, instance=performance)
    if request.method == 'POST':
        performance_form = PerformanceForm(company, request.POST, instance=performance)
        if performance_form.is_valid() :
            performance_obj = performance_form.save(commit=False)
            performance_obj.performance_update_by = request.user
            performance_obj.company = company
            performance_obj.save()

            success_msg = success('update', 'performance')
            messages.success(request, success_msg)

            if 'Save and exit' in request.POST:
                    return redirect('performance:performance-list')
            elif 'Save and add' in request.POST:
                    return redirect('performance:update-performance-reate',
                        pk = pk)
        else:
            error_msg = fail('update', 'performance')
            messages.error(request, error_msg)

            return redirect('performance:performance-edit',pk=pk )
    else:
        myContext = {
        "page_title": _("update performance"),
        "performance_form": performance_form,
        "company":company,
    }
    return render(request, 'create-performance.html', myContext)

@login_required(login_url='home:user-login')
def deletePerformance(request, pk):
    try:
        performance = Performance.objects.get(id=pk)
        performance.end_date = date.today()
        performance.save()
        success_msg = deleted("success", 'performance')
        messages.success(request, success_msg)

    except Exception as e:
        error_msg = deleted("failed", 'performance') + e 
        messages.error(request, error_msg)
        raise e

    return redirect('performance:performance-list')


@login_required(login_url='home:user-login')
def get_positions_for_department(request):
    """
    load jobs and positions according to specific department ajax request
    :param request:
    :return:
    by: gehad
    date: 3/6/2021
    """
    department_id = request.GET.get('department_id')
    department_obj = Department.objects.get(id=department_id)
    positions = Position.objects.filter(department=department_obj, end_date__isnull = True)
    context = {
        'positions': positions,
    }
    return render(request, 'positions_dropdown_list.html', context)


@login_required(login_url='home:user-login')
def get_jobs_for_department(request):
    """
    load jobs  according to specific department ajax request
    :param request:
    :return:
    by: gehad
    date: 3/6/2021
    """
    department_id = request.GET.get('department_id')
    department_obj = Department.objects.get(id=department_id)
    jobs = Position.objects.filter(department=department_obj, end_date__isnull = True).values_list('job__job_name',flat=True)
    context = {
        'jobs' : jobs,
    }
    return render(request, 'jobs_dropdown_list.html', context)

################## Performance Rating ##########################################
@login_required(login_url='home:user-login')
def create_performance_rating(request,per_id):
    overall_form = OverallRatingFormSet(queryset=PerformanceRating.objects.none(),prefix='overall')
    core_form = CoreRatingFormSet(queryset=PerformanceRating.objects.none(), prefix='core')
    jobroll_form = JobrollRatingFormSet(queryset=PerformanceRating.objects.none(), prefix='jobroll')

    performance = Performance.objects.get(id=per_id)

    if request.method == 'POST':
        overall_form = OverallRatingFormSet(request.POST, prefix='overall')
        core_form = CoreRatingFormSet(request.POST, prefix='core')
        jobroll_form = JobrollRatingFormSet(request.POST, prefix='jobroll')


        if overall_form.is_valid():
            #save_overall_form
            for form in overall_form:
                overall_obj = form.save(commit=False)
                overall_obj.performance = performance
                overall_obj.rating = 'Over all'
                overall_obj.rating_created_by = request.user
                overall_obj.save()
        else:
            error_msg = overall_form.errors
            messages.error(request, error_msg)
            return redirect('performance:create-performance-reate',
                        per_id = per_id)
        #save_core_form
        if core_form.is_valid() :  
            for form in core_form:
                core_obj = form.save(commit=False)
                core_obj.performance = performance
                core_obj.rating = 'Core'
                core_obj.rating_created_by = request.user
                core_obj.save()
        else:
            error_msg = core_form.errors
            messages.error(request, error_msg)      
            return redirect('performance:create-performance-reate',
                        per_id = per_id)
        #save_jobroll_form    
        if jobroll_form.is_valid() :    
            for form in jobroll_form:
                jobroll_obj = form.save(commit=False)
                jobroll_obj.performance = performance
                jobroll_obj.rating = 'Job'
                jobroll_obj.rating_created_by = request.user
                jobroll_obj.save()   
        else:
            error_msg = jobroll_form.errors
            messages.error(request, error_msg)  
            return redirect('performance:create-performance-reate',
                        per_id = per_id)     


        success_msg = success('create', 'Rating')
        messages.success(request, success_msg)
        return redirect('performance:management',
                    pk = performance.id)

    else:
        myContext = {
        "page_title": _("create rating"),
        "overall_form": overall_form,
        "core_form": core_form,
        "jobroll_form" :jobroll_form,
        "per_id" : per_id,        
    }
    return render(request, 'create-performance-rates.html', myContext)



@login_required(login_url='home:user-login')
def updatePerformanceRating(request,pk):
    performance = Performance.objects.get(id=pk)
    overall_form = OverallRatingFormSet(queryset=PerformanceRating.objects.filter(performance=performance , rating='Over all', end_date__isnull = True),prefix='overall')
    core_form = CoreRatingFormSet(queryset=PerformanceRating.objects.filter(performance=performance , rating='Core', end_date__isnull = True), prefix='core')
    jobroll_form = JobrollRatingFormSet(queryset=PerformanceRating.objects.filter(performance=performance, rating='Job', end_date__isnull = True), prefix='jobroll')


    if request.method == 'POST':
        overall_form = OverallRatingFormSet(request.POST, prefix='overall', queryset=PerformanceRating.objects.filter(performance=performance, rating='Over all'))
        core_form = CoreRatingFormSet(request.POST, prefix='core', queryset=PerformanceRating.objects.filter(performance=performance, rating='Core'))
        jobroll_form = JobrollRatingFormSet(request.POST, prefix='jobroll', queryset=PerformanceRating.objects.filter(performance=performance, rating='Job'))


        if overall_form.is_valid():
            #save_overall_form
            for form in overall_form:
                overall_obj = form.save(commit=False)
                overall_obj.performance = performance
                overall_obj.rating = 'Over all'
                overall_obj.rating_update_by = request.user
                overall_obj.save()
        else:
            error_msg = overall_form.errors
            messages.error(request, error_msg)
            return redirect('performance:update-performane-reate',
                        per_id = pk)
        #save_core_form
        if core_form.is_valid() :  
            for form in core_form:
                core_obj = form.save(commit=False)
                core_obj.performance = performance
                core_obj.rating = 'Core'
                core_obj.rating_update_by = request.user
                core_obj.save()
        else:
            error_msg = core_form.errors
            messages.error(request, error_msg)      
            return redirect('performance:update-performane-reate',
                        per_id = pk)
        #save_jobroll_form    
        if jobroll_form.is_valid() :    
            for form in jobroll_form:
                jobroll_obj = form.save(commit=False)
                jobroll_obj.performance = performance
                jobroll_obj.rating = 'Job'
                jobroll_obj.rating_update_by = request.user
                jobroll_obj.save()   
        else:
            error_msg = jobroll_form.errors
            messages.error(request, error_msg)  
            return redirect('performance:update-performane-reate',
                        per_id = pk)     


        success_msg = success('update', 'Rating')
        messages.success(request, success_msg)
        return redirect('performance:management',
                    pk = performance.id)

    else:
        myContext = {
        "page_title": _("create rating"),
        "overall_form": overall_form,
        "core_form": core_form,
        "jobroll_form" :jobroll_form,
        "per_id" : pk,        
    }
    return render(request, 'create-performance-rates.html', myContext)
################## performance Management ##########################################

@login_required(login_url='home:user-login')
def performanceManagement(request,pk):
    try:
        performance = Performance.objects.get(id=pk)
        overall_rating = PerformanceRating.objects.filter(performance=performance , rating = 'Over all' , end_date__isnull = True)
        core_rating = PerformanceRating.objects.filter(performance=performance , rating = 'Core', end_date__isnull = True)
        job_rating = PerformanceRating.objects.filter(performance=performance , rating = 'Job', end_date__isnull = True)

    except ObjectDoesNotExist as e:
        return False

    context = {
        'page_title': performance.performance_name,
        'overall_rating' :overall_rating,
        'core_rating' :core_rating,
        'job_rating' :job_rating,
        'pk' : pk,
    }
    return render(request, 'performance-management.html', context)

################## Segment ##########################################

@login_required(login_url='home:user-login')
def listSegment(request,pk, ret_id):
    try:
        performance = Performance.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return False
    page_title = ''
    segments =[]
    if ret_id == 1:
        segments = Segment.objects.filter(performance = performance ,rating= 'Over all' , end_date__isnull = True)
        page_title = 'Overall Segments'

    elif ret_id == 2:
        segments = Segment.objects.filter(performance = performance ,rating= 'Core' ,  end_date__isnull = True)
        page_title  = 'Core Segments'

    elif ret_id == 3:
        segments = Segment.objects.filter(performance = performance ,rating= 'Job' ,  end_date__isnull = True)
        page_title  =  'Jobrole Segments'


    context = {
        'page_title': page_title,
        'segments': segments,
        'ret_id' : ret_id,
        'pk' : pk,
    }
    return render(request, 'segment-list.html', context)



@login_required(login_url='home:user-login')
def createSegment(request,per_id,ret_id):
    question_formset = QuestionInline(queryset=Question.objects.none())
    performance = Performance.objects.get(id = per_id)
    rating =""
    scores = ""

    if ret_id == 1:
        rating = 'Over all'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Over all' , end_date__isnull = True)
    elif ret_id == 2:
        rating = 'Core'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Core' , end_date__isnull = True)
    elif ret_id == 3:
        rating = 'Job'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Job', end_date__isnull = True)
    segment_form = SegmentForm()
    if request.method == 'POST':
        segment_form = SegmentForm(request.POST)
        question_formset = QuestionInline(request.POST)
        if segment_form.is_valid():
            segment_obj = segment_form.save(commit=False)
            segment_obj.performance = performance
            segment_obj.rating = rating
            segment_obj.segment_created_by = request.user
            segment_obj.save()
            if question_formset.is_valid():
                for form in question_formset:
                    obj = form.save(commit=False)
                    obj.title = segment_obj
                    obj.question_created_by = request.user
                    obj.save()
                success_msg = success('create','Segment')
                messages.success(request, success_msg)
            else:
                print(question_formset.errors)
        else:
            error_msg = fail('create', 'Segment')
            messages.error(request, error_msg)
            print(segment_form.errors)

        return redirect('performance:segments',
                        pk = per_id,ret_id=ret_id )

    else:
        myContext = {
        "page_title": _("Create Segment"),
        "segment_form": segment_form,
        "question_formset": question_formset,
        "scores": scores,
        "per_id":per_id,
        "ret_id":ret_id,
        "rating_type" :rating,
    }
    return render(request, 'create-segment.html', myContext)


@login_required(login_url='home:user-login')
def updateSegment(request,pk,ret_id):
    segment = Segment.objects.get(id=pk)
    performance = segment.performance
    segment_form = SegmentForm(instance=segment)
    question_formset = QuestionInline(queryset=Question.objects.filter(title=segment))
    rating =""
    scores = ""
    if ret_id == 1:
        rating = 'Over all'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Over all',  end_date__isnull = True)
    elif ret_id == 2:
        rating = 'Core'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Core' ,  end_date__isnull = True)
    elif ret_id == 3:
        rating = 'Job'
        scores = PerformanceRating.objects.filter(performance=performance , rating= 'Job',  end_date__isnull = True)

    if request.method == 'POST':
        segment_form = SegmentForm(request.POST, instance=segment)
        question_formset = QuestionInline(request.POST ,queryset=Question.objects.filter(title=segment))
        print(request.POST.values)
        if segment_form.is_valid() and question_formset.is_valid():
            segment_obj = segment_form.save(commit=False)
            segment_obj.performance = performance
            segment_obj.rating = rating
            segment_obj.segment_update_by = request.user
            segment_obj.save()

            for form in question_formset:
                obj = form.save(commit=False)
                obj.title = segment_obj
                obj.question_update_by = request.user
                obj.save()

            success_msg = success('update', 'Segment')
            messages.success(request, success_msg)
        else:
            error_msg = fail('update', 'Segment')
            messages.error(request, error_msg)
            print(segment_form.errors)
            print(question_formset.errors)

        return redirect('performance:segments',
                        pk = performance.id,ret_id=ret_id )

    else:
        myContext = {
        "page_title": _("Update Segment"),
        "segment_form": segment_form,
        "question_formset": question_formset,
        "scores": scores,
        "per_id":performance.id,
        "ret_id":ret_id,
    }
    return render(request, 'create-segment.html', myContext)




@login_required(login_url='home:user-login')
def deleteSegment(request, pk, ret_id):
    try:
        segment = Segment.objects.get(id=pk)
        performance = segment.performance
        segment.end_date = date.today()
        success_msg = deleted("success", 'Segment')
        messages.success(request, success_msg)

    except Exception as e:
        error_msg = deleted("failed", 'Segment') + e
        messages.error(request, error_msg)
        raise e

    return redirect('performance:segments',
                        pk = performance.id,ret_id=ret_id )

################ Employee performance  #####################################

@login_required(login_url='home:user-login')
def list_employees_performances_for_manager(request):
    user = request.user
    try:
        employee = Employee.objects.get(user = user,emp_end_date__isnull=True)
    except ObjectDoesNotExist as e:
        error_msg = "You do not have the right to access to this page"
        messages.error(request, error_msg)
        return HttpResponseRedirect(reverse('home:homepage'))

    employees = JobRoll.objects.filter(manager=employee , end_date__isnull = True)
    context = {
        'employees': employees,
        }
    return render(request, 'employees.html', context)

@login_required(login_url='home:user-login')
def employeePerformances(request):
    position_id = request.GET.get('position_id')
    employee_performances =[]
    employee_position = Position.objects.get(id=position_id)
    performances = Performance.objects.filter(company= request.user.company , end_date__isnull = True)
    all_performances_with_no_validations= performances.filter(department = None ,job = None, position = None)
    performances_with_validations = performances.filter(
         (Q(position =  employee_position) & Q(job = employee_position.job) & Q(department = employee_position.department)) 
        |(Q(department = employee_position.department) &  Q(position= employee_position) )
        |(Q(department = employee_position.department) & Q(job = employee_position.job) )
        |(Q(department = employee_position.department))
      )
    # positions = performances.filter(position = employee_position).exclude(position=None)
    # departments  = performances.filter(department= employee_position.department).exclude(department=None)
    # jobs = performances.filter(job = employee_position.job).exclude(job=None)

    employee_performance =[all_performances_with_no_validations, performances_with_validations ]
    for queryset in employee_performance:
        for value in queryset.iterator():
            employee_performances.append(value.performance_name +' : '+ str(value.id))
    my_array = ','.join(employee_performances)

    data = {
        "my_array" :my_array
        }
    return JsonResponse(data)


@login_required(login_url='home:user-login')
def employee_rates(request, pk,emp_id):
    completed_segments = 0
    employee_jobroll = JobRoll.objects.get(id=emp_id)
    emp = employee_jobroll.emp_id.id
    employee = Employee.objects.get(id=emp)
    performance = Performance.objects.get(id =pk)
    segments = Segment.objects.filter(performance=performance , end_date__isnull = True)
    comleted_segments = related_segments(emp_id,performance.id)
    myContext = {
    "employee":employee,
    "performance":performance,
    "segments":segments,
    "completed_segments":completed_segments,
    "comleted_segments" : comleted_segments,
                }
    return render(request, 'employee-rate.html', myContext)

################ Employee Rate  #####################################

@login_required(login_url='home:user-login')
def create_employee_overview_rate(request, per_id,emp_id):
    employee = Employee.objects.get(id=emp_id)
    performance = Performance.objects.get(id=per_id)
    comleted_segments =  related_segments(emp_id,per_id)
    segments = Segment.objects.filter(performance=performance ,end_date__isnull = True)
    employee_performance_form = EmployeePerformanceForm(performance)
    try:
        employee_performance = EmployeePerformance.objects.get(employee = employee )
        return redirect('performance:update-employee-overview',per_id = performance.id ,emp_id=employee.id )
        print("employee_performance.id")
    except :
        if request.method == 'POST':
            employee_performance_form = EmployeePerformanceForm(performance, request.POST)
            if employee_performance_form.is_valid():
                performance_obj = employee_performance_form.save(commit=False)
                performance_obj.employee = employee
                performance_obj.performance = performance
                performance_obj.created_by = request.user
                performance_obj.save()

                success_msg = success('create', 'employee overview')
                messages.success(request, success_msg)
                return redirect('performance:update-employee-overview',
                            per_id = performance.id ,emp_id=employee.id )

            else:
                error_msg = fail('create', 'employee overview')
                messages.error(request, error_msg)
                print(employee_performance_form.errors)
                return redirect('performance:create-employee-overview',
                            per_id = performance.id ,emp_id=employee.id)
        else:
            myContext = {
            "employee":employee,
            "employee_performance_form": employee_performance_form,
            "performance":performance,
            "segments":segments,
            "comleted_segments" :comleted_segments,
        }
        return render(request, 'create-employee-overview.html', myContext)


@login_required(login_url='home:user-login')
def update_employee_overview_rate(request, per_id,emp_id):
    employee = Employee.objects.get(id=emp_id)
    performance = Performance.objects.get(id=per_id)
    segments = Segment.objects.filter(performance=performance , end_date__isnull = True)
    employee_performance = EmployeePerformance.objects.get(employee = employee )
    employee_performance_form = EmployeePerformanceForm(performance, instance=employee_performance)
    comleted_segments =  related_segments(emp_id,per_id)
    if request.method == 'POST':
        employee_performance_form = EmployeePerformanceForm(performance, request.POST , instance=employee_performance)
        if employee_performance_form.is_valid():
            performance_obj = employee_performance_form.save(commit=False)
            performance_obj.employee = employee
            performance_obj.performance = performance
            performance_obj.last_update_by = request.user
            performance_obj.save()

            success_msg = success('update', 'empluee overview')
            messages.success(request, success_msg)
            return redirect('performance:update-employee-overview',per_id = performance.id ,emp_id=employee.id )

        else:
            error_msg = fail('update', 'empluee overview')
            messages.error(request, error_msg)
            print(employee_performance_form.errors)
            return redirect('performance:update-employee-overview',per_id = performance.id ,emp_id=employee.id )
    else:
        myContext = {
        "employee":employee,
        "employee_performance_form": employee_performance_form,
        "performance":performance,
        "segments":segments,
        "comleted_segments":comleted_segments,
    }
    return render(request, 'create-employee-overview.html', myContext)



@login_required(login_url='home:user-login')
def employee_segment_questions(request, pk, emp_id):
    segment = Segment.objects.get(id = pk)
    performance = segment.performance
    employee = Employee.objects.get(id=emp_id)
    segments = Segment.objects.filter(performance=performance , end_date__isnull = True)
    comleted_segments = related_segments(emp_id,performance.id)
    myContext = {
    "segment":segment,
    "employee":employee,
    "performance":performance,
    "segments":segments,
    "comleted_segments" : comleted_segments,
                }
    return render(request, 'employee-segment-questions.html', myContext)


@login_required(login_url='home:user-login')
def create_employee_question_rate(request, pk,emp_id):
    question = Question.objects.get(id=pk)
    segment = question.title
    performance = segment.performance
    segments = Segment.objects.filter(performance=performance , end_date__isnull = True)
    employee = Employee.objects.get(id=emp_id)
    employee_rating_form = EmployeeRatingForm(segment)
    comleted_segments= related_segments(emp_id,performance.id)
    try:
        employee_performance = EmployeeRating.objects.get(question = question )
        return redirect('performance:update-employee-question-rate', pk =pk  ,emp_id=employee.id )
    except :
        if request.method == 'POST':
            employee_rating_form = EmployeeRatingForm(segment, request.POST)
            if employee_rating_form.is_valid():
                performance_rating_obj = employee_rating_form.save(commit=False)
                performance_rating_obj.employee = employee
                performance_rating_obj.question = question
                performance_rating_obj.created_by = request.user
                performance_rating_obj.save()

                success_msg = success('create', 'employee rate')
                messages.success(request, success_msg)
                return redirect('performance:update-employee-question-rate',
                                pk =pk  ,emp_id=employee.id )
            else:
                error_msg = fail('create', 'employee rate')
                messages.error(request, error_msg)
                print(employee_rating_form.errors)
                return redirect('performance:update-employee-question-rate',
                                pk =pk  ,emp_id=employee.id )
    myContext = {
            "segment":segment,
            "employee":employee,
            "performance":performance,
            "segments":segments,
            "question":question,
            "employee_rating_form":employee_rating_form,
            "comleted_segments" : comleted_segments,
                        }
    return render(request, 'create-employee-question-rate.html', myContext)

@login_required(login_url='home:user-login')
def update_employee_question_rate(request, pk, emp_id):
    question = Question.objects.get(id=pk)
    segment = question.title
    performance = segment.performance
    segments = Segment.objects.filter(performance=performance , end_date__isnull = True)
    employee = Employee.objects.get(id=emp_id)
    employee_performance = EmployeeRating.objects.get(question = question )
    employee_rating_form = EmployeeRatingForm(segment, instance=employee_performance)
    comleted_segments = related_segments(emp_id,performance.id)
    if request.method == 'POST':
        employee_rating_form = EmployeeRatingForm(segment, request.POST, instance=employee_performance)
        if employee_rating_form.is_valid():
            performance_rating_obj = employee_rating_form.save(commit=False)
            performance_rating_obj.employee = employee
            performance_rating_obj.question = question
            performance_rating_obj.last_update_by = request.user
            performance_rating_obj.save()

            user_lang = to_locale(get_language())
            success_msg = success('update', ' Employee Rating')
            messages.success(request, success_msg)
            return redirect('performance:update-employee-question-rate',
                            pk =pk  ,emp_id=employee.id )
        else:
            error_msg = fail('update', 'Employee Rating')
            messages.error(request, error_msg)
            print(employee_rating_form.errors)
            return redirect('performance:update-employee-question-rate',
                                pk =pk  ,emp_id=employee.id )
    myContext = {
            "segment":segment,
            "employee":employee,
            "performance":performance,
            "segments":segments,
            "question":question,
            "employee_rating_form":employee_rating_form,
            "comleted_segments" :comleted_segments,
                        }
    return render(request, 'create-employee-question-rate.html', myContext)


@login_required(login_url='home:user-login')
def employee_performances(request, pk):
    employee = Employee.objects.get(id=pk)
    employee_perfomances = EmployeePerformance.objects.filter(employee=employee)
    employee_questions = EmployeeRating.objects.filter(employee=employee)
    if len(employee_perfomances) is not 0:
        page_title = "Performances for" +" " + employee.emp_name
    else:
        page_title = "No Performances for" +" " + employee.emp_name
    myContext = {
        "employee_perfomances":employee_perfomances,
        "employee_questions":employee_questions,
        "page_title": page_title,
        "emp_id":employee.id,

                }
    return render(request, 'employee-performances.html', myContext)


def related_segments(emp_id,per_id):
    """
    segments = []
    question = Question.objects.get(id=ques_id)
    employee_segments = EmployeeRating.objects.filter(employee_id= emp_id, question__title=question.title, question__title__performance=question.title.performance).count()
    """

    segments = []
    performance = Performance.objects.get(id=per_id)
    #employee_segments = EmployeeRating.objects.filter(employee_id= emp_id, question__title__performance=performance).distinct('question__title').count()
    """
    questions = []
    emp_segments = EmployeeRating.objects.filter(employee_id= emp_id, question__title__performance=performance).distinct('question__title')
    for value in emp_segments.iterator():
        segment_title = (value.question.title)
        segment =Segment.objects.get(title=segment_title)
        questions = segment.questions.all()
        segments = EmployeeRating.objects.filter(employee_id= emp_id, question__title=segment_title)
        if len(segments) == len(questions):
            employee_segments = EmployeeRating.objects.filter(employee_id= emp_id, question__title__performance=performance).distinct('question__title').count()
            return employee_segments
        """
    return 0
