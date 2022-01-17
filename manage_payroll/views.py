from django.shortcuts import render, redirect, get_object_or_404, get_list_or_404 , HttpResponse
from django.contrib.auth.decorators import login_required
from datetime import date
from django.db.models import Q
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from custom_user.models import User
from django.utils.translation import to_locale, get_language
from django.utils.translation import ugettext_lazy as _
from manage_payroll.models import (Assignment_Batch, Assignment_Batch_Exclude,
                                   Assignment_Batch_Include, Payment_Type, Payment_Method,
                                   Bank_Master, Payroll_Master)
from manage_payroll.forms import (AssignmentBatchForm, BatchIncludeFormSet,
                                  BatchExcludeFormSet, Payment_Type_Form, Payment_Method_Form,
                                  PaymentMethodInline, Bank_MasterForm, PayrollMasterForm)
from employee.models import JobRoll, Payment , EmployeeStructureLink , Employee
from payroll_run.models import Salary_elements
from datetime import date, datetime
import xlwt        
from employee.forms import PaymentForm   
from payroll_run.forms import SalaryElementForm     
from time import strptime



@login_required(login_url='home:user-login')
def listAssignmentBatchView(request):
    user_group = request.user.groups.all()[0].name 
    if user_group == 'mena':
        batch_list = Assignment_Batch.objects.filter((Q(end_date__gte=date.today())|Q(end_date__isnull=True)),created_by = request.user,payroll_id__enterprise=request.user.company)
    else:    
        batch_list = Assignment_Batch.objects.filter((Q(end_date__gte=date.today())|Q(end_date__isnull=True)),payroll_id__enterprise=request.user.company)
    batchContxt = {"page_title":_("Assignment Batchs") , 'batch_list': batch_list}
    return render(request, 'list-assignment-batch.html', batchContxt)


@login_required(login_url='home:user-login')
def createAssignmentBatchView(request):
    batch_form = AssignmentBatchForm()
    batch_include_form = BatchIncludeFormSet(
        queryset=Assignment_Batch_Include.objects.none(), form_kwargs={'user': request.user})
    batch_exclude_form = BatchExcludeFormSet(
        queryset=Assignment_Batch_Exclude.objects.none(), form_kwargs={'user': request.user})
    if request.method == 'POST':
        batch_form = AssignmentBatchForm(request.POST)
        batch_include_form = BatchIncludeFormSet(request.POST, form_kwargs={'user': request.user})
        batch_exclude_form = BatchExcludeFormSet(request.POST, form_kwargs={'user': request.user})
        if batch_form.is_valid() and batch_include_form.is_valid() and batch_exclude_form.is_valid():
            batch_form_obj = batch_form.save(commit=False)
            batch_form_obj.created_by = request.user
            batch_form_obj.last_update_by = request.user
            batch_form_obj.save()
            batch_include_form = BatchIncludeFormSet(
                request.POST, instance=batch_form_obj, form_kwargs={'user': request.user})
            batch_include_obj = batch_include_form.save(commit=False)
            for x in batch_include_obj:
                x.created_by = request.user
                x.last_update_by = request.user
                x.save()
            batch_exclude_form = BatchExcludeFormSet(
                request.POST, instance=batch_form_obj, form_kwargs={'user': request.user})
            batch_exclude_obj = batch_exclude_form.save(commit=False)
            for x in batch_exclude_obj:
                x.created_by = request.user
                x.last_update_by = request.user
                x.save()
                user_lang=user_lang=to_locale(get_language())
                if user_lang=='ar':
                    success_msg = 'تمت العملية بنجاح'
                else:
                    success_msg ='Create Successfully'
            # success_msg = 'Assignment Batch {}, has been created successfully'.format(
                # batch_form_obj.assignment_name)

                messages.success(request, success_msg)
            print("22222222222222222222222")    
            return redirect('manage_payroll:list-assignBatch')
        else:
            print("333333333333333333333333")
            if batch_form.has_error:
                messages.error(request, batch_form.errors)
            elif batch_exclude_form.has_error:
                messages.error(request, batch_exclude_form.errors)
            elif batch_include_form.has_error:
                messages.error(request, batch_include_form.errors)
    batchContext = {
        "page_title": _("Create new Assignment Batch"),
        'batch_form': batch_form,
        'batch_include_form': batch_include_form,
        'batch_exclude_form': batch_exclude_form
    }
    return render(request, 'create-assignment-batch.html', batchContext)


