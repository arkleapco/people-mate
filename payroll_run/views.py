from io import RawIOBase
from django.contrib.messages.api import error
from django.db.models.aggregates import Sum
from django.db.models.expressions import OrderBy
from django.http import HttpResponse, request
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.contrib import messages
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from django.utils.translation import to_locale, get_language
from django.db.models import Q
import calendar
from django.db import IntegrityError
from django.db.models import Avg, Count
from payroll_run.models import *
from payroll_run.forms import SalaryElementForm, Salary_Element_Inline
from manage_payroll.models import Assignment_Batch, Assignment_Batch_Include, Assignment_Batch_Exclude
from employee.models import Employee_Element, Employee, JobRoll, Payment, EmployeeStructureLink, \
    Employee_Element_History
from leave.models import EmployeeAbsence
from employee.forms import EmployeeForm
from django.utils.translation import ugettext_lazy as _
# ############################################################
from django.conf import settings
from django.template import Context
from django.template.loader import render_to_string
from django.utils.text import slugify
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration  
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
from django.contrib.auth.models import Group, User
from num2words import num2words
from company.models import Department
import xlwt  
from element_definition.models import StructureElementLink, SalaryStructure    
from payroll_run.tax_settlement import Tax_Settlement_Deduction_Amount  






def get_employees_for_to_payroll(user):
    user_group = user.groups.all()[0].name 
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=user.company,
                    salary_structure__created_by=user,end_date__isnull=True).values_list("employee", flat=True)
        emp_job_roll_list = JobRoll.objects.filter(emp_id__in = emp_salry_structure,
            emp_id__enterprise=user.company).values_list("emp_id", flat=True)
            # .filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
            # Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
            #     Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id", flat=True)
       
        emp_list = Employee.objects.filter(id__in = emp_job_roll_list, enterprise=user.company)
        # .filter(
        #     Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True)).order_by("emp_number")
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=user.company,end_date__isnull=True).values_list("employee", flat=True)
        emp_job_roll_list = JobRoll.objects.filter(emp_id__in = emp_salry_structure,
            emp_id__enterprise=user.company).values_list("emp_id", flat=True)
            # .filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
            # Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
            #     Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id", flat=True)
        
        emp_list = Employee.objects.filter(id__in = emp_job_roll_list, enterprise=user.company)
        # .filter(
        #     Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True)).order_by("emp_number")
    return emp_list    





def check_from_to_employees(request,from_emp, to_emp,sal_obj):
    run_date = str(sal_obj.salary_year)+'-'+str(sal_obj.salary_month).zfill(2)+'-01'
    if len(from_emp) == 0: 
        from_emp = 0
        
    if len(to_emp) == 0: 
        to_emp = 0
    # error msg if not from or not to 
   
    if from_emp == 0 and to_emp != 0  or from_emp != 0 and to_emp == 0 :
        return False
   
    if from_emp == 0 and to_emp == 0 :
        employees = []
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,end_date__isnull=True).values_list("employee", flat=True)
           
        employees_list = Employee.objects.filter(id__in = emp_salry_structure , enterprise=request.user.company,emp_number__gte=from_emp,emp_number__lte=to_emp).filter(
            Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(
                Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True)).values_list("id",flat=True)
    
        last_year_employees = Employee.objects.filter(id__in=employees_list).filter(hiredate__year__lt=sal_obj.salary_year).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                Q(emp_end_date__isnull=True,terminationdate__isnull=True)).order_by("emp_number")
            
                
            
        salary_month_run_employees = Employee.objects.filter(id__in=employees_list).filter(
                    (Q(hiredate__month__lte=sal_obj.salary_month , hiredate__year=sal_obj.salary_year))).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                Q(emp_end_date__isnull=True,terminationdate__isnull=True))
            
        
        employees = last_year_employees | salary_month_run_employees
    return  employees   

   
@login_required(login_url='home:user-login')
def listSalaryView(request): 
    user_group = request.user.groups.all()[0].name 
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                    salary_structure__created_by = request.user, end_date__isnull=True).values_list("employee", flat=True)

        salary_list = Salary_elements.objects.filter(emp__in=emp_salry_structure,emp__enterprise=request.user.company).filter(
            (Q(end_date__gt=date.today()) | Q(end_date__isnull=True))).values('assignment_batch', 'salary_month',
                                                                          'salary_year', 'is_final').annotate(
                                            num_salaries=Count('salary_month')).order_by('salary_month', 'salary_year')         
    
    else:   
   
        salary_list = Salary_elements.objects.filter(emp__enterprise=request.user.company).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True))).values('assignment_batch', 'salary_month',
                                                                          'salary_year', 'is_final').annotate(
                                                            num_salaries=Count('salary_month')).order_by('salary_month', 'salary_year')
    
    
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


def set_context(request, create_payslip_context, month, sal_form, from_to_employees,emp_form):
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
            'emp_form': emp_form,
            'employees': employees,
            'employees_not_payroll_master': employees_not_payroll_master,
            'not_have_basic': not_have_basic,
            'from_to_employees' :from_to_employees
        }

    return context


@login_required(login_url='home:user-login')
def createSalaryView(request):
    sal_form = SalaryElementForm(user=request.user)
    emp_form = EmployeeForm()
    employees = 0
    not_have_basic = 0
    month = ''
    from_to_employees = get_employees_for_to_payroll(request.user)
    # context = {}
    create_payslip_context = None  # returned from create_payslip
    if request.method == 'POST':
        sal_form = SalaryElementForm(request.POST, user=request.user)
        if sal_form.is_valid():
            sal_obj = sal_form.save(commit=False)
            from_emp = request.POST.get('from_emp')    
            to_emp = request.POST.get('to_emp')
            employees_without_batch = check_from_to_employees(request, from_emp, to_emp, sal_obj)
            create_payslip_context = create_payslip(request, sal_obj,employees_without_batch, sal_form)
            month = sal_obj.salary_month
        else:  # Form was not valid
            messages.error(request, sal_form.errors)

    context = set_context(
        request=request, create_payslip_context=create_payslip_context, month=month, sal_form=sal_form, from_to_employees=from_to_employees,emp_form=emp_form)
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
            salary_month=month, salary_year=year, end_date__isnull=True,assignment_batch__isnull=True, emp__enterprise= request.user.company)
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


