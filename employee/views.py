from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect, HttpResponse
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from datetime import date
from django.db.models import Q
from django.urls import reverse
from django.contrib import messages
from django.utils.translation import to_locale, get_language
from element_definition.models import Element
from employee.models import (
    Employee, JobRoll, Payment, Employee_Element, EmployeeStructureLink, Employee_File, Employee_Depandance)
from employee.forms import (EmployeeForm, JobRollForm, Employee_Payment_formset,
                            EmployeeElementForm, Employee_Element_Inline, EmployeeStructureLinkForm, EmployeeFileForm,
                            Employee_Files_inline, Employee_depandance_inline,ConfirmImportForm)
from payroll_run.models import Salary_elements
from payroll_run.forms import SalaryElementForm
from employee.fast_formula import *
from manage_payroll.models import Bank_Master , Payment_Type
from custom_user.models import User
from django.utils.translation import ugettext_lazy as _
from django.http import JsonResponse
from company.models import Position
from .resources import *
from leave.models import *
from django.db import IntegrityError
from django.db.models import Count
from .resources_two import *
from employee.fast_formula import FastFormula
from element_definition.models import StructureElementLink , SalaryStructure
from tablib import Dataset


# ###########################Employee View #################################

@login_required(login_url='home:user-login')
def createEmployeeView(request):
    emp_form = EmployeeForm()
    emp_form.fields['user'].queryset = User.objects.filter(company=request.user.company)
    jobroll_form = JobRollForm(user_v=request.user)
    payment_form = Employee_Payment_formset(queryset=Payment.objects.none())
    files_formset = Employee_Files_inline()
    depandance_formset = Employee_depandance_inline()
    for payment in payment_form:
        payment.fields['bank_name'].queryset = Bank_Master.objects.filter(
            enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))

        payment.fields['payment_type'].queryset = Payment_Type.objects.filter(enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
           
        # {'user': request.user},
    emp_element_form = Employee_Element_Inline(queryset=Employee_Element.objects.none(), form_kwargs={'user': request.user})
    for element in emp_element_form:
        element.fields['element_id'].queryset = Element.objects.none()
    if request.method == 'POST':
        emp_form = EmployeeForm(request.POST, request.FILES)
        jobroll_form = JobRollForm(request.user, request.POST)
        payment_form = Employee_Payment_formset(request.POST)
        files_formset = Employee_Files_inline(request.POST, request.FILES)
        depandance_formset = Employee_depandance_inline(request.POST)

        if emp_form.is_valid() and jobroll_form.is_valid() and payment_form.is_valid() and files_formset.is_valid() and depandance_formset.is_valid():
            emp_obj = emp_form.save(commit=False)
            if emp_obj.user:
                check_user_is_exist = Employee.objects.filter(user = emp_obj.user,enterprise=request.user.company).filter(Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True))
            else:
                check_user_is_exist = False
            if   not check_user_is_exist:
                emp_obj.enterprise = request.user.company
                emp_obj.created_by = request.user
                emp_obj.last_update_by = request.user
                emp_obj.save()
                job_obj = jobroll_form.save(commit=False)
                job_obj.emp_id_id = emp_obj.id
                job_obj.created_by = request.user
                job_obj.last_update_by = request.user
                job_obj.save()
                payment_form = Employee_Payment_formset(
                    request.POST, instance=emp_obj)
                if payment_form.is_valid():
                    emp_payment_obj = payment_form.save(commit=False)
                    for x in emp_payment_obj:
                        x.created_by = request.user
                        x.last_update_by = request.user
                        x.save()
                else:
                    user_lang = user_lang = to_locale(get_language())
                    if user_lang == 'ar':
                        error_msg = '{}, ???? ?????? ??????????????'.format('employee payment')
                    else:
                        error_msg = '{}, has somthig wrong'.format('employee payment')
                    # error_msg = '{}, has somthig wrong'.format(emp_payment_obj)
                    messages.success(request, error_msg)

                    user_lang = to_locale(get_language())
                    if user_lang == 'ar':
                        error_msg = '{}, ???? ?????? ??????????????'.format('element')
                        success_msg = ' {},???? ?????????? ????????????'.format(
                            emp_obj.emp_name)
                    else:
                        error_msg = '{}, has somthig wrong'.format('element')
                        success_msg = 'Employee {}, has been created successfully'.format(
                            emp_obj.emp_name)

                        messages.success(request, success_msg)

                files_obj = files_formset.save(commit=False)
                for file_obj in files_obj:
                    file_obj.created_by = request.user
                    file_obj.last_update_by = request.user
                    file_obj.emp_id = emp_obj
                    file_obj.save()

                # add depandances
                depandances_obj = depandance_formset.save(commit=False)
                for depandance_obj in depandances_obj:
                    depandance_obj.created_by = request.user
                    depandance_obj.last_update_by = request.user
                    depandance_obj.emp_id = emp_obj
                    depandance_obj.save()

                return redirect('employee:list-employee')

            else:
                messages.warning(request, "username already exists or is used with another employee")
    
        else:
            if emp_form.errors:
                messages.error(
                    request, "Employee Form has the following errors")
                messages.error(request, emp_form.errors)
            elif jobroll_form.errors:
                messages.error(
                    request, "Employee Job Form has the following errors")
                messages.error(request, jobroll_form.errors)
            elif files_formset.errors:
                messages.error(
                    request, "Employee Files Form has the following errors")
                messages.error(request, files_formset.errors)
            elif payment_form.errors:
                messages.error(
                    request, "Employee Payment Form has the following errors")
                messages.error(request, payment_form.errors)
            else:
                messages.error(
                    request, "Employee depandance Form has the following errors")
                messages.error(request, depandance_formset.errors)

    myContext = {
    "page_title": _("create employee"),
    "emp_form": emp_form,
    "jobroll_form": jobroll_form,
    "payment_form": payment_form,
    "files_formset": files_formset,
    "depandance_formset": depandance_formset,
    "create_employee": True,
    "flage": 0,
    }
    return render(request, 'create-employee.html', myContext)


