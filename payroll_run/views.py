from io import RawIOBase
from django.db.models.aggregates import Sum
from django.db.models.expressions import OrderBy
from django.db.models.signals import pre_init
from django.http import HttpResponse, request
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.contrib import messages
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from datetime import date
from calendar import monthrange
import datetime
from pathlib import Path
import os
from django.utils.translation import to_locale, get_language
from django.db.models import Q
import calendar
from django.db import IntegrityError
from django.db.models import Avg, Count
import zk
from payroll_run.models import *
from payroll_run.forms import SalaryElementForm, Salary_Element_Inline
from manage_payroll.models import Assignment_Batch, Assignment_Batch_Include, Assignment_Batch_Exclude
from employee.models import Employee_Element, Employee, JobRoll, Payment, EmployeeStructureLink, \
    Employee_Element_History
from leave.models import EmployeeAbsence
from django.utils.translation import ugettext_lazy as _
# ############################################################
from django.conf import settings
from django.template import Context
from django.template.loader import render_to_string
from django.utils.text import slugify
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration  # amira: fixing error on print
# ############################################################
from .new_tax_rules import Tax_Deduction_Amount
from payroll_run.salary_calculations import Salary_Calculator
from django.http import JsonResponse
from employee.models import Employee_Element_History
from django.core.exceptions import ObjectDoesNotExist
from manage_payroll.models import Assignment_Batch, Payroll_Master
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration
from django.template.loader import render_to_string
from datetime import date, datetime
from django.db.models import Count, Sum
from .resources import *
from employee.views import calc_formula
from payroll_run.models  import Element
from time import strptime
from manage_payroll.models import Bank_Master
from employee.forms import PaymentForm
from company.models import Department
import xlwt
from zk import ZK, const
from element_definition.models import StructureElementLink














@login_required(login_url='home:user-login')
def listSalaryView(request):
    salary_list = Salary_elements.objects.filter(emp__enterprise=request.user.company).filter(
        (Q(end_date__gt=date.today()) | Q(end_date__isnull=True))).values('assignment_batch', 'salary_month',
                                                                          'salary_year', 'is_final').annotate(
        num_salaries=Count('salary_month'),total_gross=Sum('gross_salary'),total_net=Sum('net_salary') ).order_by('salary_month', 'salary_year')
    batches = Assignment_Batch.objects.filter(
        payroll_id__enterprise=request.user.company)

    salaryContext = {
        "page_title": _("salary list"),
        "salary_list": salary_list,
        "batches": batches,
    }
    return render(request, 'list-salary.html', salaryContext)


# @login_required(login_url='home:user-login')
def includeAssignmentEmployeeFunction(batch):
    included_emps = set()
    assignment_batch = Assignment_Batch.objects.get(id=batch.id)
    include_query = Assignment_Batch_Include.objects.filter(include_batch_id=assignment_batch).exclude(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=False))
    dept_set = set()
    job_set = set()
    position_set = set()
    emp_set = set()
    for x in include_query:
        if x.dept_id is not None:
            dept_set.add(x.dept_id.id)
        if x.position_id is not None:
            position_set.add(x.position_id.id)
        if x.job_id is not None:
            job_set.add(x.job_id.id)
        if x.emp_id is not None:
            emp_set.add(x.emp_id.id)
    filtered_emps = JobRoll.objects.filter(
        (
            Q(position__department__id__in=dept_set) |
            Q(position__id__in=position_set) |
            Q(position__job__id__in=job_set) |
            Q(emp_id__id__in=emp_set))
    )
    for emp in filtered_emps:
        included_emps.add(emp.emp_id.id)
    return included_emps


# @login_required(login_url='home:user-login')
def excludeAssignmentEmployeeFunction(batch):
    excluded_emps = set()
    assignment_batch = Assignment_Batch.objects.get(id=batch.id)
    exclude_query = Assignment_Batch_Exclude.objects.filter(exclude_batch_id=assignment_batch).exclude(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=False)))
    dept_set = set()
    job_set = set()
    position_set = set()
    emp_set = set()
    for x in exclude_query:
        if x.dept_id is not None:
            dept_set.add(x.dept_id.id)
        if x.position_id is not None:
            position_set.add(x.position_id.id)
        if x.job_id is not None:
            job_set.add(x.job_id.id)
        if x.emp_id is not None:
            emp_set.add(x.emp_id.id)
    filtered_emps = JobRoll.objects.filter(
        (
            Q(position__department__id__in=dept_set) |
            Q(position__id__in=position_set) |
            Q(position__job__id__in=job_set) |
            Q(emp_id__id__in=emp_set))
    )
    for emp in filtered_emps:
        excluded_emps.add(emp.emp_id.id)
    return excluded_emps


def set_context(request, create_payslip_context, month, sal_form):
    """
    set context to when creating payroll, there is error or redirect if payroll ran correctly
    :param request:
    :param create_payslip_context:
    :param month:
    :param sal_form:
    :return:
    by: amira
    date: 26/05/2021
    """
    employees = 0
    not_have_basic = 0
    employees_not_payroll_master = 0

    if create_payslip_context is not None:
        # if no errors found and payroll ran
        if create_payslip_context == {}:
            success_msg = _('Payroll for month {} done successfully').format(
                calendar.month_name[month])
            messages.success(request, success_msg)
            context = "success"
        # there are errors in structure link or basic has no value
        # context = create_payslip_context
        else:
            context = create_payslip_context

    else:
        context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': employees,
            'employees_not_payroll_master': employees_not_payroll_master,
            'not_have_basic': not_have_basic,
        }

    return context


@login_required(login_url='home:user-login')
def createSalaryView(request):
    sal_form = SalaryElementForm(user=request.user)
    employees = 0
    not_have_basic = 0
    month = ''
    # context = {}
    create_payslip_context = None  # returned from create_payslip
    if request.method == 'POST':
        sal_form = SalaryElementForm(request.POST, user=request.user)
        if sal_form.is_valid():
            sal_obj = sal_form.save(commit=False)
            create_payslip_context = create_payslip(request, sal_obj, sal_form)
            month = sal_obj.salary_month
        else:  # Form was not valid
            messages.error(request, sal_form.errors)

    context = set_context(
        request=request, create_payslip_context=create_payslip_context, month=month, sal_form=sal_form)
    if context == "success":
        return redirect('payroll_run:list-salary')
    else:
        return render(request, 'create-salary.html', context)


def month_name(month_number):
    return calendar.month_name[month_number]


@login_required(login_url='home:user-login')
def listSalaryFromMonth(request, month, year, batch_id):
    if batch_id == 0:
        salaries_list = Salary_elements.objects.filter(
            salary_month=month, salary_year=year, end_date__isnull=True, emp__enterprise= request.user.company)
    else:
        salaries_list = Salary_elements.objects.filter(
            salary_month=month, salary_year=year, assignment_batch__id=batch_id, end_date__isnull=True, emp__enterprise= request.user.company)
    monthSalaryContext = {
        'page_title': _('salaries for month {}').format(month_name(month)),
        'salaries_list': salaries_list,
        'v_month': month,
        'v_year': year,
        'batch_id': batch_id
    }
    return render(request, 'list-salary-month.html', monthSalaryContext)


