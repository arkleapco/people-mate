from django.http import HttpResponse
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.views.generic import DetailView, ListView, View
from django.contrib import messages
from django.template.loader import get_template
from django.contrib.auth.decorators import login_required
from datetime import date
from django.utils.translation import to_locale, get_language
from django.db.models import Q
import calendar
from django.db import IntegrityError
from django.db.models import Avg, Count
from payroll_run.models import Salary_elements
from payroll_run.forms import SalaryElementForm, Salary_Element_Inline
from element_definition.models import Element_Master, Element_Batch, Element_Batch_Master, Element, SalaryStructure
from manage_payroll.models import Assignment_Batch, Assignment_Batch_Include, Assignment_Batch_Exclude
from employee.models import Employee_Element, Employee, JobRoll, Payment, EmployeeStructureLink, \
    Employee_Element_History
from leave.models import EmployeeAbsence
from employee.forms import Employee_Element_Inline
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


@login_required(login_url='home:user-login')
def listSalaryView(request):
    salary_list = Salary_elements.objects.filter(
        (Q(end_date__gt=date.today()) | Q(end_date__isnull=True))).values('assignment_batch', 'salary_month',
                                                                          'salary_year', 'is_final').annotate(
        num_salaries=Count('salary_month'))
    batches = Assignment_Batch.objects.all()   
    print("kkkkkkkkkkkkkkk",salary_list)    
    salaryContext = {
        "page_title": _("salary list"),
        "salary_list": salary_list,
        "batches":batches,
    }
    print(salary_list)
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
    if create_payslip_context is not None:
        # if no errors found and payroll ran
        if create_payslip_context == {}:
            success_msg = _('Payroll for month {} done successfully').format(
                calendar.month_name[month])
            messages.success(request, success_msg)
            # return redirect('payroll_run:list-salary')
        # there are errors in structure link or basic has no value
        # context = create_payslip_context
        else:
            context = create_payslip_context
            context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': 0,
            'not_have_basic': 0,
        }
    else:
        context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': employees,
            'not_have_basic': not_have_basic,
        }
    context = {
        'page_title': _('create salary'),
        'sal_form': sal_form,
        'employees': 0,
        'not_have_basic': 0,
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
        print("kkkkkkkkkkkkk")
        sal_form = SalaryElementForm(request.POST, user=request.user)
        if sal_form.is_valid():
            sal_obj = sal_form.save(commit=False)
            create_payslip_context = create_payslip(request, sal_obj, sal_form)
            month = sal_obj.salary_month
        else:  # Form was not valid
            messages.error(request, sal_form.errors)
        
    # print('create --> ', create_payslip_context)
    context = set_context(request=request, create_payslip_context=create_payslip_context, month=month, sal_form=sal_form)
    return render(request, 'create-salary.html', context)


def month_name(month_number):
    return calendar.month_name[month_number]


@login_required(login_url='home:user-login')
def listSalaryFromMonth(request, month, year , batch_id):
    if batch_id == 0 :
         salaries_list = Salary_elements.objects.filter(
        salary_month=month, salary_year=year, end_date__isnull=True)
    else:
        salaries_list = Salary_elements.objects.filter(
            salary_month=month, salary_year=year, assignment_batch__id = batch_id , end_date__isnull=True)
    monthSalaryContext = {
        'page_title': _('salaries for month {}').format(month_name(month)),
        'salaries_list': salaries_list,
        'v_month': month,
        'v_year': year
    }
    return render(request, 'list-salary-month.html', monthSalaryContext)


@login_required(login_url='home:user-login')
def changeSalaryToFinal(request, month, year):
    draft_salary = Salary_elements.objects.filter(
        salary_month=month, salary_year=year)
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
    ).order_by('element_id__sequence')
    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                              element_id__classification__code='deduct',
                                                              salary_month=month_number, salary_year=salary_year
                                                              ).order_by('element_id__sequence')

    # Not used on the html
    emp_payment = Payment.objects.filter(
        (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)), emp_id=emp_id)
    monthSalaryContext = {
        'page_title': _('salary information for {}').format(salary_obj.emp),
        'salary_obj': salary_obj,
        'emp_elements_incomes': emp_elements_incomes,
        'emp_elements_deductions': emp_elements_deductions,
        'emp_payment': emp_payment,
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
def render_all_payslip(request, month, year):
    template_path = 'all-payslip.html'
    all_salary_obj = get_list_or_404(
        Salary_elements, salary_month=month, salary_year=year)
    new_thing = {}
    for sal in all_salary_obj:
        emp_elements = Employee_Element.objects.filter(emp_id=sal.emp.id)
        new_thing['emp_salary'] = sal
        new_thing['emp_elements'] = emp_elements
    context = {
        'all_salary_obj': all_salary_obj,
        'emp_elements': new_thing['emp_elements'],
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
    required_salary = Salary_elements.objects.filter(
        salary_month=month, salary_year=year)
    for sal in required_salary:
        sal.end_date = date.today()
        sal.save()
    return redirect('payroll_run:list-salary')


@login_required(login_url='home:user-login')
def ValidatePayslip(request):
    assignment_batch = request.GET.get('assignment_batch', None)
    salary_month = request.GET.get('salary_month', None)
    salary_year = request.GET.get('salary_year', None)

    if assignment_batch == '':
        emp_list = Employee.objects.filter(
            (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
    else:
        assignment_batch_obj = Assignment_Batch.objects.get(id=assignment_batch.id)
        emp_list = Employee.objects.filter(
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
        assignment_batch_obj = Assignment_Batch.objects.get(id=assignment_batch)
        emp_list = Employee.objects.filter(
            id__in=includeAssignmentEmployeeFunction(
                assignment_batch_obj)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                assignment_batch_obj))
        salary_to_create = Salary_elements(
            elements_type_to_run=elements_type_to_run,
            salary_month=salary_month,
            salary_year=salary_year,
            assignment_batch = assignment_batch_obj,
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


def get_elements(sal_obj):
    """
    get elements to run
    :param sal_obj:
    :return: queryset of elements
    by: amira
    date: 23/05/2021
    """
    if sal_obj.elements_type_to_run == 'appear':
        elements = Employee_Element.objects.filter(element_id__appears_on_payslip=True).filter(
            (Q(start_date__lte=date.today()) & (
                    Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
    else:
        elements = Employee_Element.objects.filter(element_id=sal_obj.element).filter(
            Q(start_date__lte=date.today()) & (
                (Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
    return elements


def get_employees(sal_obj):
    """
    get employees
    :param sal_obj:
    :return: queryset of employees
    by: amira
    date: 23/05/2021
    """
    employees = 0
    if sal_obj.assignment_batch is not None:
        employees = Employee.objects.filter(
            id__in=includeAssignmentEmployeeFunction(
                sal_obj.assignment_batch)).exclude(
            id__in=excludeAssignmentEmployeeFunction(
                sal_obj.assignment_batch))
    else:
        employees = Employee.objects.filter(
            (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
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
        emp = EmployeeStructureLink.objects.get(employee=employee)
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
            EmployeeStructureLink.objects.get(employee=employee)
        except EmployeeStructureLink.DoesNotExist:
            msg_str = str(_(": don't have Structure Link, Please add Structure Link to them and create again"))
            employees_dont_have_structurelink.append(employee.emp_name)
            employees = ', '.join(employees_dont_have_structurelink) + msg_str

    if len(employees_dont_have_structurelink) > 0:
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': employees,
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
            msg_str = str(_(": don't have basic, add basic to them and create again"))
            employees_dont_have_basic.append(employee.emp_name)
            not_have_basic = ', '.join(employees_dont_have_basic) + msg_str


    if len(employees_dont_have_basic) > 0:
        create_context = {
            'page_title': _('create salary'),
            'sal_form': sal_form,
            'employees': 0,  # to not to show employees structure link error
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
        insurance_amount=salary_calc.calc_employee_insurance(),
        # TODO need to check if the tax is applied
        tax_amount=salary_calc.calc_taxes_deduction() if structure == 'Gross to Net' else salary_calc.net_to_tax(),
        deductions=salary_calc.calc_emp_deductions_amount(),
        gross_salary=salary_calc.calc_gross_salary() if structure == 'Gross to Net' else salary_calc.net_to_gross(),
        net_salary=salary_calc.calc_net_salary() if structure == 'Gross to Net' else salary_calc.calc_basic_net() ,
        penalties=total_absence_value,
        assignment_batch=sal_obj.assignment_batch,
    )
    s.save()


def create_payslip(request, sal_obj, sal_form=None):
    element = sal_obj.element if sal_obj.element else None

    # get elements for all employees.
    elements = get_elements(sal_obj)

    employees = get_employees(sal_obj)

    # TODO: review the include and exclude assignment batch
    # to check every employee have structure link
    employees_structure_link = check_structure_link(employees=employees, sal_form=sal_form)
    if employees_structure_link != {}:
        return employees_structure_link  # return dict of errors msgs for structure link

    # to check every employee have basic
    employees_basic = check_have_basic(employees=employees, sal_form=sal_form)
    if employees_basic != {}:
        return employees_basic  # return dict of errors msgs for basic

    # if all employees have structure link
    if employees_structure_link == {} and employees_basic == {}:
        try:
            for employee in employees:
                structure = get_structure_type(employee)
                emp_elements = Employee_Element.objects.filter(element_id__in=elements, emp_id=employee).values('element_id')
                sc = Salary_Calculator(company=request.user.company, employee=employee, elements=emp_elements)
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