@login_required(login_url='home:user-login')
def updateAssignmentBatchView(request, pk):
    required_assignment_batch = Assignment_Batch.objects.get(pk=pk)
    batch_form = AssignmentBatchForm(instance=required_assignment_batch)
    batch_include_form = BatchIncludeFormSet(
        instance=required_assignment_batch, form_kwargs={'user': request.user})
    batch_exclude_form = BatchExcludeFormSet(
        instance=required_assignment_batch, form_kwargs={'user': request.user})
    if request.method == 'POST':
        batch_form = AssignmentBatchForm(
            request.POST, instance=required_assignment_batch)
        batch_include_form = BatchIncludeFormSet(
            request.POST, instance=required_assignment_batch, form_kwargs={'user': request.user})
        batch_exclude_form = BatchExcludeFormSet(
            request.POST, instance=required_assignment_batch, form_kwargs={'user': request.user})
        if batch_form.is_valid() and batch_include_form.is_valid() and batch_exclude_form.is_valid():
            batch_form_obj = batch_form.save(commit=False)
            batch_form_obj.last_update_by = request.user
            batch_form_obj.save()
            batch_include_obj = batch_include_form.save(commit=False)
            for x in batch_include_obj:
                x.created_by = request.user
                x.last_update_by = request.user
                x.save()
            batch_exclude_obj = batch_exclude_form.save(commit=False)
            for x in batch_exclude_obj:
                x.created_by = request.user
                x.last_update_by = request.user
                x.save()
                user_lang=user_lang=to_locale(get_language())
                if user_lang=='ar':
                    success_msg = 'تمت العملية بنجاح'
                else:
                    success_msg ='Create Successfully'
            # success_msg = 'Assignment Batch {}, has been created successfully'.format(
                # batch_form_obj.assignment_name)

                messages.success(request, success_msg)
            return redirect('manage_payroll:list-assignBatch')
        else:
            if batch_form.has_error:
                messages.error(request, batch_form.errors)
            elif batch_exclude_form.has_error:
                messages.error(request, batch_exclude_form.errors)
            elif batch_include_form.has_error:
                messages.error(request, batch_include_form.errors)
    batchContext = {
        "page_title": _("update Assignment Batch"),
        'batch_form': batch_form,
        'batch_include_form': batch_include_form,
        'batch_exclude_form': batch_exclude_form
    }
    return render(request, 'create-assignment-batch.html', batchContext)


@login_required(login_url='home:user-login')
def deleteAssignmentBatchView(request, pk):
    required_assignment_batch = get_object_or_404(Assignment_Batch, pk=pk)
    try:
        batch_form = AssignmentBatchForm(instance=required_assignment_batch)
        batch_obj = batch_form.save(commit=False)
        batch_obj.end_date = date.today()
        batch_include_form = BatchIncludeFormSet(
            instance=required_assignment_batch, form_kwargs={'user': request.user})
        batch_include_obj = batch_include_form.save(commit=False)
        for x in batch_include_obj:
            x.end_date = date.today()
            x.save(update_fields=['end_date'])
        batch_exclude_form = BatchExcludeFormSet(
            instance=required_assignment_batch, form_kwargs={'user': request.user})
        batch_exclude_obj = batch_exclude_form.save(commit=False)
        for x in batch_exclude_obj:
            x.end_date = date.today()
            x.save(update_fields=['end_date'])
        batch_obj.save(update_fields=['end_date'])

        user_lang=to_locale(get_language())
        if user_lang=='ar':
            success_msg = '{}تم حذف '.format(required_assignment_batch)
        else:
            success_msg = '{} was deleted successfully '.format(required_assignment_batch)
        # success_msg = '{} was deleted successfully'.format(
            # required_assignment_batch)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang=user_lang=to_locale(get_language())
        if user_lang=='ar':
            error_msg = '{} لم يتم حذف '.format(required_assignment_batch)
        else:
            error_msg = '{} cannot be deleted '.format(required_assignment_batch)
        # error_msg = '{} cannot be deleted '.format(required_assignment_batch)
            messages.error(request, error_msg)
        raise e
    return redirect('manage_payroll:list-assignBatch')