def deleteSalaryFromMonth(request, pk):
    salary = Salary_elements.objects.get(id=pk)
    try:
        salary.delete()
        success_msg = "salary deleted successfully "
        messages.success(request, success_msg)
    except Exception as e:
        error_msg = "faild to delete salary"
        messages.error(request, error_msg)
        print(e)
    return redirect('payroll_run:list-salary')


@login_required(login_url='home:user-login')
def changeSalaryToFinal(request, month, year):
    running_company = request.user.company
    draft_salary = Salary_elements.objects.filter(
        emp__enterprise=running_company, salary_month=month, salary_year=year)
    for draft in draft_salary:
        draft.is_final = True
        draft.save()
    return redirect('payroll_run:list-salary')


@login_required(login_url='home:user-login')
def userSalaryInformation(request, month_number, salary_year, salary_id, emp_id, tmp_format):
    # Get the payslip element to preview
    salary_obj = get_object_or_404(
        Salary_elements,
        salary_month=month_number,
        salary_year=salary_year,
        pk=salary_id
    )
    appear_on_payslip = salary_obj.elements_type_to_run
    if salary_obj.assignment_batch == None:
        batch_id = 0
    else:
        batch_id = salary_obj.assignment_batch.id

    # If the payslip is run on payslip elements get the payslip elements only from history
    # otherwise get the non payslip elements
    if appear_on_payslip == 'appear':
        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=True,
                                                           salary_month=month_number, salary_year=salary_year).values('element_id')
    else:
        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=False,
                                                           salary_month=month_number, salary_year=salary_year).values('element_id')
    basic_earnings_elements = ['Exceptional increase','JulyIncrease','Grants','Allowances','Special Raise','Incentive Actual','Basic'] 
    basic_ded_elements = ['Premium','MEDIACL','Mobinil','Vodafone','?????? ??????????'] 
    emp_elements_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year
                                                                   ).exclude(element_id__element_name__in=basic_earnings_elements).exclude(element_value=0.0).order_by('element_id__sequence')
                                                              
    try:
        basic = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Basic')
    except Employee_Element_History.DoesNotExist:
        basic = 0.0

    try:
        incentive_actual = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Incentive Actual')
    except Employee_Element_History.DoesNotExist:
        incentive_actual = 0.0 

    try:
        special_raise = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Special Raise')
    except Employee_Element_History.DoesNotExist:
        special_raise = 0.0                                                                    
                                                                   
    try:
        allowances = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Allowances')
    except Employee_Element_History.DoesNotExist:
        allowances = 0.0  
    
    try:
        grants = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Grants')
    except Employee_Element_History.DoesNotExist:
        grants = 0.0 
    
    try:
        july_increase = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='JulyIncrease')
    except Employee_Element_History.DoesNotExist:
        july_increase = 0.0 


    try:
        exceptional_increase = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Exceptional increase')
    except Employee_Element_History.DoesNotExist:
        exceptional_increase = 0.0 


    try:
        premium = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Premium')
    except Employee_Element_History.DoesNotExist:
        premium = 0.0


    try:
        mobinil = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Mobinil')
    except Employee_Element_History.DoesNotExist:
        mobinil = 0.0  

    try:
        vodafone = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Vodafone')
    except Employee_Element_History.DoesNotExist:
        vodafone = 0.0 

    try:
        mediacl = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='MEDIACL')
    except Employee_Element_History.DoesNotExist:
        mediacl = 0.0     

    try:
        moda_sabqa = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='?????? ??????????')
    except Employee_Element_History.DoesNotExist:
        moda_sabqa = 0.0 
          

    



    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='deduct', element_id__tax_flag= False,
                                                                      salary_month=month_number, salary_year=salary_year).exclude(element_value=0.0).exclude(
                                                                          element_id__element_name__in=basic_ded_elements).order_by('element_id__element_name')

    
    


    emp_elements_info_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='info-earn',
                                                                   salary_month=month_number, salary_year=salary_year
                                                                   ).exclude(element_value=0.0).order_by('element_id__element_name')

    emp_elements_info_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='info-deduct', element_id__tax_flag= False,
                                                                      salary_month=month_number, salary_year=salary_year).exclude(element_value=0.0).exclude(
                                                                          element_id__element_name__in=basic_ded_elements).order_by('element_id__element_name')

                                                                      
                                                                      
                                                                      
                                                                     
 
    # Not used on the html
    emp_payment = Payment.objects.filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)), emp_id=emp_id)

    monthSalaryContext = {
        'page_title': _('salary information for {}').format(salary_obj.emp),
        'salary_obj': salary_obj,
        'emp_elements_incomes': emp_elements_incomes,
        'emp_elements_deductions': emp_elements_deductions,
        'emp_elements_info_incomes':emp_elements_info_incomes,
        'emp_elements_info_deductions':emp_elements_info_deductions,
        'emp_payment': emp_payment,
        'batch_id': batch_id,
        'basic' :basic,
        'incentive_actual' :incentive_actual,
        'special_raise':special_raise,
        'allowances':allowances,
        'grants':grants,
        'july_increase':july_increase,
        'exceptional_increase':exceptional_increase,
        'premium':premium,
        'mediacl':mediacl,
        "mobinil":mobinil,
        'vodafone':vodafone,
        'moda_sabqa':moda_sabqa
    }
    # emp_elements = Employee_Element.objects.filter(emp_id=emp_id).values('element_id')

    # sc = Salary_Calculator(company=request.user.company, employee=emp_id, elements=emp_elements)
    # test = sc.calc_emp_deductions_amount()
    if tmp_format == "table":
        return render(request, 'emp-payslip.html', monthSalaryContext)
    elif tmp_format == "list":
        return render(request, 'emp-payslip-report.html', monthSalaryContext)


@login_required(login_url='home:user-login')
def render_emp_payslip(request, month, year, salary_id, emp_id):
    template_path = 'payslip.html'
    salary_obj = get_object_or_404(
        Salary_elements, salary_month=month, salary_year=year, pk=salary_id)
    emp_elements = Employee_Element.objects.filter(emp_id=emp_id).exclude(element_value=0.0)
    context = {
        'salary_obj': salary_obj,
        'emp_elements': emp_elements,
        'company_name': request.user.company,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename={date}-donation-receipt.pdf".format(
        date=date.today().strftime('%Y-%m-%d'), )
    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response


@login_required(login_url='home:user-login')
def render_all_payslip(request, month, year,batch):
    template_path = 'all-payslip.html'
    if batch == 0:
        all_salary_obj = Salary_elements.objects.filter( salary_month=month, salary_year=year,end_date__isnull=True, emp__enterprise= request.user.company)   #.values_list('emp', flat=True)
    else:
        all_salary_obj = Salary_elements.objects.filter(salary_month=month, salary_year=year, assignment_batch__id=batch, end_date__isnull=True, emp__enterprise= request.user.company)  #.values_list('emp', flat=True)

    # emp_elements = Employee_Element.objects.filter(emp_id__in = all_salary_obj).order_by('emp_id').values_list('emp_id', flat=True)

    # employess = list(set(emp_elements))
    salary_elements =[]
    emps_salary_obj = []
    # for emp in employess:
    for emp in all_salary_obj:
        emp_salarys = Employee_Element_History.objects.filter(emp_id = emp.emp, salary_month = month, salary_year= year)
        if batch == 0:
            salary_obj = Salary_elements.objects.get( salary_month=month, salary_year=year,end_date__isnull=True, emp__enterprise= request.user.company, emp= emp.emp)
        else:
            salary_obj = Salary_elements.objects.get( salary_month=month, salary_year=year,assignment_batch__id=batch,end_date__isnull=True, emp__enterprise= request.user.company, emp= emp.emp)

        emps_salary_obj.append(salary_obj)
        salary_elements.append(emp_salarys)

    context = {
        'salary_elements': salary_elements,
        'emps_salary_obj':emps_salary_obj,
        'company_name': request.user.company,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename={date}-donation-receipt.pdf".format(
        date=date.today().strftime('%Y-%m-%d'), )
    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response