@login_required(login_url='home:user-login')
def copy_element_values():
    element_obj = Element.objects.filter().exclude(global_value=0)
    emp_element = Employee_Element.objects.filter()
    for x in element_obj:
        for z in emp_element:
            if z.element_id_id == x.id:
                z.element_value = x.global_value
                z.save()


@login_required(login_url='home:user-login')
def listEmployeeView(request):
    emp_list = Employee.objects.filter(enterprise=request.user.company).filter(
        (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
    emp_job_roll_list = JobRoll.objects.filter(
        emp_id__enterprise=request.user.company).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
        Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True))
    myContext = {
        "page_title": _("List employees"),
        "emp_list": emp_list,
        'emp_job_roll_list': emp_job_roll_list,
    }
    return render(request, 'list-employees.html', myContext)


@login_required(login_url='home:user-login')
def listEmployeeCardView(request):
    emp_list = Employee.objects.filter(enterprise=request.user.company).filter(
        (Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)))
    emp_job_roll_list = JobRoll.objects.filter(
        emp_id__enterprise=request.user.company).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).filter(
        Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True))
    myContext = {
        "page_title": _("List employees"),
        "emp_job_roll_list": emp_job_roll_list,
        "emp_list":emp_list
    }
    return render(request, 'list-employees-card.html', myContext)

@login_required(login_url='home:user-login')
def list_terminated_employees(request):

    # emp_test = Employee.objects.filter(enterprise = request.user.company , terminationdate__isnull = False)
    emp_job_roll_list = JobRoll.objects.filter(emp_id__enterprise=request.user.company,emp_id__terminationdate__isnull = False)

    
    myContext = {
        "page_title": _("List Terminated employees"),
        'emp_job_roll_list': emp_job_roll_list,
    }
    return render(request, 'list-terminated-employees.html', myContext)


@login_required(login_url='home:user-login')
def viewEmployeeView(request, pk):
    required_employee = get_object_or_404(Employee, pk=pk)
    required_jobRoll = JobRoll.objects.get(emp_id=required_employee, end_date__isnull=True)
    all_jobRoll = JobRoll.objects.filter(emp_id=pk).order_by('-id')
    all_payment = Payment.objects.filter(emp_id=pk, end_date__isnull=True).order_by('-id')
    all_elements = Employee_Element.objects.filter(emp_id=pk, end_date__isnull=True).order_by('element_id__element_name')
    employee_dependence = Employee_Depandance.objects.filter(emp_id=pk)
    myContext = {
        "page_title": _("view employee"),
        "required_employee": required_employee,
        "required_jobRoll": required_jobRoll,
        "all_payment": all_payment,
        "all_elements": all_elements,
        "all_jobRoll": all_jobRoll,
        'employee_dependence': employee_dependence,
    }
    return render(request, 'view-employee.html', myContext)