###############################################################################
#               Payment type & method inline form
###############################################################################
@login_required(login_url='home:user-login')
def createPaymentView(request):
    user = User.objects.get(id=request.user.id)
    company = user.company
    payment_type_form = Payment_Type_Form(company)
    payment_method_inline = PaymentMethodInline()
    if request.method == 'POST':
        payment_type_form = Payment_Type_Form(company,request.POST)
        payment_method_inline = PaymentMethodInline(request.POST)
        if payment_type_form.is_valid() or payment_method_inline.is_valid():
            payment_object = payment_type_form.save(commit=False)
            payment_object.enterprise = request.user.company
            payment_object.created_by = request.user
            payment_object.last_update_by = request.user
            payment_object.save()
            payment_method_inline = PaymentMethodInline(
                request.POST, instance=payment_object)
            if payment_method_inline.is_valid():
                inline_obj = payment_method_inline.save(commit=False)
                for row in inline_obj:
                    row.created_by = request.user
                    row.last_update_by = request.user
                    row.save()
            user_lang=user_lang=to_locale(get_language())
            if user_lang=='ar':
                success_msg = 'تمت العملية بنجاح'
            else:
                success_msg ='Create Successfully'
            messages.success(request, success_msg)
        else:
            messages.error(request, _('Payment form hase invalid data'))
        return redirect('manage_payroll:list-payments')

    paymentContext = {
        "page_title": _("create payment"),
                      'payment_type_form': payment_type_form,
                      'payment_method_inline': payment_method_inline}
    return render(request, 'payment-create.html', paymentContext)


@login_required(login_url='home:user-login')
def listPaymentView(request):
    payment_type_list = Payment_Type.objects.filter(enterprise=request.user.company).exclude((Q(end_date__gte=date.today())|Q(end_date__isnull=False)))
    payment_method_list = Payment_Method.objects.filter( payment_type__enterprise=request.user.company).exclude((Q(end_date__gte=date.today())|Q(end_date__isnull=False)))
    paymentContext = {
        "page_title":_("Payment Types"),
        'payment_type_list':payment_type_list,
        'payment_method_list':payment_method_list,
         }
    return render(request, 'payment-list.html', paymentContext)


@login_required(login_url='home:user-login')
def updatePaymentView(request, pk):
    user = User.objects.get(id=request.user.id)
    company = user.company
    payment_obj = Payment_Type.objects.get(pk=pk)
    payment_method_obj = Payment_Method.objects.filter(payment_type=pk)

    payment_type_form = Payment_Type_Form(company,instance=payment_obj)
    payment_method_inline = PaymentMethodInline(instance=payment_obj)
    if request.method == 'POST':
        old_payment_type = Payment_Type(
                                        enterprise = payment_obj.enterprise,
                                        type_name = payment_obj.type_name,
                                        category = payment_obj.category,
                                        start_date = payment_obj.start_date,
                                        end_date = date.today(),
                                        created_by = payment_obj.created_by,
                                        creation_date = payment_obj.creation_date,
                                        last_update_by = payment_obj.last_update_by,
                                        last_update_date = payment_obj.last_update_date,
        )
        old_payment_type.save()
        for method in payment_method_obj:
            old_payment_method = Payment_Method(
                                                payment_type = old_payment_type,
                                                method_name = method.method_name,
                                                bank_name = method.bank_name,
                                                account_number = method.account_number,
                                                swift_code = method.swift_code,
                                                start_date = method.start_date,
                                                end_date = date.today(),
                                                created_by = method.created_by,
                                                creation_date = method.creation_date,
                                                last_update_by = method.last_update_by,
                                                last_update_date = method.last_update_date,
            )
            old_payment_method.save()
        payment_type_form = Payment_Type_Form(company, request.POST, instance=payment_obj)
        payment_method_inline = PaymentMethodInline(request.POST, instance=payment_obj)
        if payment_type_form.is_valid() and payment_method_inline.is_valid():
            payment_object = payment_type_form.save(commit=False)
            payment_object.enterprise = request.user.company
            payment_object.created_by = request.user
            payment_object.last_update_by = request.user
            payment_object.save()
            payment_method_inline = PaymentMethodInline(
                request.POST, instance=payment_object)
            if payment_method_inline.is_valid():
                inline_obj = payment_method_inline.save(commit=False)
                for row in inline_obj:
                    row.created_by = request.user
                    row.last_update_by = request.user
                    row.save()      
                success_msg = _('Payment Updated Successfully')
                messages.success(request, success_msg)        
                return redirect('manage_payroll:list-payments')
                
            else:
                messages.error(request, _('payment_type_form hase invalid data'))
    paymentContext = {
        "page_title":_("update payment"),
                      'payment_type_form': payment_type_form,
                      'payment_method_inline': payment_method_inline}
    return render(request, 'payment-create.html', paymentContext)