@login_required(login_url='home:user-login')
def delete_salary_view(request, month, year):
    required_salary_qs = Salary_elements.objects.filter(emp__enterprise=request.user.company,
                                                        salary_month=month, salary_year=year)
    salary_history_element = Employee_Element_History.objects.filter(emp_id__enterprise=request.user.company,
                                                                     salary_month=month, salary_year=year)
    if not required_salary_qs.values_list('is_final', flat=True)[0]:
        required_salary_qs.delete()
        salary_history_element.delete()
    return redirect('payroll_run:list-salary')


@login_required(login_url='home:user-login')
def ValidatePayslip(request):
    assignment_batch = request.GET.get('assignment_batch', None)
    salary_month = request.GET.get('salary_month', None)
    salary_year = request.GET.get('salary_year', None)

    if assignment_batch == '':
        emp_list = Employee.objects.filter(enterprise=request.user.company).filter(
            (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
    else:
        assignment_batch_obj = Assignment_Batch.objects.get(
            id=assignment_batch.id)
        emp_list = Employee.objects.filter(enterprise=request.user.company,
            id__in=includeAssignmentEmployeeFunction(
                assignment_batch_obj)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                assignment_batch_obj))

    salary_elements = Salary_elements.objects.filter(salary_year=salary_year,
                                                     salary_month=salary_month,
                                                     emp__in=emp_list)
    existing_elements = salary_elements.count()
    if existing_elements > 0:
        payslip_created = True
    else:
        payslip_created = False
    return JsonResponse({'payslip_created': payslip_created})


@login_required(login_url='home:user-login')
def DeleteOldPayslip(request):
    assignment_batch = request.GET.get('assignment_batch', None)
    salary_month = request.GET.get('salary_month', None)
    salary_year = request.GET.get('salary_year', None)
    elements_type_to_run = request.GET.get('elements_type_to_run', None)

    if assignment_batch == '':
        emp_list = Employee.objects.filter(
            (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
        salary_to_create = Salary_elements(
            elements_type_to_run=elements_type_to_run,
            salary_month=int(salary_month),
            salary_year=int(salary_year),
        )
    else:
        assignment_batch_obj = Assignment_Batch.objects.get(
            id=assignment_batch)
        emp_list = Employee.objects.filter(
            id__in=includeAssignmentEmployeeFunction(
                assignment_batch_obj)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                assignment_batch_obj))
        salary_to_create = Salary_elements(
            elements_type_to_run=elements_type_to_run,
            salary_month=salary_month,
            salary_year=salary_year,
            assignment_batch=assignment_batch_obj,
        )

    salary_elements_to_delete = Salary_elements.objects.filter(salary_year=salary_year,
                                                               salary_month=salary_month,
                                                               emp__in=emp_list)
    for element in salary_elements_to_delete:
        element.delete()
    if create_payslip(request, salary_to_create):
        return JsonResponse({'true': True})
    else:
        return JsonResponse({'false': False})


def get_elements(user,sal_obj):
    """
    get elements to run
    :param sal_obj:
    :return: queryset of elements
    by: amira
    date: 23/05/2021
    """
    if sal_obj.elements_type_to_run == 'appear':
        elements = Employee_Element.objects.filter(element_id__appears_on_payslip=True,element_id__enterprise=user.company).filter(
            (Q(start_date__lte=date.today()) & (
                Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
    else:
        elements = Employee_Element.objects.filter(element_id=sal_obj.element,element_id__enterprise=user.company).filter(
            Q(start_date__lte=date.today()) & (
                (Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
    return elements

################### check employess hire date  #####
# def check_employees_hire_date(employees, sal_obj, request):
#     """
#         get all employees that hire date befor today 
#         :param employees,sal_obj:
#         :return: queryset of employees
#         by: gehad
#         date: 1/11/2021
#     """
#     emps = []
#     try:
#         absent_element = Element.objects.get(is_absent=True, enterprise = request.user.company)
#     except Element.DoesNotExist:
#         error_msg = _("create (number of vacation days) element first ")
#         messages.error(request, error_msg)
#         return  redirect('payroll_run:create-salary')

#     for emp in employees:
#         if emp.hiredate.year == sal_obj.salary_year:
#             if emp.hiredate.month == sal_obj.salary_month :
#                 employee_unwork_days = emp.employee_working_days_from_hiredate
#                 if employee_unwork_days:
#                     try:
#                         absent_element = Employee_Element.objects.get(emp_id = emp.id , element_id__is_absent=True)
#                         absent_element.element_value = employee_unwork_days
#                         absent_element.save()
#                     except Employee_Element.DoesNotExist:
#                         absent_element = Employee_Element(
#                                         emp_id = emp,
#                                         element_id = absent_element,
#                                         element_value = employee_unwork_days,
#                                         start_date = datetime.today(),
#                                         created_by = request.user,
#                                         creation_date = datetime.today(),
#                                         last_update_by = request.user,
#                                         last_update_date = datetime.today(),)
#                         absent_element.save()
#                     emps.append(emp.id)
#             if emp.hiredate.month < sal_obj.salary_month :
#                 emps.append(emp.id) 
#         if emp.hiredate.year < sal_obj.salary_year:
#             emps.append(emp.id)  
#     return emps                         


# def check_employees_termination_date(employees, sal_obj, request):
#     """
#         get all employees that termination date befor today 
#         :param employees,sal_obj:
#         :return: queryset of employees
#         by: gehad
#         date: 1/11/2021
#     """
#     emps = []
#     try:
#         absent_element = Element.objects.get(is_absent=True, enterprise = request.user.company)
#     except Element.DoesNotExist:
#         error_msg = _("create (number of vacation days) element first ")
#         messages.error(request, error_msg)
#         return  redirect('payroll_run:create-salary')

#     for emp in employees:
#         if emp.terminationdate is not None:
#             if emp.terminationdate.year == sal_obj.salary_year:
#                 if emp.terminationdate.month == sal_obj.salary_month :
#                     employee_work_days = emp.check_employee_work_days
#                     if employee_work_days:
#                         try:
#                             absent_element = Employee_Element.objects.get(emp_id = emp.id , element_id__is_absent=True)
#                             absent_element.element_value = employee_work_days
#                             absent_element.save()
#                         except Employee_Element.DoesNotExist:
#                             absent_element = Employee_Element(
#                                             emp_id = emp,
#                                             element_id = absent_element,
#                                             element_value = employee_work_days,
#                                             start_date = datetime.today(),
#                                             created_by = request.user,
#                                             creation_date = datetime.today(),
#                                             last_update_by = request.user,
#                                             last_update_date = datetime.today(),)
#                             absent_element.save()
#                         emps.append(emp.id)
#                 if emp.terminationdate.month > sal_obj.salary_month :
#                     emps.append(emp.id) 
#             if emp.terminationdate.year > sal_obj.salary_year:
#                 emps.append(emp.id)
#         else:
#             emps.append(emp.id)
#     return emps                         



def get_employees(user,sal_obj,request):
    """
    get employees
    :param sal_obj:
    :return: queryset of employees
    by: amira
    date: 23/05/2021
    """
    employees = 0
    if sal_obj.assignment_batch is not None:
        employees = Employee.objects.filter(enterprise=user.company,
            id__in=includeAssignmentEmployeeFunction(
                sal_obj.assignment_batch)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                sal_obj.assignment_batch))
    else:
        employees = Employee.objects.filter(enterprise=user.company).filter(
            (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True)))  
    # unterminated_employees = check_employees_termination_date(employees, sal_obj, request)
    # hired_employees =  check_employees_hire_date(employees, sal_obj, request)
    # unterminated_employees.extend(hired_employees)
    # employees_queryset = Employee.objects.filter(id__in=unterminated_employees)  
    return employees


def get_structure_type(employee):
    """
    check if employee has structure link
    :param employee:
    :return: structure type or empty string
    by: amira
    date: 25/05/2021
    """
    try:
        emp = EmployeeStructureLink.objects.get(employee=employee, end_date__isnull = True)
        structure = emp.salary_structure.structure_type
    except EmployeeStructureLink.DoesNotExist:
        structure = ''

    return structure


def check_structure_link(employees, sal_form):
    """
    check if all employees have structure link
    :param employees:
    :param sal_form:
    :param not_have_basic:
    :return: dict of errors when an employee doesn't have structure link
    by: amira
    date: 25/05/2021
    """
    not_have_basic = 0
    employees_dont_have_structurelink = []
    create_context = {}
    for employee in employees:
        try:
            EmployeeStructureLink.objects.get(employee=employee,end_date__isnull=True) 
        except EmployeeStructureLink.DoesNotExist:
            msg_str = str(
                _(": don't have Structure Link, Please add Structure Link to them and create again"))
            employees_dont_have_structurelink.append(employee.emp_name)
            employees = ', '.join(employees_dont_have_structurelink) + msg_str
        except Exception as e:
            print(e)
            msg_str = str(
                _(": Something went wrong, Please contact your system administrator"))


    if len(employees_dont_have_structurelink) > 0:
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': employees,
            'not_have_basic': not_have_basic,
            'employees_not_payroll_master': 0,
        }
    return create_context


def check_rule_master(employees, sal_form):
    """
    check if all employees have payroll master
    :param employees:
    :return: dict of errors when an employee doesn't have structure link
    by: gehad
    date: 9/06/2021
    """
    create_context = {}
    not_have_basic = 0
    employees_not_have_payroll_master = []
    not_have_basic = 0
    employees_dont_have_structurelink = []
    for employee in employees:
        try:
            Payroll_Master.objects.get(
                enterprise=employee.enterprise, end_date__isnull=True)
        except Payroll_Master.DoesNotExist:
            msg_str = str(_('You must add Payroll Definition'))
            employees_not_have_payroll_master.append(employee.emp_name)
            employees_not_payroll_master = ', '.join(
                employees_not_have_payroll_master) + msg_str

    if len(employees_not_have_payroll_master) > 0:
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees_not_payroll_master': employees_not_payroll_master,
            'not_have_basic': not_have_basic,

        }
    return create_context


def check_have_basic(employees, sal_form):
    """
    check if all employees have basic salary
    :param employees:
    :param sal_form:
    :return: empty context if all employees have basic salary
    by: amira
    date: 25/05/2021
    """
    employees_dont_have_basic = []
    create_context = {}
    for employee in employees:
        # check that every employee have basic salary
        # ,element_value__isnull=False
        basic_net = Employee_Element.objects.filter(element_id__is_basic=True, emp_id=employee,
                                                    element_value__isnull=False).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        if len(basic_net) == 0:
            msg_str = str(
                _(": don't have basic, add basic to them and create again"))
            employees_dont_have_basic.append(employee.emp_name)
            not_have_basic = ', '.join(employees_dont_have_basic) + msg_str

    if len(employees_dont_have_basic) > 0:
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': 0,  # to not to show employees structure link error
            'employees_not_payroll_master': 0,
            'not_have_basic': not_have_basic,
        }

    return create_context


def save_salary_element(structure, employee, element, sal_obj, total_absence_value, salary_calc, user):
    """
    create salary elements for employee
    :param structure:
    :param employee:
    :param element:
    :param sal_obj:
    :param total_absence_value:
    :param salary_calc:
    :param user:
    :return:
    by: amira
    date: 25/05/2021
    """
    s = Salary_elements(
        emp=employee,
        elements_type_to_run=sal_obj.elements_type_to_run,
        salary_month=sal_obj.salary_month,
        salary_year=sal_obj.salary_year,
        run_date=sal_obj.run_date,
        created_by=user,
        incomes=salary_calc.calc_emp_income(),
        element=element,
        # TODO need to check if the tax is applied
        tax_amount=salary_calc.calc_taxes_deduction(
        ) if structure == 'Gross to Net' else salary_calc.net_to_tax(),
        deductions=salary_calc.calc_emp_deductions_amount(),
        gross_salary=salary_calc.calc_gross_salary(
        ) if structure == 'Gross to Net' else salary_calc.net_to_gross(),
        net_salary=salary_calc.calc_net_salary(
        ) if structure == 'Gross to Net' else salary_calc.calc_basic_net(),
        penalties=total_absence_value,
        assignment_batch=sal_obj.assignment_batch,
        # attribute1 = salary_calc.calc_attribute1(),
        attribute2 = salary_calc.calc_attribute2(),
        # final_net_salary = salary_calc.calc_final_net_salary(),
        insurance_amount = salary_calc.calc_employee_insurance(),
        company_insurance_amount=salary_calc.calc_company_insurance(),
        retirement_insurance_amount=salary_calc.calc_retirement_insurance()
    )
    # if s.emp.insured:
    #     if s.emp.insurance_salary and  s.emp.insurance_salary > 0.0:
    #         s.insurance_amount=salary_calc.calc_employee_insurance()
    #         s.company_insurance_amount=salary_calc.calc_company_insurance()
    #     elif s.emp.retirement_insurance_salary and  s.emp.retirement_insurance_salary > 0.0:
    #         s.retirement_insurance_amount=salary_calc.calc_retirement_insurance()
    s.save()
    if sal_obj.salary_month == 1:
        salary_calc.get_yearly_return(s.gross_salary)


def create_payslip(request, sal_obj, sal_form=None):
    element = sal_obj.element if sal_obj.element else None

    # get elements for all employees.
    elements = get_elements(request.user,sal_obj)

    employees = get_employees(request.user,sal_obj,request)
    

    # TODO: review the include and exclude assignment batch
    # to check every employee have structure link
    employees_structure_link = check_structure_link(
        employees=employees, sal_form=sal_form)
    if employees_structure_link != {}:
        return employees_structure_link  # return dict of errors msgs for structure link

    # to check every employee have basic
    employees_basic = check_have_basic(employees=employees, sal_form=sal_form)
    if employees_basic != {}:
        return employees_basic  # return dict of errors msgs for basic

    # to check every employee have payroll master
    employees_payroll_master = check_rule_master(
        employees=employees, sal_form=sal_form)
    if employees_payroll_master != {}:
        return employees_payroll_master  # return dict of errors msgs for payroll master

    # if all employees have structure link
    if employees_structure_link == {} and employees_basic == {} and employees_payroll_master == {}:
        try:
            for employee in employees:
                try:
                    job_id = JobRoll.objects.get(emp_id=employee, end_date__isnull=True)
                except JobRoll.DoesNotExist:  
                    jobs = JobRoll.objects.filter(emp_id=employee).order_by('end_date')
                    job_id = jobs.last()


                calc_formula(request,1,job_id.id)
                structure = get_structure_type(employee)
                emp_elements = Employee_Element.objects.filter(
                    element_id__in=elements, emp_id=employee).values('element_id')
                sc = Salary_Calculator(
                    company=request.user.company, employee=employee, elements=emp_elements, month=sal_obj.salary_month, year=sal_obj.salary_year)

                absence_value_obj = EmployeeAbsence.objects.filter(employee_id=employee.id).filter(
                    end_date__year=sal_obj.salary_year).filter(end_date__month=sal_obj.salary_month)
                total_absence_value = 0
                for i in absence_value_obj:
                    total_absence_value += i.value
                save_salary_element(structure=structure, employee=employee, element=element, sal_obj=sal_obj,
                                    total_absence_value=total_absence_value, salary_calc=sc, user=request.user)

        except IntegrityError:
            error_msg = _("Payroll for this month created before")
            messages.error(request, error_msg)

    create_context = {}  # return empty dictionary as there is no errors
    return create_context


@login_required(login_url='home:user-login')
def get_month_year_to_payslip_report(request):
    '''
        By:Gehad
        Date: 13/06/2021
        Purpose: get month and year to print payslip report 
    '''
    salary_form = SalaryElementForm(user=request.user)
    employess =Employee.objects.filter(enterprise=request.user.company,emp_end_date__isnull=True).order_by("emp_number")
    if request.method == 'POST':
        year = request.POST.get('salary_year',None)

        from_month = request.POST.get('from_month')
        if len(from_month) == 0: 
            from_month = 0
        else:
            from_month=strptime(from_month,'%b').tm_mon 

               
        to_month = request.POST.get('to_month')
        if len(to_month) == 0: 
            to_month = 0
        else:
            to_month = strptime(to_month,'%b').tm_mon
    
        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
            
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
            
        if 'export' in request.POST:
            return redirect('payroll_run:export-payroll_information',
                from_month=from_month,to_month=to_month,year=year,from_emp =from_emp,to_emp=to_emp )
        elif 'print' in request.POST:
            return redirect('payroll_run:print-payroll',
                from_month=from_month,to_month=to_month,year=year, from_emp=from_emp,to_emp=to_emp ) 
        elif 'export_elements' in request.POST:   
            return redirect('payroll_run:export-payroll',
                from_month=from_month,to_month=to_month,year=year,from_emp=from_emp ,to_emp=to_emp)
        
    myContext = {
        "salary_form": salary_form,
        "employess":employess
    }
    return render(request, 'add-month-year-report.html', myContext)



@login_required(login_url='home:user-login')
def export_employees_information(request,from_month ,to_month, year,from_emp,to_emp):

    '''
        By:Gehad and Mamduh
        Date: 20/09/2021
        Purpose: export  excel sheet of employees payslip information
    '''
    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        query_set = EmployeesPayrollInformation.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,
                history_month__gte= from_month, history_month__lte= to_month,history_year= year,
                information_month__gte=from_month,information_month__lte=to_month,information_year=year,
                company=request.user.company.id)
        
    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
            query_set = EmployeesPayrollInformation.objects.filter(history_month__gte= from_month, history_month__lte= to_month,
            history_year= year,information_month__gte=from_month,information_month__lte=to_month,
            company=request.user.company.id)
        
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            query_set = EmployeesPayrollInformation.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,
                history_year= year,company=request.user.company.id)
           
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    data = EmployeesPayrollInformationResource().export(query_set)
    data.csv
    response = HttpResponse(data.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="employee payroll elements from "' + str(from_month) +"to " +str(to_month) +"  "+ str(year) +".xls"

    return response 




@login_required(login_url='home:user-login')
def export_employees_payroll_elements(request ,from_month,to_month,year,from_emp,to_emp):

    '''
        By:AHD
        Date: 11/7/2021
        Purpose: export  excel sheet of employees payslip information
    '''
    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        if request.user.company.id == 2 :
            query_set = EmployeePayrollElements2.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
            data = EmployeePayrollElements2Resource().export(query_set)
        
        if request.user.company.id == 3:
            query_set = EmployeePayrollElements3.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
            data = EmployeePayrollElements3Resource().export(query_set)
        
        if request.user.company.id == 4 :
            query_set = EmployeePayrollElements4.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
            data = EmployeePayrollElements4Resource().export(query_set)
    
    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
            if request.user.company.id == 2 :
                query_set = EmployeePayrollElements2.objects.filter(payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
                data = EmployeePayrollElements2Resource().export(query_set)
            
            if request.user.company.id == 3:
                query_set = EmployeePayrollElements3.objects.filter(payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
                data = EmployeePayrollElements3Resource().export(query_set)
            
            if request.user.company.id == 4 :
                query_set = EmployeePayrollElements4.objects.filter(payroll_month__gte= from_month, payroll_month__lte= to_month,payroll_year= year, enterprise_id=request.user.company.id).order_by("payroll_month")
                data = EmployeePayrollElements4Resource().export(query_set)
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            if request.user.company.id == 2 :
                query_set = EmployeePayrollElements2.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,  enterprise_id=request.user.company.id).order_by("emp_number")
                data = EmployeePayrollElements2Resource().export(query_set)
            
            if request.user.company.id == 3:
                query_set = EmployeePayrollElements3.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,  enterprise_id=request.user.company.id).order_by("emp_number")
                data = EmployeePayrollElements3Resource().export(query_set)
            
            if request.user.company.id == 4 :
                query_set = EmployeePayrollElements4.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp, enterprise_id=request.user.company.id).order_by("emp_number")
                data = EmployeePayrollElements4Resource().export(query_set)
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    data.csv
    response = HttpResponse(data.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename="employee payroll elements from "' + str(from_month) +"to " +str(to_month) +"  "+ str(year) +".xls"
    return response 



@login_required(login_url='home:user-login')
def get_employees_information(request,from_month ,to_month,year,from_emp,to_emp):
    '''
        By:Gehad
        Date: 9/06/2021
        Purpose: print report of employees payslip information
    '''
    template_path = 'employees_payroll_report.html'
    # month_obj = Salary_elements.objects.filter(salary_month=month).first()
    # if month_obj:
    #     month_name = month_obj.get_salary_month_display()
    # else:
    #     month_name=''

    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        employees_information = Salary_elements.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp,emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")

    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
             employees_information = Salary_elements.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            employees_information = Salary_elements.objects.filter(salary_year=year,
                    emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp,emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("emp__emp_number")
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')
    
    
    for employee in employees_information:
        basic = Employee_Element_History.objects.filter(emp_id__enterprise= request.user.company, emp_id=employee['emp'],
                                                        salary_month__gte=from_month,salary_month__lte=to_month , salary_year=year, element_id__is_basic=True).values_list('element_value', flat=True)                                              
        try:
            basic[0]
            emp_basic = round(basic[0], 2)
        except IndexError:
            emp_basic = 0
        employee['basic'] = emp_basic
        employee['allowences'] = employee['incomes'] - employee['basic']

    context = {
        'employees_information': employees_information,
        'company': request.user.company,
        'year': year,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename=employee payroll elements from {from_month} to {to_month}-{year}.pdf".format(
        from_month=from_month ,to_month=to_month, year=year)

    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response


def render_payslip_report(request, month_number, salary_year, salary_id, emp_id):
    '''
        By:Mamdouh , Gehad
        Date: 10/06/2021
        Purpose: print report of leaves
    '''
    template_path = 'payslip-report.html'
    salary_obj = get_object_or_404(
        Salary_elements,
        salary_month=month_number,
        salary_year=salary_year,
        pk=salary_id
    )
    insurance_amount = salary_obj.insurance_amount

    appear_on_payslip = salary_obj.elements_type_to_run
    if salary_obj.assignment_batch == None:
        batch_id = 0
    else:
        batch_id = salary_obj.assignment_batch.id

    # If the payslip is run on payslip elements get the payslip elements only from history
    # otherwise get the non payslip elements
    if appear_on_payslip == 'appear':

        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=True,
                                                           salary_month=month_number, salary_year=salary_year).values('element_id')
    else:
        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=False,
                                                           salary_month=month_number, salary_year=salary_year).values('element_id')

    emp_elements_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   ).exclude(element_value=0.0).order_by('element_id__sequence')
    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='deduct',
                                                                      salary_month=month_number, salary_year=salary_year
                                                                      ).exclude(element_value=0.0).order_by('element_id__sequence')
    emp_elements_info_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='info-earn',
                                                                   salary_month=month_number, salary_year=salary_year
                                                                   ).exclude(element_value=0.0).order_by('element_id__element_name')

    emp_elements_info_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='info-deduct', element_id__tax_flag= False,
                                                                      salary_month=month_number, salary_year=salary_year).exclude(element_value=0.0).order_by('element_id__element_name')
 
    # Not used on the html
    emp_payment = Payment.objects.filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)), emp_id=emp_id)

    total_incomes = Employee_Element_History.objects.filter(emp_id=emp_id,
                                                            element_id__classification__code='earn', salary_month=month_number, salary_year=salary_year).values("emp_id").annotate(Sum('element_value')).values_list('element_value__sum', flat=True)
    try:
        total_incomes[0]
        emp_total_incomes = total_incomes[0]
    except IndexError:
        emp_total_incomes = 0

    total_deductions = Employee_Element_History.objects.filter(emp_id=emp_id,
            element_id__classification__code='deduct', salary_month=month_number, salary_year=salary_year).values("emp_id").annotate(Sum('element_value')).values_list('element_value__sum' , flat=True)

    # structurelink = EmployeeStructureLink.objects.get(employee = emp_id , end_date__isnull= True)
    # emp_structurelink =structurelink.salary_structure.structure_type
    # if emp_structurelink == 'Gross to Net':
    try:
        total_deductions[0]
        emp_total_deductions= total_deductions[0] + insurance_amount
    except :
        emp_total_deductions = insurance_amount

    gross = salary_obj.gross_salary 

    another_ded = salary_obj.tax_amount + salary_obj.attribute2

    emp_total_deductions += another_ded
    # else:
    #     try:
    #         total_deductions[0]
    #         emp_total_deductions= total_deductions[0]  + insurance_amount
    #     except :
    #         emp_total_deductions = insurance_amount

    #     gross = salary_obj.gross_salary
    try:
        emp_position = JobRoll.objects.get(
            emp_id=emp_id, end_date__isnull=True).position.position_name
    except Exception as e:
        emp_position = "Has No Position"

    try:
        emp_payment_method = Payment.objects.get(emp_id=emp_id,end_date__isnull=True)
    except Payment.DoesNotExist:    
        emp_payment_method = "Has No Payment Method" 
    except Exception as e:
        emp_payment_method = Payment.objects.filter(emp_id=emp_id,end_date__isnull=True).first()


        
        


    BASE_DIR = Path(__file__).resolve().parent.parent
    path = os.path.join( BASE_DIR , 'static') 
    
    context = {
        'path':path,
        'company_name': request.user.company,
        'page_title': _('salary information for {}').format(salary_obj.emp),
        'salary_obj': salary_obj,
        'emp_elements_incomes': emp_elements_incomes,
        'emp_elements_deductions': emp_elements_deductions,
        'emp_elements_info_deductions':emp_elements_info_deductions,
        'emp_elements_info_incomes' :emp_elements_info_incomes,
        'emp_payment': emp_payment,
        'batch_id': batch_id,
        'emp_total_incomes': emp_total_incomes,
        'emp_total_deductions': emp_total_deductions,
        'insurance_amount': insurance_amount,
        'gross': gross,
        'emp_position': emp_position,
        'emp_payment_method':emp_payment_method,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename={date}-donation-receipt.pdf".format(
        date=date.today().strftime('%Y-%m-%d'), )
    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response