def deleteSalaryFromMonth(request, pk , month , year):
    salary = Salary_elements.objects.get(id=pk)
    employee = salary.emp
    employee_elements_history = Employee_Element_History.objects.filter(emp_id=employee,salary_month=month,salary_year=year)
    try:
        salary.delete()
        for element in employee_elements_history:
                element.delete()
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

    emp_elements_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year
                                                                   ).order_by('element_id__element_name')
    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='deduct',
                                                                      salary_month=month_number, salary_year=salary_year).order_by('element_id__element_name')
    
                                                                 
    
    # Not used on the html
    emp_payment = Payment.objects.filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)), emp_id=emp_id)

    
    
    monthSalaryContext = {
        'page_title': _('salary information for {}').format(salary_obj.emp),
        'salary_obj': salary_obj,
        'emp_elements_incomes': emp_elements_incomes,
        'emp_elements_deductions': emp_elements_deductions,
        'emp_payment': emp_payment,
        'batch_id': batch_id,
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
    emp_elements = Employee_Element.objects.filter(emp_id=emp_id)
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
        all_salary_obj = Salary_elements.objects.filter( salary_month=month, salary_year=year, emp__enterprise= request.user.company).filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))   #.values_list('emp', flat=True)
    else:
        all_salary_obj = Salary_elements.objects.filter(salary_month=month, salary_year=year, assignment_batch__id=batch, emp__enterprise= request.user.company).filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))  #.values_list('emp', flat=True)

    # emp_elements = Employee_Element.objects.filter(emp_id__in = all_salary_obj).order_by('emp_id').values_list('emp_id', flat=True)

    # employess = list(set(emp_elements))
    salary_elements =[]
    emps_salary_obj = []
    # for emp in employess:
    for emp in all_salary_obj:
        emp_salarys = Employee_Element_History.objects.filter(emp_id = emp.emp, salary_month = month, salary_year= year)
        if batch == 0:
            salary_obj = Salary_elements.objects.get( salary_month=month, salary_year=year, emp__enterprise= request.user.company, emp= emp.emp).filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        else:
            salary_obj = Salary_elements.objects.get( salary_month=month, salary_year=year,assignment_batch__id=batch, emp__enterprise= request.user.company, emp= emp.emp).filter(
                (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))

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
def delete_salary_view(request, month, year,batch_id):
    if batch_id == 0:
        required_salary_qs = Salary_elements.objects.filter(emp__enterprise=request.user.company,
                                                            salary_month=month, salary_year=year, assignment_batch__isnull=True)
        
        salary_history_element = Employee_Element_History.objects.filter(emp_id__in = required_salary_qs.values_list("emp",flat=True),emp_id__enterprise=request.user.company,
                                                                        salary_month=month, salary_year=year)
    
    else:
        required_salary_qs = Salary_elements.objects.filter(emp__enterprise=request.user.company,
                                                            salary_month=month, salary_year=year, assignment_batch=batch_id)
        salary_history_element = Employee_Element_History.objects.filter(emp_id__in = required_salary_qs.values_list("emp",flat=True),emp_id__enterprise=request.user.company,
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

    to_emp = request.GET.get('to_emp', None)
    from_emp = request.GET.get('from_emp', None)

    if assignment_batch == '':
        if from_emp != '' and to_emp != '':
            emp_list = Employee.objects.filter(enterprise=request.user.company,emp_number__gte=from_emp,emp_number__lte=to_emp).filter(
            Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))
        else :
            emp_list = Employee.objects.filter(enterprise=request.user.company).filter(
            Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))
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
    to_emp = request.GET.get('to_emp', None)
    from_emp = request.GET.get('from_emp', None)

    if assignment_batch == '':
        if from_emp != '' and to_emp != '':
            emp_list = Employee.objects.filter(enterprise=request.user.company,emp_number__gte=from_emp,emp_number__lte=to_emp).filter(
            Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))
        else :
            emp_list = Employee.objects.filter(enterprise=request.user.company).filter(
            Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))
        
        salary_to_create = Salary_elements(
            elements_type_to_run=elements_type_to_run,
            salary_month=int(salary_month),
            salary_year=int(salary_year))
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
    # if create_payslip(request, salary_to_create):
        # return JsonResponse({'true': True})
        # deleted = True
    # else:
        # return JsonResponse({'false': False})
    deleted = False
    return JsonResponse({'deleted': deleted})



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
                Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))).values('element_id')
    else:
        elements = Employee_Element.objects.filter(element_id=sal_obj.element,element_id__enterprise=user.company).filter(
            Q(start_date__lte=date.today()) & (
                (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))).values('element_id')
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
    by: bassant and gehad
    """
    # problem that onlt get that have structure link and didn't get warning message
    employees = 0
    run_date = str(sal_obj.salary_year)+'-'+str(sal_obj.salary_month).zfill(2)+'-01'
    if sal_obj.assignment_batch is not None:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                end_date__isnull=True).values_list("employee", flat=True)

        employees = Employee.objects.filter(enterprise=user.company,
            id__in=includeAssignmentEmployeeFunction(
                sal_obj.assignment_batch)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                sal_obj.assignment_batch)).filter(id__in=emp_salry_structure).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                Q(emp_end_date__isnull=True,terminationdate__isnull=True))
    else:
        user_group = request.user.groups.all()[0].name 
        if user_group == 'mena':
            emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
           
            last_year_employees = Employee.objects.filter(id__in=emp_salry_structure,enterprise=user.company).filter(hiredate__year__lt=sal_obj.salary_year).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                Q(emp_end_date__isnull=True,terminationdate__isnull=True)).order_by("emp_number")
            
            
            # problem that month 1 never bigger than 12 in secand condation 
            salary_month_run_employees = Employee.objects.filter(id__in=emp_salry_structure,enterprise=user.company).filter(
                        (Q(hiredate__month__lte=sal_obj.salary_month , hiredate__year=sal_obj.salary_year))).filter(Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                        Q(emp_end_date__isnull=True,terminationdate__isnull=True)).order_by("emp_number")
            
        else:
            emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,end_date__isnull=True).values_list("employee", flat=True)
           
            last_year_employees = Employee.objects.filter(id__in=emp_salry_structure,enterprise=user.company).filter(hiredate__year__lt=sal_obj.salary_year).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date)|
                Q(emp_end_date__isnull=True,terminationdate__isnull=True)).order_by("emp_number")


            salary_month_run_employees = Employee.objects.filter(id__in=emp_salry_structure,enterprise=user.company).filter(
                (Q(hiredate__month__lte=sal_obj.salary_month , hiredate__year=sal_obj.salary_year))).filter(
                Q(emp_end_date__gte=run_date ,terminationdate__gte=run_date) | 
                Q(emp_end_date__isnull=True,terminationdate__isnull=True)).order_by("emp_number")
            
        employees = last_year_employees | salary_month_run_employees # union operator for queryset 
        
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
    by: gehad
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
        attribute1 = salary_calc.calc_attribute1(),
        final_net_salary = salary_calc.calc_final_net_salary(),
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


def create_payslip(request, sal_obj,employees_without_batch, sal_form=None):
    element = sal_obj.element if sal_obj.element else None

    # get elements for all employees.
    elements = get_elements(request.user,sal_obj)

    if employees_without_batch == False:
        message_error = "please enter from employee to employee "
        messages.error(request, message_error)
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': 0,  # to not to show employees structure link error
            'employees_not_payroll_master': 0,
            'from_to_employees' :get_employees_for_to_payroll(request.user)
        }
        return create_context
    else :
        if len(employees_without_batch) != 0:
            employees = employees_without_batch

        else:    
            employees = get_employees(request.user,sal_obj, request)
    
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
        print("************", )
        try:
            for employee in employees:
                try:
                    job_id = JobRoll.objects.get(emp_id=employee, end_date__isnull=True)
                except JobRoll.DoesNotExist:  
                    jobs = JobRoll.objects.filter(emp_id=employee).order_by('end_date')
                    job_id = jobs.first()

                             

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
    user_group = request.user.groups.all()[0].name 
    salary_form = SalaryElementForm(user=request.user)
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        employess = Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number") 
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        
        employess =Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
                
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
    user_group = request.user.groups.all()[0].name 
    emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                    salary_structure__created_by = request.user, end_date__isnull=True).values_list("employee", flat=True)

    if from_month != 0 and to_month != 0 and from_emp != 0 and to_emp != 0 :
        if user_group == 'mena':
            employees_information = Salary_elements.objects.filter(emp__in=emp_salry_structure,salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp,emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")
        else:
            employees_information = Salary_elements.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                    emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp,emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")

    if from_emp == 0 and to_emp == 0 :
        if from_month != 0 and to_month != 0 :
            if user_group == 'mena':
                 employees_information = Salary_elements.objects.filter(emp__in=emp_salry_structure,salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                        emp__enterprise=request.user.company).values(
                        'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")

            else: 
                employees_information = Salary_elements.objects.filter(salary_month__gte=from_month,salary_month__lte=to_month ,salary_year=year,
                        emp__enterprise=request.user.company).values(
                        'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("salary_month")
        else:
            message_error = "please enter from month to month or from employee to employee"
            messages.error(request, message_error)
            return redirect('payroll_run:creat-report')

    if from_month == 0 and to_month == 0 :
        if from_emp != 0 and to_emp != 0 :
            if user_group == 'mena':
                employees_information = Salary_elements.objects.filter(emp__in=emp_salry_structure,salary_year=year,
                    emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp,emp__enterprise=request.user.company).values(
                    'emp__emp_number', 'emp__emp_name', 'incomes', 'insurance_amount', 'tax_amount', 'deductions', 'gross_salary', 'net_salary', 'emp').order_by("emp__emp_number")

            else:    
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
    jobroll = JobRoll.objects.filter(emp_id=emp_id).filter(
        Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by("end_date").last()

    payment = Payment.objects.filter(
            emp_id=emp_id).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by("end_date").last()
  
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
                                                                   salary_month=month_number, salary_year=salary_year
                                                                   ).exclude(element_id__is_basic=True).order_by('element_id__sequence')
                                                                
    try:
        basic = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__is_basic=True)
    except Employee_Element_History.DoesNotExist:
        basic = 0.0
    
    try:
        other_allowances = Employee_Element_History.objects.get(element_id__in=elements,
                                                                   emp_id=emp_id,
                                                                   element_id__classification__code='earn',
                                                                   salary_month=month_number, salary_year=salary_year,
                                                                   element_id__element_name='Other Allowances')
    except Employee_Element_History.DoesNotExist:
        other_allowances = 0.0

    
    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                                      element_id__classification__code='deduct',
                                                                      salary_month=month_number, salary_year=salary_year
                                                                      ).order_by('element_id__sequence')
    net_in_arabic = num2words(round(salary_obj.net_salary, 2),lang='ar')

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
        emp_total_deductions= total_deductions[0] + insurance_amount + salary_obj.tax_amount 
    except :
        emp_total_deductions = insurance_amount

    gross = salary_obj.gross_salary 
    # else:
    #     try:
    #         total_deductions[0]
    #         emp_total_deductions= total_deductions[0]  + insurance_amount
    #     except :
    #         emp_total_deductions = insurance_amount

    #     gross = salary_obj.gross_salary
    
    
    context = {
        'company_name': request.user.company,
        'page_title': _('salary information for {}').format(salary_obj.emp),
        'salary_obj': salary_obj,
        'emp_elements_incomes': emp_elements_incomes,
        'emp_elements_deductions': emp_elements_deductions,
        'emp_payment': emp_payment,
        'batch_id': batch_id,
        'emp_total_incomes': emp_total_incomes,
        'emp_total_deductions': emp_total_deductions,
        'insurance_amount': insurance_amount,
        'gross': gross,
        'jobroll':jobroll,
        'payment':payment,
        'basic':basic,
        'other_allowances':other_allowances,
        'net_in_arabic':net_in_arabic,
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
def departments_payslip(request,month_number,salary_year):
    departments = Department.objects.all().filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')          
    if request.method == 'POST': 
        dep_name= request.POST.get('dep_id')
        dep_id =Department.objects.filter(dept_name=dep_name).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).last().id
        return redirect('payroll_run:print-department-payslip',dep_id=dep_id,month = month_number,year = salary_year)
    myContext = {
        'departments':departments,
    }
    return render(request, 'departments_payslip.html', myContext)




def print_departments_report(request,dep_id,month,year):
    template_path = 'all-payslip.html'

    emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,end_date__isnull=True).values_list("employee", flat=True)
    emp_job_roll_list = JobRoll.objects.filter(emp_id__in = emp_salry_structure,
            emp_id__enterprise=request.user.company,position__department=dep_id).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
                Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                    Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)
        
    all_salary_obj = Salary_elements.objects.filter(salary_month=month, salary_year=year,emp__in= emp_job_roll_list ,emp__enterprise= request.user.company).filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True))) 

    salary_elements =[]
    emps_salary_obj = []
    # for emp in employess:
    for emp in all_salary_obj:
        emp_salarys = Employee_Element_History.objects.filter(emp_id = emp.emp, salary_month = month, salary_year= year)
        salary_obj = Salary_elements.objects.get( salary_month=month, salary_year=year, emp__enterprise= request.user.company, emp= emp.emp)
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
def get_month_year_employee_company_insurance_report(request):
    salary_form = SalaryElementForm(user=request.user)
    user_group = request.user.groups.all()[0].name 
   
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                    salary_structure__created_by = request.user, end_date__isnull=True).values_list("employee", flat=True)
    
        employess =Employee.objects.filter(id__in =emp_salry_structure ,enterprise=request.user.company).order_by("emp_number")
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")

    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
             end_date__isnull=True).values_list("employee", flat=True)
    
        employess =Employee.objects.filter(id__in =emp_salry_structure,enterprise=request.user.company).order_by("emp_number")
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
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









########################################### Monthely Salary Reports ##########################################
@login_required(login_url='home:user-login')
def monthly_salary_report(request):
    user_group = request.user.groups.all()[0].name 
    salary_form = SalaryElementForm(user=request.user)
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        
        employess = Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number") 
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                end_date__isnull=True).values_list("employee", flat=True)
        
        employess =Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
    
    departments = Department.objects.all().filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')          
    
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
            to_month=strptime(to_month,'%b').tm_mon 

        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
            
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
        
        
        dep_id = request.POST.get('dep_id')
        if len(dep_id) == 0: 
            dep_id = 0
        else:
            dep_id =Department.objects.filter(dept_name=dep_id ).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).last().id

        return redirect('payroll_run:monthly-salary-report',
            from_month=from_month,to_month=to_month,year=year,from_emp =from_emp,to_emp=to_emp ,dep_id=dep_id)

    myContext = {
        "salary_form": salary_form,
        "employess":employess,
        'departments':departments,
    }
    return render(request, 'monthly_salary_report_parameters.html', myContext)







@login_required(login_url='home:user-login')
def export_monthly_salary_report(request,from_month ,to_month, year,from_emp,to_emp,dep_id):
    if from_emp != 0 and to_emp != 0 and dep_id != 0:
        emp_job_roll_list = JobRoll.objects.filter(
            emp_id__enterprise=request.user.company,position__department=dep_id ).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
            Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)
        
        monthly_salary_employees = Employee.objects.filter(id__in = emp_job_roll_list).filter(emp_number__gte=from_emp,emp_number__lte=to_emp)
 
    elif from_emp == 0 and to_emp == 0  and  dep_id != 0:
        emp_job_roll_list = JobRoll.objects.filter(
            emp_id__enterprise=request.user.company,position__department=dep_id ).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
                Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                    Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)
        
      
        monthly_salary_employees = Employee.objects.filter(id__in = emp_job_roll_list)
        

    elif from_emp != 0 and to_emp != 0 and  dep_id == 0:        
        monthly_salary_employees = Employee.objects.filter(enterprise=request.user.company).filter(
                    Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(
                        Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True)).filter(emp_number__gte=from_emp,
                            emp_number__lte=to_emp)

    else:
        monthly_salary_employees = Employee.objects.filter(enterprise=request.user.company).filter(
                    Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True)).filter(
                        Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))                   

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Monthly Salary Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Monthly Salary Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True
    earning_elements__salary_structure = list(StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company,element__classification__code='earn').exclude(
        element__is_basic=True).filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by("element__sequence").values_list("element__element_name",flat=True))
    earning_unique_elements = set(earning_elements__salary_structure)

    deduct_elements__salary_structure = list(StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company,element__classification__code='deduct').filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by("element").values_list("element__element_name",flat=True))
    deduct_unique_elements = set(deduct_elements__salary_structure )
    
    
    columns = [ 'Person Code','Person Number','Date of Hire','Date of Resignation','Insurance No.',
    'National ID','Position','Location','Department','Division', 'Total Baisc Salary','Basic salary	','Basic salary increase','Total earnings', 'Tax','Emp Insurance',
    'Total Deduction',' Net Salary','Alimony','Company Insurance','Insurance Salary','Insurance Salary Retirement']

    columns[13:13] = earning_unique_elements
    total_earning_index = columns.index('Total Deduction')
    columns[total_earning_index:total_earning_index] = deduct_unique_elements

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    # monthes_list = list(range(from_month, to_month+1)) 
    for emp in monthly_salary_employees:
        try:
            jobroll_obj = JobRoll.objects.filter(emp_id=emp.id).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
            jobroll = jobroll_obj.first()
        except JobRoll.DoesNotExist:
            jobroll = 0
        # for month in monthes_list:
        try:
            salary_element = Salary_elements.objects.filter(emp=emp,salary_month__gte=from_month , salary_month__lte=to_month , salary_year=year)
            emp_dic = []
            emp_dic.append(emp.emp_number)
            emp_dic.append(emp.emp_name)
            emp_dic.append(emp.hiredate)
            emp_dic.append(emp.terminationdate)
            emp_dic.append(emp.insurance_number)
            if emp.id_number:
                id_number = emp.id_number
            else : 
                id_number = ''           
            emp_dic.append(id_number) 
            if  jobroll is not None and jobroll != 0 :
                if jobroll.position.position_name:
                    emp_dic.append(jobroll.position.position_name)
                else:
                    emp_dic.append('')    
            emp_dic.append('')
            if jobroll is not None and jobroll != 0 :
                if jobroll.position.department.dept_name:
                    emp_dic.append(jobroll.position.department.dept_name)
                else:
                    emp_dic.append('') 
            emp_dic.append('')
            try:
                employee_element = Employee_Element_History.objects.filter(emp_id=emp,
                    salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum'] 
                employee_element_value = employee_element  
            except Employee_Element_History.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value)
            
            try:
                employee_element = Employee_Element_History.objects.filter(emp_id=emp,
                    salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, element_id__element_name='Basic salary').aggregate(Sum('element_value'))['element_value__sum'] 
                employee_element_value = employee_element  
            except Employee_Element_History.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value)

            try:
                employee_element = Employee_Element_History.objects.filter(emp_id=emp,
                    salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, element_id__element_name='Basic salary increase').aggregate(Sum('element_value'))['element_value__sum'] 
                employee_element_value = employee_element  
            except Employee_Element_History.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value)
            

            
            for element in earning_unique_elements:
                try:
                    employee_element = Employee_Element_History.objects.filter(emp_id=emp,
                                salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum'] 
                    employee_element_value =employee_element  
                except Employee_Element_History.DoesNotExist:
                    employee_element_value = 0.0
                emp_dic.append(employee_element_value)  
            emp_dic.append(salary_element.aggregate(Sum('incomes'))['incomes__sum'])
            emp_dic.append(salary_element.aggregate(Sum('tax_amount'))['tax_amount__sum'])
            emp_dic.append(salary_element.aggregate(Sum('insurance_amount'))['insurance_amount__sum'])
            for element in deduct_unique_elements:
                try:
                    employee_element = Employee_Element_History.objects.filter(emp_id=emp,
                                salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum'] 
                    employee_element_value =employee_element
                except Employee_Element_History.DoesNotExist:
                    employee_element= 0.0        
                emp_dic.append(employee_element_value) 
            emp_dic.append(salary_element.aggregate(Sum('deductions'))['deductions__sum'])
            emp_dic.append(salary_element.aggregate(Sum('net_salary'))['net_salary__sum'])
            try:
                employee_element = Employee_Element_History.objects.filter(emp_id=emp,salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year, 
                        element_id__element_name='Alimony').aggregate(Sum('element_value'))['element_value__sum']
                alimony_element =employee_element 
            except Employee_Element_History.DoesNotExist:
                    alimony_element = 0.0
            emp_dic.append(alimony_element)  
            emp_dic.append(salary_element.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'])
            emp_dic.append(emp.insurance_salary)
            emp_dic.append(emp.retirement_insurance_salary)
            emp_list.append(emp_dic)
        except Salary_elements.DoesNotExist:
            pass   
    
    emp_dic = []
    #   columns = [ 'Person Code','Person Number','Date of Hire','Date of Resignation','Insurance No.',
    # 'National ID','Position','Location','Department','Division', 'Total Baisc Salary','Basic salary	','Basic salary increase','Total earnings', 'Tax','Emp Insurance',
    # 'Total Deduction',' Net Salary','Alimony','Company Insurance','Insurance Salary','Insurance Salary Retirement']
    employees_elements = Employee_Element_History.objects.filter(emp_id__in=monthly_salary_employees,salary_month__gte= from_month, salary_month__lte= to_month,salary_year=year)
    salary_elements = Salary_elements.objects.filter(emp__in=monthly_salary_employees,salary_month__gte=from_month , salary_month__lte=to_month , salary_year=year)

    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    employee_element =employees_elements.filter(element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum'] 
    emp_dic.append(employee_element)
    
    employee_element =employees_elements.filter( element_id__element_name='Basic salary').aggregate(Sum('element_value'))['element_value__sum'] 
    emp_dic.append(employee_element)
    
    employee_element =employees_elements.filter(element_id__element_name='Basic salary increase').aggregate(Sum('element_value'))['element_value__sum'] 
    emp_dic.append(employee_element)
    for element in earning_unique_elements:
        employee_element = employees_elements.filter( element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum'] 
        emp_dic.append(employee_element)
   
    emp_dic.append(salary_elements.aggregate(Sum('incomes'))['incomes__sum'])
    emp_dic.append(salary_elements.aggregate(Sum('tax_amount'))['tax_amount__sum'])
    emp_dic.append(salary_elements.aggregate(Sum('insurance_amount'))['insurance_amount__sum'])
   
    for element in deduct_unique_elements:
        employee_element = employees_elements.filter( element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum'] 
        emp_dic.append(employee_element)
                     
    emp_dic.append(salary_elements.aggregate(Sum('deductions'))['deductions__sum'])
    emp_dic.append(salary_elements.aggregate(Sum('net_salary'))['net_salary__sum'])
    employee_element = employees_elements.filter(element_id__element_name='Alimony').aggregate(Sum('element_value'))['element_value__sum'] 
    emp_dic.append(employee_element)
    
    emp_dic.append(salary_elements.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'])
    emp_dic.append(monthly_salary_employees.aggregate(Sum('insurance_salary'))['insurance_salary__sum'])
    emp_dic.append(monthly_salary_employees.aggregate(Sum('retirement_insurance_salary'))['retirement_insurance_salary__sum'])
    emp_list.append(emp_dic)    

    
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response






########################################### Monthely Cost Center Salary Reports ##########################################
@login_required(login_url='home:user-login')
def cost_center_monthly_salary_report(request):
    user_group = request.user.groups.all()[0].name 
    salary_form = SalaryElementForm(user=request.user)
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        employess = Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number") 
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                        end_date__isnull=True).values_list("employee", flat=True)
        employess =Employee.objects.filter(enterprise=request.user.company).order_by("emp_number")
        
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
    
    departments = Department.objects.all().filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')          
    
    if request.method == 'POST':
        year = request.POST.get('salary_year',None)

        from_month_in_words = request.POST.get('from_month')
        from_month=strptime(from_month_in_words,'%b').tm_mon 
        
        to_month_in_words = request.POST.get('to_month')
        to_month=strptime(to_month_in_words,'%b').tm_mon 

        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
            
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
        
        
        dep_id = request.POST.get('dep_id')
        if len(dep_id) == 0:
            dep_id = 0
        else:
            dep_id =Department.objects.filter(dept_name=dep_id ).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).last().id
        return redirect('payroll_run:cost-center-monthly-salary-report',
            from_month=from_month,to_month=to_month,year=year,from_emp =from_emp,to_emp=to_emp ,dep_id=dep_id)

    myContext = {
        "salary_form": salary_form,
        "employess":employess,
        'departments':departments,
    }
    return render(request, 'cost_center_monthly_salary_report_parameters.html', myContext)







@login_required(login_url='home:user-login')
def export_cost_center_monthly_salary_report(request,from_month ,to_month, year,from_emp,to_emp,dep_id):
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

    deduct_elements__salary_structure = list(StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company,element__classification__code='deduct').filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by("element").values_list("element__element_name",flat=True))
    deduct_unique_elements = set(deduct_elements__salary_structure )
    
    
    columns = [' ','Head count','Total Baisc Salary','Basic salary','Basic salary increase', 'Total earnings', 'Tax','Emp Insurance',
                'Total Deduction',' Net Salary','Alimony','Company Insurance','Insurance Salary','Insurance Salary Retirement']

    columns[5:5] = earning_unique_elements
    total_earning_index = columns.index('Total Deduction')
    columns[total_earning_index:total_earning_index] = deduct_unique_elements

    
    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    # monthes_list = list(range(from_month, to_month+1))
    if dep_id == 0 :
        if from_emp == 0 and to_emp == 0:
            emp_job_roll_query = JobRoll.objects.filter(
                        emp_id__enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
                            Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)) 
        else:
            emp_job_roll_query = JobRoll.objects.filter(
                        emp_id__enterprise=request.user.company,emp_id__emp_number__gte=from_emp,emp_id__emp_number__lte=to_emp).filter(
                            Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
                            Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True))  
        dept_list = Department.objects.all().filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')
        # for month in monthes_list:
        for dep in dept_list:
            emp_job_roll_list = emp_job_roll_query.filter(position__department=dep).values_list("emp_id",flat=True)
            # emp_job_roll_query.filter(position__department=dep).filter(
            #     Q(end_date__month__gte=date.today().month)| Q(end_date__isnull=True)).filter(
            #     Q(emp_end_date__month__gte=date.today().month,terminationdate__month__gte=date.today().month) | 
            #     Q(emp_end_date__isnull=True,terminationdate__isnull=True)).values_list("emp_id",flat=True)     
            
            emps_ids = set(emp_job_roll_list) 
            
            employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)
            salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)
            employees_query = Employee.objects.filter(id__in=emps_ids)

                
            total_earnings = salary_elements_query.aggregate(Sum('incomes'))['incomes__sum'] 
            total_deductions= salary_elements_query.aggregate(Sum('deductions'))['deductions__sum']                 
            taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
            insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum'] 
            net= salary_elements_query.aggregate(Sum('net_salary'))['net_salary__sum']  
            
            company_insurance= salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'] 
            insurance_salary= employees_query.aggregate(Sum('insurance_salary'))['insurance_salary__sum'] 
            insurance_salary_retirement= employees_query.aggregate(Sum('retirement_insurance_salary'))['retirement_insurance_salary__sum']                                        


            emp_dic = []
            emp_dic.append(dep.dept_name)
            emp_dic.append(len(emps_ids))
            sum_of_basic = employees_elements_query.filter(element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_basic) 
            
            sum_of_basic_salary = employees_elements_query.filter(element_id__element_name='Basic salary').aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_basic_salary) 
            
            sum_of_basic_salary_increase = employees_elements_query.filter(element_id__element_name='Basic salary increase').aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_basic_salary_increase) 

            
            for element in earning_unique_elements:
                sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
                emp_dic.append(sum_of_element)  
            emp_dic.append(total_earnings)   
            emp_dic.append(taxs) 
            emp_dic.append(insurance_amount) 
            for element in deduct_unique_elements:
                sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
                emp_dic.append(sum_of_element) 
            emp_dic.append(total_deductions)   
            emp_dic.append(net)
            emp_dic.append(employees_elements_query.filter(element_id__element_name='Alimony').aggregate(Sum('element_value'))['element_value__sum'])
            emp_dic.append(company_insurance)
            emp_dic.append(insurance_salary)
            emp_dic.append(insurance_salary_retirement)
            emp_list.append(emp_dic) 
# ---------------------------------------------------------------
        emp_dic = []
        emp_job_roll_list = emp_job_roll_query.filter(position__department__in=dept_list).values_list("emp_id",flat=True)
        emps_ids = set(emp_job_roll_list) 
        employees_query = Employee.objects.filter(id__in=emps_ids)
        total_employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)
        total_salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)

        emp_dic.append("")
        emp_dic.append("")
        sum_of_basic = total_employees_elements_query.filter(element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum']
        emp_dic.append(sum_of_basic) 
        
        sum_of_basic_salary = total_employees_elements_query.filter(element_id__element_name='Basic salary').aggregate(Sum('element_value'))['element_value__sum']
        emp_dic.append(sum_of_basic_salary) 
        
        sum_of_basic_salary_increase = total_employees_elements_query.filter(element_id__element_name='Basic salary increase').aggregate(Sum('element_value'))['element_value__sum']
        emp_dic.append(sum_of_basic_salary_increase) 

        for element in earning_unique_elements:
            sum_of_element = total_employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_element)  
        emp_dic.append(total_salary_elements_query.aggregate(Sum('incomes'))['incomes__sum'] )   
        emp_dic.append(total_salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  ) 
        emp_dic.append(total_salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum'] ) 
        for element in deduct_unique_elements:
            sum_of_element = total_employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_element) 
        emp_dic.append(total_salary_elements_query.aggregate(Sum('deductions'))['deductions__sum']                 )   
        emp_dic.append(total_salary_elements_query.aggregate(Sum('net_salary'))['net_salary__sum']  )
        emp_dic.append(employees_elements_query.filter(element_id__element_name='Alimony').aggregate(Sum('element_value'))['element_value__sum'])
        emp_dic.append(total_salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'] )
        emp_dic.append(employees_query.aggregate(Sum('insurance_salary'))['insurance_salary__sum'] )
        emp_dic.append(employees_query.aggregate(Sum('retirement_insurance_salary'))['retirement_insurance_salary__sum'])
        emp_list.append(emp_dic)     
    else:
        if from_emp == 0 and to_emp == 0 :
            emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=request.user.company,position__department=dep_id ).filter(
                            Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
                            Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)) 

        else:    
            emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=request.user.company,position__department=dep_id ,emp_id__emp_number__gte=from_emp,emp_id__emp_number__lte=to_emp).filter(
                Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).filter(
                Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                    Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True))
            
        
        # for month in monthes_list:
        emp_job_roll_list = emp_job_roll_query.values_list("emp_id",flat=True)   
        emps_ids = set(emp_job_roll_list) 
        
        employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)
        salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month__gte= from_month,salary_month__lte=to_month,salary_year=year)
        employees_list = employees_elements_query.values_list("emp_id", flat=True)
        employees_query= Employee.objects.filter(id__in=employees_list)

            
        total_earnings = salary_elements_query.aggregate(Sum('incomes'))['incomes__sum'] 
        total_deductions= salary_elements_query.aggregate(Sum('deductions'))['deductions__sum']                 
        taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
        insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum'] 
        net= salary_elements_query.aggregate(Sum('net_salary'))['net_salary__sum']  
        
        company_insurance= salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum'] 
        insurance_salary= employees_query.aggregate(Sum('insurance_salary'))['insurance_salary__sum'] 
        insurance_salary_retirement= employees_query.aggregate(Sum('retirement_insurance_salary'))['retirement_insurance_salary__sum']                                        


        emp_dic = []
        emp_dic.append(Department.objects.get(id=dep_id).dept_name)
        emp_dic.append(len(emps_ids))
        sum_of_basic = employees_elements_query.filter(element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum']
        emp_dic.append(sum_of_basic) 
        for element in earning_unique_elements:
            sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_element)  
        emp_dic.append(total_earnings)   
        emp_dic.append(taxs) 
        emp_dic.append(insurance_amount) 
        for element in deduct_unique_elements:
            sum_of_element = employees_elements_query.filter(element_id__element_name=element).aggregate(Sum('element_value'))['element_value__sum']
            emp_dic.append(sum_of_element) 
        emp_dic.append(total_deductions)   
        emp_dic.append(net)
        emp_dic.append(employees_elements_query.filter(element_id__element_name='Alimony').aggregate(Sum('element_value'))['element_value__sum'])
        emp_dic.append(company_insurance)
        emp_dic.append(insurance_salary)
        emp_dic.append(insurance_salary_retirement)
        emp_list.append(emp_dic) 

    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response







########################################### Monthely Entery Salary Reports ##########################################
@login_required(login_url='home:user-login')
def entery_monthly_salary_report(request):
    user_group = request.user.groups.all()[0].name 
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        
        employess = Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).order_by("emp_number") 
        
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number") 
    else:
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                end_date__isnull=True).values_list("employee", flat=True)
        
        employess =Employee.objects.filter(enterprise=request.user.company).order_by("emp_number")
        
        
        # .filter(
        #     (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")
    
    
    departments = Department.objects.all().filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).order_by('tree_id')          
    
    if request.method == 'POST': 
        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
            
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
        
        
        dep_id = request.POST.get('dep_id')
        if len(dep_id) == 0: 
            dep_id = 0
        else:
            dep_id =Department.objects.filter(dept_name=dep_id ).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True)).last().id
        return redirect('payroll_run:entery-monthly-salary-report',from_emp =from_emp,to_emp=to_emp ,dep_id=dep_id)

    myContext = {
        "employess":employess,
        'departments':departments,
    }
    return render(request, 'entery_monthly_salary_report_parameters.html', myContext)









@login_required(login_url='home:user-login')
def export_entery_monthly_salary_report(request,from_emp,to_emp,dep_id):
    if from_emp != 0 and to_emp != 0 and dep_id != 0:
        emp_job_roll_list = JobRoll.objects.filter(
            emp_id__enterprise=request.user.company,position__department=dep_id ).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
            Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)
    
        employees = Employee.objects.filter(id__in = emp_job_roll_list).filter(emp_number__gte=from_emp,emp_number__lte=to_emp)
 
    elif from_emp == 0 and to_emp == 0  and  dep_id != 0:
        emp_job_roll_list = JobRoll.objects.filter(
            emp_id__enterprise=request.user.company,position__department=dep_id).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
                Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                    Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)
        
        employees = Employee.objects.filter(id__in = emp_job_roll_list)
        

    elif from_emp != 0 and to_emp != 0 and  dep_id == 0:        
        employees = Employee.objects.filter(enterprise=request.user.company).filter(
                    Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).filter(
                        Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True)).filter(emp_number__gte=from_emp,
                            emp_number__lte=to_emp)

    else:
        employees = Employee.objects.filter(enterprise=request.user.company).filter(
                    Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True)).filter(
                        Q(terminationdate__gte=date.today())|Q(terminationdate__isnull=True))                   

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Entery Monthly Salary Report.xls"'
    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Entery Monthly Salary Report')
    row_num = 0
    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    structure_element = StructureElementLink.objects.filter(salary_structure__enterprise =request.user.company).filter(
        Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
    
    earning_elements__salary_structure = list(structure_element.filter(element__classification__code='earn').exclude(
        element__is_basic=True).order_by("element__sequence").values_list("element__element_name",flat=True))
    earning_unique_elements = set(earning_elements__salary_structure)

    deduct_elements__salary_structure = list(structure_element.filter(element__classification__code='deduct').order_by("element__sequence").values_list("element__element_name",flat=True))
    deduct_unique_elements = set(deduct_elements__salary_structure )
    
    info_elements__salary_structure = list(structure_element.exclude(element__classification__code='deduct').exclude(element__classification__code='earn').order_by("element__sequence").values_list("element__element_name",flat=True))
    info_unique_elements = set(info_elements__salary_structure )
    columns = [ 'Person Code','Person Number','Date of Hire','Date of Resignation','Insurance No.',
    'National ID','Position','Location','Department','Division', 'Total Baisc Salary','Alimony','Insurance Salary','Insurance Salary Retirement']

    columns[11:11] = earning_unique_elements
    columns[11:11] = info_unique_elements 
    total_earning_index = columns.index('Alimony')
    columns[total_earning_index:total_earning_index] = deduct_unique_elements


    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    for emp in employees:
        try:
            jobroll_obj = JobRoll.objects.filter(emp_id=emp).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
            jobroll = jobroll_obj.first()
        except JobRoll.DoesNotExist:
            jobroll= 0
        emp_dic = []
        emp_dic.append(emp.emp_number)
        emp_dic.append(emp.emp_name)
        emp_dic.append(emp.hiredate)
        emp_dic.append(emp.terminationdate)
        emp_dic.append(emp.insurance_number)
        if emp.id_number:
            id_number = emp.id_number
        else : 
            id_number = ''           
        emp_dic.append(id_number) 
        if jobroll is not None and jobroll != 0 :
            if jobroll.position.position_name:
                emp_dic.append(jobroll.position.position_name)
            else:
                emp_dic.append('')  
        emp_dic.append('')
        if jobroll is not None and jobroll != 0 :
            if jobroll.position.department.dept_name:
                emp_dic.append(jobroll.position.department.dept_name)
            else:
                emp_dic.append('')
        emp_dic.append('')
        try:
            basic_element = Employee_Element.objects.get(emp_id=emp, element_id__is_basic=True)
            employee_element_value =basic_element.element_value    
        except Employee_Element.DoesNotExist:
            employee_element_value  = 0.0
        emp_dic.append(employee_element_value) 
        for element in info_unique_elements :
            try:
                employee_element = Employee_Element.objects.get(emp_id=emp, element_id__element_name= element)
                employee_element_value =employee_element.element_value    
            except Employee_Element.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value) 
        for element in earning_unique_elements:
            try:
                employee_element = Employee_Element.objects.get(emp_id=emp, element_id__element_name= element)
                employee_element_value =employee_element.element_value    
            except Employee_Element.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value)  
        for element in deduct_unique_elements:
            try:
                employee_element = Employee_Element.objects.get(emp_id=emp, element_id__element_name= element)
                employee_element_value =employee_element.element_value    
            except Employee_Element.DoesNotExist:
                employee_element_value = 0.0
            emp_dic.append(employee_element_value) 
        try:
            employee_element = Employee_Element.objects.get(emp_id=emp, element_id__element_name='Alimony')
            alimony_element =employee_element.element_value    
        except Employee_Element.DoesNotExist:
                alimony_element = 0.0
        emp_dic.append(alimony_element)
        emp_dic.append(emp.insurance_salary)
        emp_dic.append(emp.retirement_insurance_salary)
        emp_list.append(emp_dic)
    #----------------------------------------------------------------
    emp_dic = []
    emp_dic.append("")
    emp_dic.append("")
    emp_dic.append("")
    emp_dic.append("")
    emp_dic.append("")        
    emp_dic.append("") 
    emp_dic.append('')  
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append('')
    emp_dic.append(Employee_Element.objects.filter(emp_id__in=employees, element_id__is_basic=True).aggregate(Sum('element_value'))['element_value__sum'])
    for element in info_unique_elements :
        emp_dic.append(Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name= element).aggregate(Sum('element_value'))['element_value__sum'] ) 
    for element in earning_unique_elements:
        emp_dic.append(Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name= element).aggregate(Sum('element_value'))['element_value__sum'] ) 
    for element in deduct_unique_elements:
        emp_dic.append(Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name= element).aggregate(Sum('element_value'))['element_value__sum'] ) 
    emp_dic.append(Employee_Element.objects.filter(emp_id__in = employees, element_id__element_name= 'Alimony').aggregate(Sum('element_value'))['element_value__sum'] ) 
    emp_dic.append(employees.aggregate(Sum('insurance_salary'))['insurance_salary__sum'] ) 
    emp_dic.append(employees.aggregate(Sum('retirement_insurance_salary'))['retirement_insurance_salary__sum'] )
    emp_list.append(emp_dic)
    print("&&&", emp_dic)
    
    
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response
############################################################################################################
 # calculate annyal tax amount   
def annual_tax(request, emp_id ):
    required_employee = Employee.objects.get(id=emp_id)
    tax_rule_master = Payroll_Master.objects.get(enterprise=required_employee.enterprise , end_date__isnull = True)
    
    personal_exemption = tax_rule_master.tax_rule.personal_exemption
    round_to_10 = tax_rule_master.tax_rule.round_down_to_nearest_10
    # initiat the tax class here 
    tax_deduction_obj = Tax_Settlement_Deduction_Amount(personal_exemption, round_to_10)
    
    salary_element = Salary_elements.objects.filter(emp=9946, salary_year=2021)
    gross_salary = salary_element.aggregate(Sum('gross_salary'))['gross_salary__sum'] 
    insurance = salary_element.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
    emp_deductions = Employee_Element_History.objects.filter(
        element_id__classification__code='deduct',element_id__tax_flag= True, salary_year=2021,emp_id=9946).aggregate(
            Sum('element_value'))['element_value__sum']
    
    
    taxable_salary = gross_salary- emp_deductions
    # taxxxxxxx 43410.061
    taxes = tax_deduction_obj.run_tax_calc(taxable_salary, insurance) 
    # taxxxxxxx222222 40737.061

    annual_tax = salary_element.aggregate(Sum('tax_amount'))['tax_amount__sum']
    # difffirance 548.71 ,  5737.07
    return round(taxes, 2) 