@login_required(login_url='home:user-login')
def correctPaymentView(request, pk):
    user = User.objects.get(id=request.user.id)
    company = user.company
    payment_obj = Payment_Type.objects.get(pk=pk)
    payment_type_form = Payment_Type_Form(company , instance=payment_obj)
    payment_method_inline = PaymentMethodInline(instance=payment_obj)
    if request.method == 'POST':
        payment_type_form = Payment_Type_Form(company, request.POST,instance=payment_obj)
        payment_method_inline = PaymentMethodInline(request.POST, instance=payment_obj)
        if payment_type_form.is_valid() and payment_method_inline.is_valid():
            payment_object = payment_type_form.save(commit=False)
            payment_object.enterprise = request.user.company
            payment_object.created_by = request.user
            payment_object.last_update_by = request.user
            payment_object.save()
            payment_method_inline = PaymentMethodInline(
                request.POST, instance=payment_object)
            if payment_method_inline.is_valid():
                inline_obj = payment_method_inline.save(commit=False)
                for row in inline_obj:
                    row.created_by = request.user
                    row.last_update_by = request.user
                    row.save()
            success_msg = _('Payment Updated Successfully')
            messages.success(request, success_msg)
            return redirect('manage_payroll:list-payments')
           
        else:
            messages.error(request, _('payment_type_form hase invalid data'))
    paymentContext = {
        "page_title": _("correct payment"),
                      'payment_type_form': payment_type_form,
                      'payment_method_inline': payment_method_inline}
    return render(request, 'payment-create.html', paymentContext)


@login_required(login_url='home:user-login')
def deletePaymentView(request, pk):
    required_payment_type = get_object_or_404(Payment_Type, pk=pk)
    try:
        company = request.user.company
        type_form = Payment_Type_Form(company, instance=required_payment_type)
        type_obj = type_form.save(commit=False)
        type_obj.end_date = date.today()
        method_form = PaymentMethodInline(instance=required_payment_type)
        method_obj = method_form.save(commit=False)
        for x in method_obj:
            x.end_date = date.today()
            x.save(update_fields=['end_date'])
        type_obj.save(update_fields=['end_date'])
        user_lang=user_lang=to_locale(get_language())
        if user_lang=='ar':
            success_msg = '{}تم حذف '.format(required_payment_type)
        else:
            success_msg = '{} was deleted successfully '.format(required_payment_type)
        # success_msg = '{} was deleted successfully'.format(
            # required_payment_type)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang=user_lang=to_locale(get_language())
        if user_lang=='ar':
            error_msg = '{} لم يتم حذف '.format(required_payment_type)
        else:
            error_msg = '{} cannot be deleted '.format(required_payment_type)
        # error_msg = '{} cannot be deleted '.format(required_payment_type)
        messages.error(request, error_msg)
        raise e
    return redirect('manage_payroll:list-payments')

#               End of Payment type & method inline form
###############################################################################