@login_required(login_url='home:user-login')
def get_month_year_employee_company_insurance_report(request):
    salary_form = SalaryElementForm(user=request.user)
    employess =Employee.objects.filter(enterprise=request.user.company,emp_end_date__isnull=True).order_by("emp_number")
    if request.method == 'POST':
        year = request.POST.get('salary_year',None)

        from_month = request.POST.get('from_month')
        if len(from_month) == 0: 
            from_month = 0
        else:
            from_month=strptime(from_month,'%b').tm_mon 

               
        to_month = request.POST.get('to_month')
        if len(to_month) == 0: 
            to_month = 0
        else:
            to_month = strptime(to_month,'%b').tm_mon
    
        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
            
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
            
        if 'export' in request.POST:
            return redirect('payroll_run:export-export-employees-company-insurance-share',
                from_month=from_month,to_month=to_month,year=year,from_emp =from_emp,to_emp=to_emp )
        if 'print' in request.POST:
            return redirect('payroll_run:print-employees-company-insurance-share',
                from_month=from_month,to_month=to_month,year=year, from_emp=from_emp,to_emp=to_emp ) 
    myContext = {
        "salary_form": salary_form,
        "employess":employess
    }
    return render(request, 'add-month-year-employee-company-insurance-report.html', myContext)