@login_required(login_url='home:user-login')
def updateEmployeeView(request, pk):
    required_jobRoll = JobRoll.objects.get(id=pk)
    required_employee = get_object_or_404(
        Employee, pk=required_jobRoll.emp_id.id)
    emp_form = EmployeeForm(instance=required_employee)
    files_formset = Employee_Files_inline(instance=required_employee)
    depandance_formset = Employee_depandance_inline(instance=required_employee)
    
    # filter the user fk list to show the company users only.
    emp_form.fields['user'].queryset = User.objects.filter(
        company=request.user.company)
    jobroll_form = JobRollForm(user_v=request.user, instance=required_jobRoll)

    payment_form = Employee_Payment_formset(instance=required_employee)
    for payment in payment_form:
        payment.fields['bank_name'].queryset = Bank_Master.objects.filter(
            enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
        
        payment.fields['payment_type'].queryset = Payment_Type.objects.filter(enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
               
    
    
    
    get_employee_salary_structure = ""
    employee_element_qs = Employee_Element.objects.filter(
        emp_id=required_employee, end_date__isnull=True,element_id__end_date__isnull=True).order_by('element_id__element_name')
    employee_has_structure = False
    files = Employee_File.objects.filter(emp_id=required_employee)

    try:
        employee_salary_structure = EmployeeStructureLink.objects.get(
            employee=required_employee, end_date__isnull=True)
        employee_has_structure = True
        get_employee_salary_structure = employee_salary_structure.salary_structure
    except EmployeeStructureLink.DoesNotExist:
        employee_has_structure = False

    employee_element_form = EmployeeElementForm(user=request.user)

    if request.method == 'POST':
        jobroll_form = JobRollForm(
            request.user, request.POST, instance=required_jobRoll)
        emp_form = EmployeeForm(
            request.POST, request.FILES, instance=required_employee)
        payment_form = Employee_Payment_formset(
            request.POST, instance=required_employee)
        files_formset = Employee_Files_inline(
            request.POST, request.FILES, instance=required_employee)
        depandance_formset = Employee_depandance_inline(
            request.POST, instance=required_employee)

        if EmployeeStructureLink.DoesNotExist:
            emp_link_structure_form = EmployeeStructureLinkForm(request.POST,user=request.user)
        else:
            emp_link_structure_form = EmployeeStructureLinkForm(
                request.POST, user=request.user,instance=employee_salary_structure)

        employee_element_form = EmployeeElementForm(request.user , request.POST)
        old_obj = Employee(
            emp_number=required_employee.emp_number,
            emp_name=required_employee.emp_name,
            address1=required_employee.address1,
            address2=required_employee.address2,
            phone=required_employee.phone,
            mobile=required_employee.mobile,
            date_of_birth=required_employee.date_of_birth,
            hiredate=required_employee.hiredate,
            email=required_employee.email,
            picture=required_employee.picture,
            is_active=required_employee.is_active,
            identification_type=required_employee.identification_type,
            id_number=required_employee.id_number,
            place_of_birth=required_employee.place_of_birth,
            nationality=required_employee.nationality,
            field_of_study=required_employee.field_of_study,
            education_degree=required_employee.education_degree,
            gender=required_employee.gender,
            social_status=required_employee.social_status,
            military_status=required_employee.military_status,
            religion=required_employee.religion,
            insured=required_employee.insured,
            insurance_number=required_employee.insurance_number,
            insurance_date=required_employee.insurance_date,
            insurance_salary=required_employee.insurance_salary,
            has_medical=required_employee.has_medical,
            medical_number=required_employee.medical_number,
            medical_date=required_employee.medical_date,
            emp_start_date=required_employee.emp_start_date,
            emp_end_date=date.today(),
            created_by=required_employee.created_by,
            creation_date=required_employee.creation_date,
            last_update_by=required_employee.last_update_by,
            last_update_date=required_employee.last_update_date,
            enterprise_id=required_employee.enterprise_id,
            user_id=required_employee.user_id,
            emp_type=required_employee.emp_type,
            terminationdate=required_employee.terminationdate,
        )
        old_obj.save()
        if emp_form.is_valid() and jobroll_form.is_valid() and payment_form.is_valid() and files_formset.is_valid() and depandance_formset.is_valid():
            emp_obj = emp_form.save(commit=False)
            if emp_obj.user:
                if emp_obj.emp_end_date:
                    check_user_is_exist = Employee.objects.filter(user = emp_obj.user,enterprise=request.user.company ).filter(Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True))
                else:
                    check_user_is_exist = Employee.objects.filter(user = emp_obj.user,enterprise=request.user.company).filter(Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).exclude(id = required_employee.id)
            else:
                check_user_is_exist = False

            if not check_user_is_exist:
                emp_obj.created_by = request.user
                emp_obj.last_update_by = request.user
                emp_obj.save()
                #
                job_obj = jobroll_form.save(commit=False)
                job_obj.emp_id_id = emp_obj.id
                job_obj.created_by = request.user
                job_obj.last_update_by = request.user
                job_obj.save()
                #
                payment_form = Employee_Payment_formset(
                    request.POST, instance=emp_obj)
                emp_payment_obj = payment_form.save(commit=False)
                for x in emp_payment_obj:
                    x.created_by = request.user
                    x.last_update_by = request.user
                    x.save()
                #
                files_obj = files_formset.save(commit=False)
                for file_obj in files_obj:
                    file_obj.created_by = request.user
                    file_obj.last_update_by = request.user
                    file_obj.emp_id = emp_obj
                    file_obj.save()
                #
                depandances_obj = depandance_formset.save(commit=False)
                for depandance_obj in depandances_obj:
                    depandance_obj.created_by = request.user
                    depandance_obj.last_update_by = request.user
                    depandance_obj.emp_id = emp_obj
                    depandance_obj.save()
                #
                if emp_obj.terminationdate:
                    terminat_employee(request,pk)

                """
                emp_element_obj = employee_element_form.save(commit=False)
                emp_element_obj.emp_id = required_employee
                emp_element_obj.created_by = request.user
                emp_element_obj.last_update_by = request.user
                emp_element_obj.save()
                """
                user_lang = to_locale(get_language())

                if user_lang == 'ar':
                    success_msg = ' {},???? ?????????? ????????????'.format(required_employee)
                else:
                    success_msg = 'Employee {}, has been created successfully'.format(
                        required_employee)
                return redirect('employee:list-employee')
            else:
                messages.warning(request, "username already exists or is used with another employee")
        elif not emp_form.is_valid():
            messages.error(request, emp_form.errors)
        elif not jobroll_form.is_valid():
            messages.error(request, jobroll_form.errors)
        elif not payment_form.is_valid():
            messages.error(request, payment_form.errors)
        elif not files_formset.is_valid():
            messages.error(request, files_formset.errors)
        elif not depandance_formset.is_valid():
            messages.error(request, depandance_formset.errors)

    myContext = {
        "page_title": _("update employee"),
        "emp_form": emp_form,
        "jobroll_form": jobroll_form,
        "payment_form": payment_form,
        "required_employee": required_employee,
        "employee_element_qs": employee_element_qs,
        "employee_has_structure": employee_has_structure,
        "employee_element_form": employee_element_form,
        "get_employee_salary_structure": get_employee_salary_structure,
        "emp": pk,
        "required_jobRoll": required_jobRoll,
        "flage": 1,
        "files_formset": files_formset,
        "depandance_formset": depandance_formset,
    }
    return render(request, 'create-employee.html', myContext)


@login_required(login_url='home:user-login')
def correctEmployeeView(request, pk):
    required_jobRoll = JobRoll.objects.get(id=pk)
    required_employee = get_object_or_404(
        Employee, pk=required_jobRoll.emp_id.id)
    # s = EmployeeStructureLink.objects.get(employee=required_employee)
    # print("$$$$$$$$$$$$$$$$$$$$$$$$$4",s)
    jobs = JobRoll.objects.filter(emp_id=required_employee).order_by('end_date')
    emp_form = EmployeeForm(instance=required_employee)
    files_formset = Employee_Files_inline(instance=required_employee)
    depandance_formset = Employee_depandance_inline(instance=required_employee)
  
    # filter the user fk list to show the company users only.
    emp_form.fields['user'].queryset = User.objects.filter(
        company=request.user.company)
    jobroll_form = JobRollForm(user_v=request.user, instance=required_jobRoll)

    payment_form = Employee_Payment_formset(instance=required_employee)
    for payment in payment_form:
        payment.fields['bank_name'].queryset = Bank_Master.objects.filter(
            enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
        
        payment.fields['payment_type'].queryset = Payment_Type.objects.filter(enterprise=request.user.company).filter(
                Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
            
    get_employee_salary_structure = ""

    '''
        updateing employee element part to show the elements & values for that Employee
        (removing the formset) and adding a button to link salary structure to that employee.
        By: Ahd Hozayen
        Date: 29-12-2020
    '''
    employee_element_qs = Employee_Element.objects.filter(
        emp_id=required_employee, end_date__isnull=True,element_id__end_date__isnull=True).order_by('element_id__element_name')
    employee_has_structure = False
    files = Employee_File.objects.filter(emp_id=required_employee)

    try:
        employee_salary_structure = EmployeeStructureLink.objects.get(
            employee=required_employee, end_date__isnull=True)
        employee_has_structure = True
        get_employee_salary_structure = employee_salary_structure.salary_structure
        # emp_form.fields['salary_structure'].initial = employee_salary_structure.salary_structure
    except EmployeeStructureLink.DoesNotExist:
        employee_has_structure = False

    employee_element_form = EmployeeElementForm(user=request.user)

    if request.method == 'POST':
        jobroll_form = JobRollForm(
            request.user, request.POST, instance=required_jobRoll)
        emp_form = EmployeeForm(
            request.POST, request.FILES, instance=required_employee)
        payment_form = Employee_Payment_formset(
            request.POST, instance=required_employee)
        files_formset = Employee_Files_inline(
            request.POST, request.FILES, instance=required_employee)
        depandance_formset = Employee_depandance_inline(
            request.POST, instance=required_employee)

        if EmployeeStructureLink.DoesNotExist:
            emp_link_structure_form = EmployeeStructureLinkForm(request.POST,user=request.user)
        else:
            emp_link_structure_form = EmployeeStructureLinkForm(
                request.POST,user=request.user, instance=employee_salary_structure)

        employee_element_form = EmployeeElementForm(request.user  ,request.POST)

        if emp_form.is_valid() and jobroll_form.is_valid() and payment_form.is_valid() and files_formset.is_valid() and depandance_formset.is_valid():
            emp_obj = emp_form.save(commit=False)
            if emp_obj.user:
                if emp_obj.emp_end_date:
                    check_user_is_exist = Employee.objects.filter(user = emp_obj.user,enterprise=request.user.company ).filter(Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True))
                else:
                    check_user_is_exist = Employee.objects.filter(user = emp_obj.user,enterprise=request.user.company).filter(Q(emp_end_date__gt=date.today()) | Q(emp_end_date__isnull=True)).exclude(id = required_employee.id)
            else:
                check_user_is_exist= False

            if not check_user_is_exist:
                emp_obj.created_by = request.user
                emp_obj.last_update_by = request.user
                emp_obj.save()
                #
                job_obj = jobroll_form.save(commit=False)
                job_obj.emp_id_id = emp_obj.id
                job_obj.created_by = request.user
                job_obj.last_update_by = request.user
                job_obj.save()
                #
                # payment_form = Employee_Payment_formset(
                #     request.POST, instance=emp_obj)
                emp_payment_obj = payment_form.save(commit=False) 
                for x in emp_payment_obj:
                    x.created_by = request.user
                    x.last_update_by = request.user
                    x.save()
                #
                files_formset = Employee_Files_inline(
                    request.POST, request.FILES, instance=emp_obj)
                if files_formset.is_valid():
                    files_obj = files_formset.save(commit=False)
                    for file_obj in files_obj:
                        file_obj.created_by = request.user
                        file_obj.last_update_by = request.user
                        file_obj.save()
                #
                depandances_obj = depandance_formset.save(commit=False)
                for depandance_obj in depandances_obj:
                    depandance_obj.created_by = request.user
                    depandance_obj.last_update_by = request.user
                    depandance_obj.emp_id = emp_obj
                    depandance_obj.save()
                #
                if emp_obj.terminationdate:
                    terminat_employee(request,pk)

                user_lang = to_locale(get_language())

                if user_lang == 'ar':
                    success_msg = ' {},???? ?????????? ????????????'.format(required_employee)
                else:
                    success_msg = 'Employee {}, has been created successfully'.format(
                        required_employee)
                return redirect('employee:list-employee')
            else:
                messages.warning(request, "username already exists or is used with another employee")    

        elif not emp_form.is_valid():
            messages.error(request, "Employee Form has the following errors")
            messages.error(request, emp_form.errors)
        elif not jobroll_form.is_valid():
            messages.error(request, "Job Form has the following errors")
            messages.error(request, jobroll_form.errors)
        elif not payment_form.is_valid():
            messages.error(request, "Payment Form has the following errors")
            messages.error(request, payment_form.errors)
        elif not files_formset.is_valid():
            messages.error(request, "File Form has the following errors")
            messages.error(request, files_formset.errors)
        elif not depandance_formset.is_valid():
            messages.error(request, "Depandance Form has the following errors")
            messages.error(request, depandance_formset.errors)

    myContext = {
        "page_title": _("correct employee"),
        "emp_form": emp_form,
        "jobroll_form": jobroll_form,
        "payment_form": payment_form,
        "required_employee": required_employee,
        "employee_element_qs": employee_element_qs,
        "employee_has_structure": employee_has_structure,
        "employee_element_form": employee_element_form,
        "get_employee_salary_structure": get_employee_salary_structure,
        "emp": pk,
        "required_jobRoll": required_jobRoll,
        "flage": 1,
        "files_formset": files_formset,
        "depandance_formset": depandance_formset,
    }
    return render(request, 'create-employee.html', myContext)


@login_required(login_url='home:user-login')
def create_link_employee_structure(request, pk):
    required_jobRoll = JobRoll.objects.get(id=pk)
    required_employee = get_object_or_404(Employee, pk=required_jobRoll.emp_id.id, emp_end_date__isnull=True)
    emp_link_structure_form = EmployeeStructureLinkForm(user=request.user)
    if request.method == 'POST':
        emp_link_structure_form = EmployeeStructureLinkForm(request.POST, user=request.user)
        if emp_link_structure_form.is_valid():
            try:
                emp_structure_obj = emp_link_structure_form.save(commit=False)
                emp_structure_obj.employee = required_employee 
                emp_structure_obj.created_by = request.user
                emp_structure_obj.last_update_by = request.user
                emp_structure_obj.save()

            # except IntegrityError as e: 
            except Exception as e: 
                # if 'unique constraint' in e.message: 
                msg = 'employee and element must be unique'
                print(e)
                print(msg)
                messages.warning(request, msg)
                return redirect('employee:correct-employee', pk=pk)
            return redirect('employee:correct-employee', pk=pk)
        else:
            messages.warning(request, emp_link_structure_form.errors)
    my_context = {
        "page_title": _("Link Employee Structure"),
        "required_employee": required_employee,
        "emp_link_structure_form": emp_link_structure_form,
        "required_jobRoll":required_jobRoll,
    }
    return render(request, 'link-structure.html', my_context)


@login_required(login_url='home:user-login')
def update_link_employee_structure(request, pk):
    required_jobRoll = JobRoll.objects.get(id=pk)

    required_employee = get_object_or_404(
        Employee, pk=required_jobRoll.emp_id.id)
    employee_salary_structure = EmployeeStructureLink.objects.get(employee=required_employee, end_date__isnull=True)
       
    
    emp_link_structure_form = EmployeeStructureLinkForm(
        instance=employee_salary_structure,user=request.user)

    if request.method == 'POST':
        emp_link_structure_form = EmployeeStructureLinkForm(
            request.POST,user=request.user, instance=employee_salary_structure)
        if emp_link_structure_form.is_valid():
            emp_structure_obj = emp_link_structure_form.save(commit=False)
            emp_structure_obj.employee = required_employee
            emp_structure_obj.created_by = request.user
            emp_structure_obj.last_update_by = request.user
            emp_structure_obj.save()
            return redirect('employee:correct-employee', pk=pk)
        else:
            messages.warning(request, emp_link_structure_form.errors)
    my_context = {
        "page_title": _("Link Employee Structure"),
        "required_jobRoll": required_jobRoll,
        "emp_link_structure_form": emp_link_structure_form,
    }
    return render(request, 'link-structure.html', my_context)


@login_required(login_url='home:user-login')
def deleteEmployeeView(request, pk):
    required_jobRoll = get_object_or_404(JobRoll, pk=pk)
    required_employee = required_jobRoll.emp_id
    try:
        jobroll_form = JobRollForm(
            user_v=request.user, instance=required_jobRoll)
        end_date_jobroll_obj = jobroll_form.save(commit=False)
        end_date_jobroll_obj.end_date = date.today()
        end_date_jobroll_obj.save(update_fields=['end_date'])

        emp_form = EmployeeForm(instance=required_employee)
        end_date_obj = emp_form.save(commit=False)
        end_date_obj.emp_end_date = date.today()
        end_date_obj.save(update_fields=['emp_end_date'])

        user_lang = to_locale(get_language())
        if user_lang == 'ar':

            success_msg = ' {},???? ?????? ????????????'.format(required_employee)
        else:

            success_msg = 'Employee {} was deleted successfully'.format(
                required_employee)

        # success_msg = 'Employee {} was deleted successfully'.format(
        # required_employee)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang = to_locale(get_language())
        if user_lang == 'ar':
            success_msg = '{} ???? ?????? ?????? '.format(required_employee)
        else:
            success_msg = '{} cannot be deleted '.format(required_employee)
        # success_msg = 'Employee {} cannot be deleted'.format(
        # required_employee)
        messages.error(request, success_msg)
        raise e
    return redirect('employee:list-employee')


@login_required(login_url='home:user-login')
def deleteEmployeePermanently(request, pk):
    required_employee = get_object_or_404(Employee, pk=pk)
    # required_jobRoll = get_object_or_404(JobRoll, emp_id=pk)
    try:
        required_employee.delete()
        user_lang = to_locale(get_language())
        if user_lang == 'ar':
            success_msg = ' {},???? ?????? ????????????'.format(required_employee)
        else:

            success_msg = 'Employee {} was deleted permanently successfully'.format(
                required_employee)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang = to_locale(get_language())
        if user_lang == 'ar':
            success_msg = '{} ???? ?????? ?????? '.format(required_employee)
        else:
            success_msg = '{} cannot be deleted '.format(required_employee)
        # success_msg = 'Employee {} cannot be deleted'.format(
        # required_employee)
        messages.error(request, success_msg)
        raise e
    return redirect('employee:list-employee')


def change_element_value(request):
    element = request.GET.get('element')
    element_value = request.GET.get('value')
    Employee_Element.objects.filter(
        id=element).update(element_value=element_value)
    element_after_update = Employee_Element.objects.get(id=element)
    element_after_update_element_value = element_after_update.element_value
    data = {'element_after_update_element_value': element_after_update_element_value,
            'element_value': element_value
            }
    if element_after_update_element_value != element_value:
        data['error_message'] = "Employee Element didn't save "

    return JsonResponse(data)


@login_required(login_url='home:user-login')
def export_employee_data(request):
    if request.method == 'POST':
        file_format = request.POST['file-format']
        employee_resource = EmployeeResource()
        dataset = employee_resource.export()

        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="employee_exported_data.csv"'
            return response
        elif file_format == 'JSON':
            response = HttpResponse(
                dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="employee_exported_data.json"'
            return response
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(
                dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="employee_exported_data.xls"'
            return response
    export_context = {
        'page_title': 'Please select format of file.',
    }
    return render(request, 'export.html', export_context)


@login_required(login_url='home:user-login')
def createJobROll(request, job_id):
    jobroll_form = JobRollForm(user_v=request.user)
    required_jobRoll = JobRoll.objects.get(id=job_id)
    if request.method == "POST":
        jobroll_form = JobRollForm(request.user, request.POST)
        if jobroll_form.is_valid():
            required_jobRoll.end_date = date.today()
            required_jobRoll.save()

            job_obj = jobroll_form.save(commit=False)
            job_obj.emp_id = required_jobRoll.emp_id
            job_obj.created_by = request.user
            job_obj.save()
        else:
            print(jobroll_form.errors)
        return redirect('employee:correct-employee',
                        pk=job_obj.id)

    else:
        return render(request, 'create-jobroll.html',
                      {'jobroll_form': jobroll_form, 'required_employee': required_jobRoll.emp_id})


@login_required(login_url='home:user-login')
def list_employee_leave_requests(request):
    """
        view to list all approved leave requests for all employees
        author: Ahmed Mamdouh
        created at: 04/03/2021
    """
    employees = Employee.objects.filter(
        emp_end_date__isnull=True, enterprise=request.user.company)  # get all active employees
    employees_leaves_approaved_requests = []
    leave_masters = LeaveMaster.objects.all()
    for employee in employees:
        leave_requests = Leave.objects.filter(status='Approved', user=employee.user).values(
            'leavetype__type', 'startdate', 'enddate')  ## get all approved leaves for this employee
        z = {
            'employee': employee.emp_name,
            'leave_requests': {}
        }  ### z is a dictionary for each employee and all his leaves
        z['leave_requests']['total'] = 0
        for master in leave_masters:
            leaves = [
                dictionary for dictionary in leave_requests if
                dictionary["leavetype__type"] == master.type]  ## get all leaves matches this leave master type
            num_of_days = 0  ## number of days for each leave type
            if len(leaves) != 0:
                for i in leaves:
                    num_of_days += abs((i['enddate'] -
                                        i['startdate']).days + 1)
            z['leave_requests'][master.type] = num_of_days
            z['leave_requests']['total'] = num_of_days + z['leave_requests']['total']
        employees_leaves_approaved_requests.append(z)

    context = {
        "leave_requests": employees_leaves_approaved_requests,
        "leave_masters": leave_masters,
    }
    return render(request, "list-leaves-history.html", context)


@login_required(login_url='home:user-login')
def create_employee_element(request, job_id):
    required_jobRoll = JobRoll.objects.get(id=job_id)
    required_employee = get_object_or_404(
        Employee, pk=required_jobRoll.emp_id.id)
    if request.method == "POST":
        emp_element_form = EmployeeElementForm(request.user, request.POST)
        if emp_element_form.is_valid():
            emp_obj = emp_element_form.save(commit=False)
            emp_obj.emp_id = required_employee
            emp_obj.created_by = request.user
            emp_obj.last_update_by = request.user
            try:
                emp_obj.save()
            except Exception as e:
                print(e)
                error_msg = " This employee already have this element update it"
                messages.error(request, error_msg)
                return redirect('employee:correct-employee',
                        pk=required_jobRoll.id)       


            element = emp_obj.element_id
            value = element.fixed_amount
            emp_obj.element_value = value
            emp_obj.save()

        #     if element.element_type == 'formula':
        #         if emp_obj.set_formula_amount(required_employee):
        #             if emp_obj.set_formula_amount(required_employee) == -1:
        #                 emp_obj.delete()
        #                 error_msg = " division by zero please check your element amount"
        #                 messages.error(request, error_msg)
        #             else:                                  
        #                 formula = emp_obj.set_formula_amount(required_employee)
        #         else:
        #             emp_obj.delete()
        #             error_msg = "employee not have the  element in element used in formula"
        #             messages.error(request, error_msg)

        #         """
        #         if formula == False :
        #             error_msg = "you must add "
        #             messages.error(request, error_msg)
        #             return redirect('employee:correct-employee', pk =required_jobRoll.id)
        #         """
        # else:
        #     print(emp_element_form.errors)
        #     error_msg = emp_element_form.errors
        #     messages.error(request, error_msg)
        return redirect('employee:correct-employee',
                        pk=required_jobRoll.id)




def calc_formula(request,where_flag , job_id):
    # where_flage define where this function is called from
    # from payroll run or the button recalculate formula.
    errors = []
    required_jobRoll = JobRoll.objects.get(id=job_id)
    required_employee = get_object_or_404(
        Employee, pk=required_jobRoll.emp_id.id)
    formula_element = Employee_Element.objects.filter(emp_id=required_employee.id,
             element_id__element_type='formula').order_by('element_id__sequence')
    for x in formula_element:
        value = FastFormula(required_employee.id, x.element_id , Employee_Element)
        amount = value.get_formula_amount()
        if amount is not False:
            if amount == -1:
                errors.append("element " + x.element_id.element_name + "for "+required_employee.emp_name + "  division by zero please check it's amount" )  
            else:  
                x.element_value = amount
                x.save()
        else:
            errors.append (x.element_id.element_name + "for employee "+required_employee.emp_name + "  it's code not in element master table")
    error_msg = errors
    messages.error(request, error_msg)
    if where_flag == 0:                         
        return redirect('employee:correct-employee',
                        pk=required_jobRoll.id)
    if where_flag == 1 :
        return True                    


def deleteElementView(request):
    element = request.GET.get('element')
    employee_element = get_object_or_404(Employee_Element, pk=element)
    user_lang = to_locale(get_language())
    try:
        if user_lang == 'ar':
            success_msg = '???? ?????? ???????????? ,{}'.format(employee_element)
        else:
            success_msg = 'Element {} was deleted successfully'.format(
                employee_element)
        employee_element.delete()
        # messages.success(request, success_msg)
    except Exception as e:
        if user_lang == 'ar':
            success_msg = '{} ???? ?????? ?????? '.format(employee_element)
        else:
            success_msg = '{} cannot be deleted '.format(employee_element)
        # messages.error(request, success_msg)
    return JsonResponse({"success_msg":success_msg})




def terminat_employee(request,job_roll_id):
    try:
        required_jobRoll = JobRoll.objects.get(id=job_roll_id)
        required_employee = Employee.objects.get(pk=required_jobRoll.emp_id.id)
        employee_elements = Employee_Element.objects.filter(emp_id=required_employee)
        if employee_elements:
            for element in employee_elements:
                element.end_date= required_employee.terminationdate
                element.save()
        required_employee.terminationdate = date.today()
        required_employee.emp_end_date = date.today()
        required_jobRoll.end_date = date.today()
        required_employee.save()
        required_jobRoll.save()
        success_msg = 'Employe  terminated successfully'
        messages.success(request,success_msg)
    except JobRoll.DoesNotExist:
        error_msg = 'no employee with this jobroll'
        messages.error(request,error_msg)
    except Employee.DoesNotExist:
        error_msg = 'no employee with this id'
        messages.error(request,error_msg)
    except Exception as e:
        print(e) 
        error_msg = 'cannot terminat, Some thing wrong connect to admin'
        messages.error(request,error_msg)
    return redirect('employee:list-employee')    