@login_required(login_url='home:user-login')
def createBankAccountView(request):
    bank_form = Bank_MasterForm()
    if request.method == 'POST':
        bank_form = Bank_MasterForm(request.POST)
        if bank_form.is_valid():
            master_object = bank_form.save(commit=False)
            master_object.enterprise = request.user.company
            master_object.created_by = request.user
            master_object.last_update_by = request.user
            master_object.save()
            return redirect('manage_payroll:list-banks')
            success_msg = _('Bank Created Successfully')
            messages.success(request, success_msg)
        else:
            [messages.error(request, error[0])
             for error in bank_form.errors.values()]
    myContext = {"page_title":_("Create bank branch") ,
                 'bank_form': bank_form, }
    return render(request, 'create-bank-accounts.html', myContext)


@login_required(login_url='home:user-login')
def listBankAccountsView(request):
    if request.method == 'GET':
        bank_master = Bank_Master.objects.filter((Q(end_date__gte=date.today())|Q(end_date__isnull=True)), enterprise = request.user.company)
    myContext = {"page_title": _("Bank List"), 'bank_master': bank_master, }
    return render(request, 'list-bank-branchs.html', myContext)


@login_required(login_url='home:user-login')
def updateBankAccountView(request, pk):
    required_bank = Bank_Master.objects.get(pk=pk)
    if request.method == 'POST':
        bank_form = Bank_MasterForm(request.POST, instance=required_bank)
        if bank_form.is_valid():
            bank_form.save()
            return redirect('manage_payroll:list-banks')
            success_msg = _('Bank Updated Successfully')
            messages.success(request, success_msg)
            # redirect_to = reverse('manage_payroll:update-bank', kwargs={'pk': pk})
            # return redirect(redirect_to)
        else:
            [messages.error(request, account_form.errors)]
    else:
        bank_form = Bank_MasterForm(instance=required_bank)
    myContext = {"page_title": _("update bank details"), 'bank_form': bank_form, }
    return render(request, 'create-bank-accounts.html', myContext)


@login_required(login_url='home:user-login')
def deleteBankAccountView(request, pk):
    required_bank = get_object_or_404(Bank_Master, pk=pk)
    try:
        bank_form = Bank_MasterForm(instance=required_bank)
        bank_obj = bank_form.save(commit=False)
        bank_obj.end_date = date.today()
        bank_obj.save(update_fields=['end_date'])
        user_lang=user_lang=to_locale(get_language())
        if user_lang=='ar':
            success_msg = '{} تم حذف'.format(required_bank)
        else:
            success_msg ='{} was deleted successfully'.format(required_bank)
        # success_msg = '{} was deleted successfully'.format(required_bank)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang=user_lang=to_locale(get_language())
        if user_lang=='ar':
            error_msg = '{} لم يتم حذف '.format(required_bank)
        else:
            error_msg = '{} cannot be deleted '.format(required_bank)
        # error_msg = '{} cannot be deleted '.format(required_bank)
        messages.error(request, error_msg)
        raise e
    return redirect('manage_payroll:list-banks')

################################################################################
@login_required(login_url='home:user-login')
def listPayrollView(request):
    user_group = request.user.groups.all()[0].name 
    if user_group == 'mena':
        list_payroll = Payroll_Master.objects.filter(enterprise=request.user.company, created_by=request.user).filter(Q(end_date__gt=date.today())|Q(end_date__isnull=True))
    else:
        list_payroll = Payroll_Master.objects.filter(enterprise=request.user.company).filter(Q(end_date__gt=date.today())|Q(end_date__isnull=True))


    payrollContext = {"page_title":_("payroll list") ,
                      'list_payroll': list_payroll}
    return render(request, 'list-payrolls.html', payrollContext)


@login_required(login_url='home:user-login')
def createPayrollView(request):
    payroll_form = PayrollMasterForm(user=request.user)
    if request.method == 'POST':
        payroll_form = PayrollMasterForm(request.POST,user=request.user)
        if payroll_form.is_valid():
            master_object = payroll_form.save(commit=False)
            master_object.enterprise = request.user.company
            master_object.created_by_id = request.user.id
            master_object.last_update_by_id = request.user.id
            master_object.save()
            return redirect('manage_payroll:list-payroll')
            success_msg = _('Payroll Created Successfully')
            messages.success(request, success_msg)
        else:
            print(payroll_form.errors)
    payContext = {
        "page_title": _("Create Payroll"),
        'pay_form': payroll_form
    }
    return render(request, 'create-payroll.html', payContext)