@login_required(login_url='home:user-login')
def export_employees_company_insurance_share(request,from_month ,to_month, year,from_emp,to_emp):
    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        query_set = EmployeeCompanyInsuranceShare.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,
                salary_month__gte=from_month,salary_month__lte=to_month,salary_year=year,
                company_id=request.user.company.id)
        
    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
            query_set = EmployeeCompanyInsuranceShare.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month,salary_year=year,
                company_id=request.user.company.id)
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-employee-company-insurance-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            query_set = EmployeeCompanyInsuranceShare.objects.filter(emp_number__gte= from_emp,emp_number__lte= to_emp,
                salary_year= year,company_id=request.user.company.id)
           
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-employee-company-insurance-report')

    data = EmployeeCompanyInsuranceShareResource().export(query_set)
    
    data = EmployeeCompanyInsuranceShareResource().export(query_set)
    data.csv
    response = HttpResponse(data.xls, content_type='application/vnd.ms-excel')
    response['Content-Disposition'] = 'attachment; filename= Social Insurance Company Share from "' + str(from_month) +"to " +str(to_month) +"  "+ str(year) +".xls"

    return response 










@login_required(login_url='home:user-login')
def print_employees_company_insurance_share(request,from_month ,to_month,year,from_emp,to_emp):
    template_path = 'employees_company_insurance_share_report.html'
    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        employees_information = EmployeeCompanyInsuranceShare.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    emp_number__gte=from_emp,emp_number__lte=to_emp,company_id=request.user.company.id).values(
                    'insurance_amount', 'company_insurance_amount', 'emp_name' , 'emp_number').order_by("salary_month")

    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
             employees_information = EmployeeCompanyInsuranceShare.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    company_id=request.user.company.id).values(
                    'insurance_amount', 'company_insurance_amount',  'emp_name' , 'emp_number').order_by("salary_month")
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-employee-company-insurance-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            employees_information = EmployeeCompanyInsuranceShare.objects.filter(salary_year=year,
                    emp_number__gte=from_emp,emp_number__lte=to_emp,company_id=request.user.company.id).values(
                    'insurance_amount', 'company_insurance_amount',   'emp_name' , 'emp_number').order_by("salary_month")
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-employee-company-insurance-report')
    
    context = {
        'employees_information': employees_information,
        'company': request.user.company,
        'year': year,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename=Social Insurance Company Share from {from_month} to {to_month}-{year}.pdf".format(
        from_month=from_month ,to_month=to_month, year=year)

    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response




