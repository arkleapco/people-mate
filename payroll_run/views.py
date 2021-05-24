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
from employee.models import Employee_Element, Employee, JobRoll, Payment, EmployeeStructureLink
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
    salaryContext = {
        "page_title": _("salary list"),
        "salary_list": salary_list,
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


def set_context_and_render(request, sal_form, employees, not_have_basic):
    """
    set context of salary and render to salary list
    :param sal_form:
    :param employees:
    :param not_have_basic:
    :return:
    """
    salContext = {
        'page_title': _('create salary'),
        'sal_form': sal_form,
        'employees': employees,
        'not_have_basic': not_have_basic,
    }
    return render(request, 'create-salary.html', salContext)


@login_required(login_url='home:user-login')
def createSalaryView(request):
    user_lang = to_locale(get_language())
    sal_form = SalaryElementForm(user=request.user)
    employees_dont_have_structurelink = []
    employees_dont_have_basic = []
    employees = 0
    not_have_basic = 0
    if request.method == 'POST':
        sal_form = SalaryElementForm(request.POST, user=request.user)
        if sal_form.is_valid():
            sal_obj = sal_form.save(commit=False)
            element = sal_obj.element if sal_obj.element else None
            # run employee on all emps.
            elements = get_elements(sal_obj)

            emps = get_employees(sal_obj)
            # TODO: review the include and exclude assignment batch
            # to check every employee have structure link
            # if employee doesnt have structure link
            for employee in emps:

                # emp_elements = Employee_Element.objects.filter(element_id__in=elements, emp_id=employee).values('element_id')
                # sc = Salary_Calculator(company=request.user.company, employee=employee, elements=emp_elements)
                try:
                    emp = EmployeeStructureLink.objects.get(employee=employee)
                    structure = emp.salary_structure.structure_type
                except EmployeeStructureLink.DoesNotExist:
                    employees_dont_have_structurelink.append(employee.emp_name)
                    employees = ', '.join(employees_dont_have_structurelink) \
                                + ': dont have structurelink, add structurelink to them and create again'
                if len(employees_dont_have_structurelink) > 0:
                    return set_context_and_render(request, sal_form, employees, not_have_basic)

                # check that every employee have basic salary
                basic_net = Employee_Element.objects.filter(element_id__is_basic=True, emp_id=employee).filter(
                    (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
                if len(basic_net) == 0:
                    employees_dont_have_basic.append(employee.emp_name)
                    not_have_basic = ', '.join(employees_dont_have_basic) \
                                     + ': dont have basic, add basic to them and create again'
                if len(employees_dont_have_basic) > 0:
                    return set_context_and_render(request, sal_form, employees, not_have_basic)

            # if all employees have structure link
            if len(employees_dont_have_structurelink) == 0 and len(employees_dont_have_basic) == 0:
                try:
                    for x in emps:
                        emp_elements = Employee_Element.objects.filter(element_id__in=elements, emp_id=x).values(
                            'element_id')
                        sc = Salary_Calculator(company=request.user.company, employee=x, elements=emp_elements)
                        absence_value_obj = EmployeeAbsence.objects.filter(employee_id=x.id).filter(
                            end_date__year=sal_obj.salary_year).filter(end_date__month=sal_obj.salary_month)
                        total_absence_value = 0
                        for i in absence_value_obj:
                            total_absence_value += i.value
                        if structure == 'Gross to Net':
                            s = Salary_elements(
                                emp=x,
                                elements_type_to_run=sal_obj.elements_type_to_run,
                                salary_month=sal_obj.salary_month,
                                salary_year=sal_obj.salary_year,
                                run_date=sal_obj.run_date,
                                created_by=request.user,
                                incomes=sc.calc_emp_income(),
                                element=element,
                                insurance_amount=sc.calc_employee_insurance(),
                                # TODO need to check if the tax is applied
                                tax_amount=sc.calc_taxes_deduction(),
                                deductions=sc.calc_emp_deductions_amount(),
                                gross_salary=sc.calc_gross_salary(),
                                net_salary=sc.calc_net_salary(),
                                penalties=total_absence_value,
                                assignment_batch=sal_obj.assignment_batch,

                            )
                            print("uuuuuuuuuuuuuuuuuuuuuuuuuuuuu", sc.calc_taxes_deduction())

                        else:
                            s = Salary_elements(
                                emp=x,
                                elements_type_to_run=sal_obj.elements_type_to_run,
                                salary_month=sal_obj.salary_month,
                                salary_year=sal_obj.salary_year,
                                run_date=sal_obj.run_date,
                                created_by=request.user,
                                incomes=sc.calc_emp_income(),
                                element=element,
                                insurance_amount=sc.calc_employee_insurance(),
                                # TODO need to check if the tax is applied
                                tax_amount=sc.net_to_tax(),
                                deductions=sc.calc_emp_deductions_amount(),
                                gross_salary=sc.net_to_gross(),
                                net_salary=sc.calc_basic_net(),
                                penalties=total_absence_value,
                                assignment_batch=sal_obj.assignment_batch,

                            )

                        s.save()
                except IntegrityError:
                    if user_lang == 'ar':
                        error_msg = "تم إنشاء  راتب هذا الشهر من قبل"
                        messages.error(request, error_msg)
                    else:
                        error_msg = "Payroll for this month created befor"
                        messages.error(request, error_msg)

                if user_lang == 'ar':
                    success_msg = 'تم تشغيل راتب شهر {} بنجاح'.format(
                        calendar.month_name[sal_obj.salary_month])
                    messages.success(request, success_msg)
                else:
                    success_msg = 'Payroll for month {} done successfully'.format(
                        calendar.month_name[sal_obj.salary_month])
                return redirect('payroll_run:list-salary')

            else:
                print('employees')
                print('employees_dont_have_basic')

        else:  # Form was not valid
            messages.error(request, sal_form.errors)
    salContext = {
        'page_title': _('create salary'),
        'sal_form': sal_form,
        'employees': employees,
        'not_have_basic': not_have_basic,
    }
    return render(request, 'create-salary.html', salContext)


def month_name(month_number):
    return calendar.month_name[month_number]


@login_required(login_url='home:user-login')
def listSalaryFromMonth(request, month, year):
    salaries_list = Salary_elements.objects.filter(
        salary_month=month, salary_year=year, end_date__isnull=True)
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
    # if appear_on_payslip == 'appear':
    #
    #     elements = Employee_Element.objects.filter(element_id__appears_on_payslip=True).filter(
    #         (Q(start_date__lte=date.today()) & (
    #             Q(end_date__gt=salary_obj.run_date) | Q(end_date__isnull=True)))).values('element_id')
    # else:
    #     elements = Employee_Element.objects.filter(element_id__id=salary_obj.element.id,
    #                                                element_id__appears_on_payslip=False).filter(
    #         (Q(start_date__lte=date.today()) & (
    #             Q(end_date__gt=salary_obj.run_date) | Q(end_date__isnull=True)))).values('element_id')

    # If the payslip is run on payslip elements get the payslip elements only from history
    # otherwise get the non payslip elements
    if appear_on_payslip == 'appear':

        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=True, salary_month=month_number, salary_year=salary_year).values('element_id')
    else:
        elements = Employee_Element_History.objects.filter(element_id__appears_on_payslip=False, salary_month=month_number, salary_year=salary_year).values('element_id')

    # emp_elements_incomes = Employee_Element.objects.filter(
    #     element_id__in=elements,
    #     emp_id=emp_id,
    #     element_id__classification__code='earn',
    #
    # ).order_by('element_id__sequence')
    # emp_elements_deductions = Employee_Element.objects.filter(element_id__in=elements, emp_id=emp_id,
    #                                                           element_id__classification__code='deduct',
    #                                                           ).order_by('element_id__sequence')

    # Get payroll elements from history instead of from employee elements
    # so that when editing employee elements and opening old payroll the elements
    # match to gross as it was previously run
    emp_elements_incomes = Employee_Element_History.objects.filter(element_id__in=elements,
        emp_id=emp_id,
        element_id__classification__code='earn',
        salary_month=month_number, salary_year=salary_year
    ).order_by('element_id__sequence')
    emp_elements_deductions = Employee_Element_History.objects.filter(element_id__in=elements, emp_id=emp_id,
                                                              element_id__classification__code='deduct',
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



def create_payslip(request, sal_obj):
# #     user_lang = to_locale(get_language())
# #     employees_dont_have_structurelink = []
# #     employees_dont_have_basic = []
# #     employees = 0
# #     not_have_basic = 0
# #     element = None
# #     # run employee on all emps.
# #     if sal_obj.elements_type_to_run == 'appear':
# #         elements = Employee_Element.objects.filter(element_id__appears_on_payslip=True).filter(
# #             (Q(start_date__lte=date.today()) & (
# #                     Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
# #     else:
# #         elements = Employee_Element.objects.filter(element_id=sal_obj.element).filter(
# #             Q(start_date__lte=date.today()) & (
# #                 (Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))).values('element_id')
# #         if len(elements) != 0:
# #             element = Element.objects.get(id=elements[0]['element_id'])
# #     if sal_obj.assignment_batch is not None:
# #         emps = Employee.objects.filter(
# #             id__in=includeAssignmentEmployeeFunction(
# #                 sal_obj.assignment_batch)).exclude(
# #             id__in=excludeAssignmentEmployeeFunction(
# #                 sal_obj.assignment_batch))
# #     else:
# #         emps = Employee.objects.filter(
# #             (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
# #     # TODO: review the include and exclude assignment batch
# #     #to check every employee have structure link
# #     for x in emps:
# #         emp_elements = Employee_Element.objects.filter(element_id__in=elements, emp_id=x).values('element_id')
# #         sc = Salary_Calculator(company=request.user.company, employee=x, elements=emp_elements)
# #         try:
# #             emp = EmployeeStructureLink.objects.get(employee=x)
# #             structure = emp.salary_structure.structure_type
# #         except EmployeeStructureLink.DoesNotExist:
# #             employees_dont_have_structurelink.append(x.emp_name)
# #             employees =  ', '.join(employees_dont_have_structurelink) + ': dont have structurelink, add structurelink to them and create again'
# #
# #         #check that every employee have basic salary
# #         basic_net =Employee_Element.objects.filter(element_id__is_basic=True, emp_id=x).filter(
# #                 (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
# #         if len(basic_net) == 0:
# #             employees_dont_have_basic.append(x.emp_name)
# #             not_have_basic =  ', '.join(employees_dont_have_basic) + ': dont have basic, add basic to them and create again'
# #
# #     #if all employees have structure link
# #     if len(employees_dont_have_structurelink) == 0 and len(employees_dont_have_basic) == 0:
# #         try:
# #             for x in emps:
# #                 emp_elements = Employee_Element.objects.filter(element_id__in=elements, emp_id=x).values('element_id')
# #                 sc = Salary_Calculator(company=request.user.company, employee=x, elements=emp_elements)
# #                 absence_value_obj = EmployeeAbsence.objects.filter(employee_id=x.id).filter(end_date__year=sal_obj.salary_year).filter(end_date__month=sal_obj.salary_month)
# #                 total_absence_value = 0
# #                 for i in absence_value_obj :
# #                     total_absence_value+= i.value
# #                 if structure == 'Gross to Net' :
# #                     s = Salary_elements(
# #                         emp=x,
# #                         elements_type_to_run=sal_obj.elements_type_to_run,
# #                         salary_month=sal_obj.salary_month,
# #                         salary_year=sal_obj.salary_year,
# #                         run_date=sal_obj.run_date,
# #                         created_by=request.user,
# #                         incomes=sc.calc_emp_income(),
# #                         element=element,
# #                         insurance_amount=sc.calc_employee_insurance(),
# #                         # TODO need to check if the tax is applied
# #                         tax_amount=sc.calc_taxes_deduction(),
# #                         deductions=sc.calc_emp_deductions_amount(),
# #                         gross_salary=sc.calc_gross_salary(),
# #                         net_salary=sc.calc_net_salary(),
# #                         penalties = total_absence_value,
# #                         assignment_batch = sal_obj.assignment_batch,
# #                         )
# #                 else :
# #                     s = Salary_elements(
# #                         emp=x,
# #                         elements_type_to_run=sal_obj.elements_type_to_run,
# #                         salary_month=sal_obj.salary_month,
# #                         salary_year=sal_obj.salary_year,
# #                         run_date=sal_obj.run_date,
# #                         created_by=request.user,
# #                         incomes=sc.calc_emp_income(),
# #                         element=element,
# #                         insurance_amount=sc.calc_employee_insurance(),
# #                         # TODO need to check if the tax is applied
# #                         tax_amount=sc.net_to_tax(),
# #                         deductions=sc.calc_emp_deductions_amount(),
# #                         gross_salary=sc.net_to_gross(),
# #                         net_salary=sc.calc_basic_net(),
# #                         penalties = total_absence_value,
# #                         assignment_batch = sal_obj.assignment_batch,
# #
# #                     )
# #                 s.save()
# #         except IntegrityError :
# #             if user_lang == 'ar':
# #                 error_msg = "تم إنشاء  راتب هذا الشهر من قبل"
# #                 messages.error(request, error_msg)
# #             else:
# #                 error_msg = "Payroll for this month created before"
# #                 messages.error(request, error_msg)
# #
# #         if user_lang == 'ar':
# #             success_msg = 'تم تشغيل راتب شهر {} بنجاح'.format(
# #             calendar.month_name[sal_obj.salary_month])
# #             messages.success(request, success_msg)
# #         else:
# #             success_msg = 'Payroll for month {} done successfully'.format(
# #             calendar.month_name[sal_obj.salary_month] )
# #     else:
# #         print('employees')
# #         print('employees_dont_have_basic')
    return True