@login_required(login_url='home:user-login')
def updatePayrollView(request, pk):
    required_payroll = get_object_or_404(Payroll_Master, pk=pk)
    pay_form = PayrollMasterForm(instance=required_payroll,user=request.user)
    if request.method == 'POST':
        pay_form = PayrollMasterForm(request.POST, instance=required_payroll,user=request.user)
        if pay_form.is_valid():
            pay_form.save()
        return redirect('manage_payroll:list-payroll')
        success_msg = _('Payroll Created Successfully')
        messages.success(request, success_msg)
    payContext = {
        "page_title":_("Update Payroll") ,
        'pay_form': pay_form
    }
    return render(request, 'create-payroll.html', payContext)


@login_required(login_url='home:user-login')
def deletePayrollView(request, pk):
    required_payroll = get_object_or_404(Payroll_Master, pk=pk)
    try:
        payroll_form = PayrollMasterForm(instance=required_payroll,user=request.user)
        payroll_obj = payroll_form.save(commit=False)
        payroll_obj.end_date = date.today()
        payroll_obj.save(update_fields=['end_date'])
        user_lang=to_locale(get_language())
        if user_lang=='ar':
            success_msg = '{}تم حذف'.format(required_payroll)
        else:
            success_msg = '{} was deleted successfully'.format(required_payroll)
        # success_msg = '{} was deleted successfully'.format(required_payroll)
        messages.success(request, success_msg)
    except Exception as e:
        user_lang=to_locale(get_language())
        if user_lang=='ar':
            error_msg = '{} لم يتم حذف '.format(required_payroll)
        else:
            error_msg = '{} cannot be deleted '.format(required_payroll)
        # error_msg = '{} cannot be deleted '.format(required_payroll)
        messages.error(request, error_msg)
        raise e
    return redirect('manage_payroll:list-payroll')
####################################################################
@login_required(login_url='home:user-login')
def export_cash_report(request):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Cash Report.xls"'

    employees_without_bank = list(Payment.objects.filter(bank_name__isnull=True, account_number__isnull=True,emp_id__enterprise= request.user.company).filter(
    Q(emp_id__emp_end_date__gte=date.today()) | Q(emp_id__emp_end_date__isnull=True)).values_list("emp_id",flat=True))        
    now = datetime.now()
    year = now.year
    month = now.month
    salary_obj = Salary_elements.objects.filter(emp__in = employees_without_bank, salary_month=month,
    salary_year=year)


    wb = xlwt.Workbook(encoding='utf-8')
    ws = wb.add_sheet('Cash Report')

    # Sheet header, first row
    row_num = 0

    font_style = xlwt.XFStyle()
    font_style.font.bold = True

    columns = [ 'Person Code','Person Number','Position','Location','Department','Division','Net Salary','Signature',]

    for col_num in range(len(columns)):
        ws.write(row_num, col_num, columns[col_num], font_style)

    # Sheet body, remaining rows
    font_style = xlwt.XFStyle()

    emp_list = []
    for emp in salary_obj:
        try:
            last_jobroll = JobRoll.objects.get(emp_id = emp,end_date__isnull=True)
        except JobRoll.DoesNotExist:
            last_jobroll = JobRoll.objects.filter(emp_id = emp).filter(Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).last()

        emp_dic = []
        emp_dic.append(emp.emp.emp_number)
        emp_dic.append(emp.emp.emp_number)
        emp_dic.append(last_jobroll.position.position_name)
        emp_dic.append('')
        emp_dic.append(last_jobroll.department.dept_name)
        emp_dic.append('')
        emp_dic.append(emp.net_salary)
        emp_dic.append('')
        emp_list.append(emp_dic)
    for row in emp_list:
        row_num += 1
        for col_num in range(len(row)):
            ws.write(row_num, col_num, row[col_num], font_style)
    wb.save(response)
    return response