@login_required(login_url='home:user-login')
def get_bank_report(request):
    salary_form = SalaryElementForm(user=request.user)
    payment_form = PaymentForm()
    payment_form.fields['bank_name'].queryset = Bank_Master.objects.filter(
            enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
    if request.method == 'POST':
        year = request.POST.get('salary_year',None)
        month_in_words = request.POST.get('month')
        month=strptime(month_in_words,'%b').tm_mon  
        bank_id = request.POST.get('bank_name',None)
        if len(bank_id) == 0: 
            bank_id = 0
        return redirect('payroll_run:export-bank-report',bank_id=bank_id,month=month,year=year)  
    myContext = {
        'payment_form': payment_form,
        'salary_form':salary_form,
    }
    return render(request, 'export-bank-report.html', myContext)








@login_required(login_url='home:user-login')
def export_bank_report(request,bank_id,month,year):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Bank Report.xls"'
    run_date = str(year)+'-'+str(month).zfill(2)+'-01'
    month_last_date = monthrange(year, month)[1] # like: num_days = 28
    end_run_date = str(year)+'-'+str(month).zfill(2)+'-'+str(month_last_date)  ## 

    if bank_id != 0:
        try:
            bank = Bank_Master.objects.get(id = bank_id)
            employees_with_bank = Payment.objects.filter(bank_name= bank , emp_id__enterprise= request.user.company).filter(
                start_date__lte=end_run_date).filter(Q(end_date__gte=run_date) | Q(end_date__isnull=True)).filter(
                    Q(emp_id__emp_end_date__gte=run_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
                        Q(emp_id__terminationdate__gte=run_date)|Q(emp_id__terminationdate__isnull=True))
        except Bank_Master.DoesNotExist:
            messages.error(request, 'this bank not exist, conntact with admin')
            return redirect('payroll_run:bank-report')
    else:
        employees_with_bank = Payment.objects.filter(payment_type__type_name= 'BANK', emp_id__enterprise= request.user.company).filter(
             start_date__lte=end_run_date).filter(
                Q(end_date__gte=run_date) | Q(end_date__isnull=True)).filter(
                    Q(emp_id__emp_end_date__gte=run_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
                        Q(emp_id__terminationdate__gte=run_date)|Q(emp_id__terminationdate__isnull=True))

    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Bank Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Employee Code','Employee Name','Account Number',  'Bank', 'Net Salary', ]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    for emp in employees_with_bank:
        try:
            salary_obj = Salary_elements.objects.get(emp= emp.emp_id, salary_month=month,salary_year=year)
            emp_dic = []
            emp_dic.append(str(emp.emp_id.emp_number))
            emp_dic.append(emp.emp_id.emp_name)
            emp_dic.append(str(emp.account_number))
            emp_dic.append(str(emp.bank_name.bank_name))
            emp_dic.append(round(salary_obj.net_salary,2))
            emp_list.append(emp_dic)
        except Salary_elements.DoesNotExist:
            pass
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response
    
############################################### Cash Report #######################
@login_required(login_url='home:user-login')
def get_cash_report(request):
    salary_form = SalaryElementForm(user=request.user)    
    if request.method == 'POST':
        year = request.POST.get('salary_year',None)
        month_in_words = request.POST.get('month')
        month=strptime(month_in_words,'%b').tm_mon 
        return redirect('payroll_run:export-cash-report',
                    month=month,year=year)
    myContext = {
        "salary_form": salary_form}
    return render(request, 'export-cash-report.html', myContext)





@login_required(login_url='home:user-login')
def export_cash_report(request,month,year):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Cash Report.xls"'
    run_date = str(year)+'-'+str(month).zfill(2)+'-01'
    month_last_date = monthrange(year, month)[1] # like: num_days = 28
    end_run_date = str(year)+'-'+str(month).zfill(2)+'-'+str(month_last_date)  ## 

    employees_without_bank = list(Payment.objects.filter(payment_type__type_name='Cash',emp_id__enterprise= request.user.company).filter(
        start_date__lte=end_run_date).filter(
        Q(end_date__gte=run_date) | Q(end_date__isnull=True)).filter(
            Q(emp_id__emp_end_date__gte=run_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=run_date)|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)) 

    salary_obj = Salary_elements.objects.filter(emp__id__in = employees_without_bank, salary_month=month,
    salary_year=year)



    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Cash Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = [ 'Employee Code','Employee Name','Net Salary',]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    for emp in salary_obj:
        emp_dic = []
        emp_dic.append(emp.emp.emp_number)
        emp_dic.append(emp.emp.emp_name)
        emp_dic.append(round(emp.net_salary,2))
        emp_list.append(emp_dic)
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response

























@login_required(login_url='home:user-login')
def get_year_and_month_for_totals_report(request):
    salary_form = SalaryElementForm(user=request.user)
    employess =Employee.objects.filter(enterprise=request.user.company).order_by("emp_number")
    # .filter(
    #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
    if request.method == 'POST': 
        year = request.POST.get('salary_year',None)
        month_in_words = request.POST.get('from_month')
        month=strptime(month_in_words,'%b').tm_mon 
        if 'export deductions' in request.POST:
            return redirect('payroll_run:deduction-report',
                month=month,year=year )
        elif 'export earnings' in request.POST:
            return redirect('payroll_run:earnings-report',
                month=month,year=year) 
    myContext = {
        "employess":employess,
        'salary_form':salary_form,
    }
    return render(request, 'totals-report.html', myContext)













@login_required(login_url='home:user-login')
def export_all_deductions_report(request,year,month):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Cost Center Monthly Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Cost Center Monthly Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    

    deduct_elements__salary_structure = list(StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company,element__classification__code='deduct').filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).values_list("element__element_name",flat=True))
    deduct_unique_elements = set(deduct_elements__salary_structure )
    
    
    columns = ['Department Name','Total Deduction','Net','Tax','?????????? ??????????????' ,'company Insurance Amount'  
        'Insurance Amount']

    columns[1:1] = deduct_unique_elements

    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    # monthes_list = list(range(from_month, to_month+1))
    emp_job_roll_query = JobRoll.objects.filter(
        emp_id__enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
            Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)) 
        
    dept_list = Department.objects.filter(enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')
    # for month in monthes_list:
    for dep in dept_list:
        emp_job_roll_list = emp_job_roll_query.filter(position__department=dep).values_list("emp_id",flat=True)
        emps_ids = set(emp_job_roll_list) 
        
        employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month= month,salary_year=year)
        salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month=month,salary_year=year)

            
        total_deductions= salary_elements_query.aggregate(Sum('deductions'))['deductions__sum']                 
        net= salary_elements_query.aggregate(Sum('net_salary'))['net_salary__sum']  
        tax= salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum'] 
        attribute2= salary_elements_query.aggregate(Sum('attribute2'))['attribute2__sum'] 
        company_insurance_amount= salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'] 
        insurance_amount= salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum'] 

        

        emp_dic = []
        emp_dic.append(dep.dept_name)
        for element in deduct_unique_elements:
            sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(round(sum_of_element,2)) 
        emp_dic.append(round(total_deductions,2))
        emp_dic.append(round(net,2))   
        emp_dic.append(round(tax,2)) 
        emp_dic.append(round(attribute2,2))   
        emp_dic.append(round(company_insurance_amount,2))   
        emp_dic.append(round(insurance_amount,2))     

        emp_list.append(emp_dic)       
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response