@login_required(login_url='home:user-login')
def get_bank_report(request):
    user_group = request.user.groups.all()[0].name 
    salary_form = SalaryElementForm(user=request.user)
    payment_form = PaymentForm() 
    payment_form.fields['bank_name'].queryset = Bank_Master.objects.filter(
            enterprise=request.user.company).filter(
            Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
    payment_form.fields['bank_name'].required = 'required'
    
    if user_group == 'mena':
        emp_salry_structure = EmployeeStructureLink.objects.filter(salary_structure__enterprise=request.user.company,
                            salary_structure__created_by=request.user,end_date__isnull=True).values_list("employee", flat=True)
        employess = Employee.objects.filter(id__in=emp_salry_structure,enterprise=request.user.company).filter(
            (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number") 
    else:
        employess =Employee.objects.filter(enterprise=request.user.company).filter(
            (Q(emp_end_date__gte=date.today()) | Q(emp_end_date__isnull=True))).order_by("emp_number")       
    
    if request.method == 'POST':
        bank_id = request.POST.get('bank_name',None)
        year = request.POST.get('salary_year',None)
        
        month_in_words = request.POST.get('month')
        month=strptime(month_in_words,'%b').tm_mon 

        from_emp = request.POST.get('from_emp')
        if len(from_emp) == 0: 
            from_emp = 0
        to_emp = request.POST.get('to_emp')
        if len(to_emp) == 0: 
            to_emp = 0
        return redirect('manage_payroll:export-bank-report',bank_id=bank_id,
                month=month,year=year,from_emp =from_emp,to_emp=to_emp )  


    myContext = {
        "salary_form": salary_form,
        "employess":employess,
        'payment_form':payment_form,
    }
    return render(request, 'export-bank-report.html', myContext)




    
    
@login_required(login_url='home:user-login')
def export_bank_report(request,bank_id,month,year,from_emp,to_emp):
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="Bank Report.xls"'
    try:
        bank = Bank_Master.objects.get(id = bank_id)
        employees_with_bank = list(Payment.objects.filter(bank_name= bank , emp_id__enterprise= request.user.company).filter(
            Q(emp_id__emp_end_date__gt=date.today()) | Q(emp_id__emp_end_date__isnull=True)).filter(
                Q(emp_id__terminationdate__gte=date.today())|Q(emp_id__terminationdate__isnull=True)).values_list("emp_id",flat=True)) 
        if from_emp != 0 and to_emp != 0 :       
            salary_obj = Salary_elements.objects.filter(emp__in = employees_with_bank, salary_month=month,salary_year=year).filter(
                emp__emp_number__gte=from_emp,emp__emp_number__lte=to_emp)
        else :
           salary_obj = Salary_elements.objects.filter(emp__in = employees_with_bank, salary_month=month,salary_year=year)

        wb = xlwt.Workbook(encoding='utf-8')
        ws = wb.add_sheet('Bank Report')

        # Sheet header, first row
        row_num = 0

        font_style = xlwt.XFStyle()
        font_style.font.bold = True

        columns = [ 'Person Code','Person Number','Branch Code','Bank name','Basic Code','account no.','IBAN No.','salary tran.',]


        for col_num in range(len(columns)):
            ws.write(row_num, col_num, columns[col_num], font_style)

        # Sheet body, remaining rows
        font_style = xlwt.XFStyle()

        emp_list = []
        for emp in salary_obj:
            account = Payment.objects.filter(emp_id=emp.emp.id).filter(
            Q(end_date__gt=date.today()) | Q(end_date__isnull=True)).last()
            emp_dic = []
            emp_dic.append(emp.emp.emp_number)
            emp_dic.append(emp.emp.emp_name)
            emp_dic.append(account.bank_name.branch_name)
            emp_dic.append(account.bank_name.bank_name)
            emp_dic.append(account.bank_name.basic_code)
            emp_dic.append(account.iban_number)
            emp_dic.append(account.account_number)
            emp_dic.append(emp.net_salary)
            emp_list.append(emp_dic)
        for row in emp_list:
            row_num += 1
            for col_num in range(len(row)):
                ws.write(row_num, col_num, row[col_num], font_style)
        wb.save(response)
        return response
    except Bank_Master.DoesNotExist:
            return redirect('manage_payroll:bank-report')