@login_required(login_url='home:user-login')
def export_all_earnings_report(request,year,month):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Cost Center Monthly Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Cost Center Monthly Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    earning_elements__salary_structure = list(StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company,element__classification__code='earn').filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).exclude(
        element__is_basic=True).order_by("element__sequence").values_list("element__element_name",flat=True))
    earning_unique_elements = set(earning_elements__salary_structure)
    
    
    columns = ['Department Name','Total Earnings']

    columns[1:1] = earning_unique_elements

    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    # monthes_list = list(range(from_month, to_month+1))
    emp_job_roll_query = JobRoll.objects.filter(
        emp_id__enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
            Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)) 
        
    dept_list = Department.objects.filter(enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')
    # for month in monthes_list:
    for dep in dept_list:
        emp_job_roll_list = emp_job_roll_query.filter(position__department=dep).values_list("emp_id",flat=True)
        emps_ids = set(emp_job_roll_list) 
        
        employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month= month,salary_year=year)
        salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month=month,salary_year=year)

            
        total_earnings = salary_elements_query.aggregate(Sum('incomes'))['incomes__sum'] 


        emp_dic = []
        emp_dic.append(dep.dept_name)
        for element in earning_unique_elements:
            sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(round(sum_of_element,2)) 
        emp_dic.append(round(total_earnings,2))
        emp_list.append(emp_dic)       
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response







@login_required(login_url='home:user-login')
def export_total_elements_report(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Total Elements Report.xls"'
    now = datetime.now()
    year = now.year
    month = now.month
    departments = Department.objects.filter(enterprise=request.user.company).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')
    
    department_list = []
    for department in departments:
        elements_list = []
        employees = list(JobRoll.objects.filter(
            emp_id__enterprise=request.user.company,position__department= department).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
                Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).values_list('emp_id' , flat=True))
        
        
        salary_obj = Salary_elements.objects.filter(emp__in = employees, salary_month=month,
        salary_year=year)
        
        basic = Employee_Element.objects.filter(emp_id__in = employees, element_id__is_basic= True).aggregate(Sum('element_value'))['element_value__sum']
        social_increase = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Special Raise').aggregate(Sum('element_value'))['element_value__sum']
        grants = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Grants').aggregate(Sum('element_value'))['element_value__sum']
        special_raise = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Social Increase').aggregate(Sum('element_value'))['element_value__sum']     
        allowances =  Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Allowances').aggregate(Sum('element_value'))['element_value__sum']
        incentive_actual = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Incentive Actual').aggregate(Sum('element_value'))['element_value__sum']                                 
        over_time = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Over time').aggregate(Sum('element_value'))['element_value__sum']                                 
        adjusting_deserve = Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name='Adjusting Deserve').aggregate(Sum('element_value'))['element_value__sum'] 
        
        
        total_earning = salary_obj.aggregate(Sum('gross_salary'))['gross_salary__sum']
        total_deductions = salary_obj.aggregate(Sum('deductions'))['deductions__sum']  
        tax = salary_obj.aggregate(Sum('tax_amount'))['tax_amount__sum']  
        attribute2 = salary_obj.aggregate(Sum('attribute2'))['attribute2__sum']  
        net = salary_obj.aggregate(Sum('net_salary'))['net_salary__sum'] 
        employee_insurance = Employee.objects.filter(id__in = employees).aggregate(Sum('insurance_salary'))['insurance_salary__sum'] 
        
        elements_list.append(department.dept_name)
        # elements_list.append(round(basic, 2))
        elements_list.append(round(basic, 2) if basic is not None  else 0)
        # elements_list.append(round(social_increase,2))
        elements_list.append(round(social_increase, 2) if social_increase is not None  else 0)
        # elements_list.append(round(grants,2))
        elements_list.append(round(grants, 2) if grants is not None  else 0)
        # elements_list.append(round(special_raise,2))
        elements_list.append(round(special_raise, 2) if special_raise is not None  else 0)
        # elements_list.append(round(allowances,2))
        elements_list.append(round(allowances, 2) if allowances is not None  else 0)
        # elements_list.append(round(incentive_actual,2))
        elements_list.append(round(incentive_actual, 2) if incentive_actual is not None  else 0)
        # elements_list.append(round(over_time,2))
        elements_list.append(round(over_time, 2) if over_time is not None  else 0)
        # elements_list.append(round(adjusting_deserve,2))
        elements_list.append(round(adjusting_deserve, 2) if adjusting_deserve is not None  else 0)
        # elements_list.append(round(total_earning,2))
        elements_list.append(round(total_earning, 2) if total_earning is not None  else 0)


        # elements_list.append(round(total_deductions,2))
        elements_list.append(round(total_deductions, 2) if total_deductions is not None  else 0)

        # elements_list.append(round(tax,2))
        elements_list.append(round(tax, 2) if tax is not None  else 0)

        # elements_list.append(round(attribute2,2))
        elements_list.append(round(attribute2, 2) if attribute2 is not None  else 0)

        # elements_list.append(round(net,2))
        elements_list.append(round(net, 2) if net is not None  else 0)

        # elements_list.append(round(employee_insurance,2))
        elements_list.append(round(employee_insurance, 2) if employee_insurance is not None  else 0)
        department_list.append(elements_list)


    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Total Elements Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = ['Department Name', 'Basic', 'Social Increase','Grants','Special Raise','Allowances' , 'Incentive Actual',
         'Total Over Time','Adjusting Deserve','Total Earning','Total Deductions', 'Tax', '?????????? ?????????? ?????????????? ', 'Final Net' ,'Employee Insurance'  ]




    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()
    
    for row in department_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response

