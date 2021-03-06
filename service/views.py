from django.shortcuts import render, redirect
from django.http import HttpResponse
from employee.models import Employee, JobRoll
from service.models import Bussiness_Travel, Purchase_Request
from service.forms import FormAllowance, PurchaseRequestForm, Purchase_Item_formset
from django.db.models import Q
from company.models import Department
from django.shortcuts import get_object_or_404
from django.contrib.auth import authenticate, login, logout  # for later
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.urls import reverse
from django.contrib import messages
from django import forms
from django.core.mail import send_mail
from django.template import loader
from datetime import date, datetime
from workflow.workflow_status import WorkflowStatus
from django.template import Context
from django.template.loader import render_to_string
from weasyprint import HTML, CSS
from weasyprint.fonts import FontConfiguration 


@login_required(login_url='/user_login/')
def services_list(request):
    try:
        request_employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True ,enterprise= request.user.company)
    except Employee.DoesNotExist:
        messages.error(request,"You need to add employee for your user before accessing any service!!")
        return redirect('employee:employee-create' )
    bussiness_travel_list = Bussiness_Travel.objects.filter(emp=request_employee).order_by('-creation_date')
    servicesContext = {
        'services': bussiness_travel_list,
    }
    return render(request, 'list_bussiness_travel.html', servicesContext)


@login_required(login_url='/user_login/')
def services_edit(request, id ,type):
    instance = get_object_or_404(Bussiness_Travel, id=id)
    service_form = FormAllowance(instance=instance)
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    version = instance.version 
    next_version = version + 1
    home = False
    if request.method == "POST":
        service_form = FormAllowance(data=request.POST, instance=instance)
        if service_form.is_valid():
            service = service_form.save(commit=False)
            service.created_by = request.user
            service.last_update_by = request.user
            service.version = next_version
            service.status = 'pending'
            service.save()
            workflow = WorkflowStatus(service, "travel")
            workflow.send_workflow_notification()
            messages.add_message(request, messages.SUCCESS, 'Service was updated successfully')
            return redirect('service:services_list')
        else:
            print(service_form.errors)
    else:  # http request
        service_form = FormAllowance(instance=instance)
        context = {'service_form': service_form}
        home = True
    return render(request, 'edit_allowance.html',
                  context={'service_form': service_form, 'service_id': id, 'employee': employee, 'home': home})


@login_required(login_url='/user_login/')
def services_update(request, id):
    instance = get_object_or_404(Bussiness_Travel, id=id)
    service_form = FormAllowance(instance=instance)
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    if request.method == "POST":
        service_form = FormAllowance(data=request.POST, instance=instance)
        if service_form.is_valid():
            service = service_form.save(commit=False)
            service.created_by = request.user
            service.last_update_by = request.user
            service.total = service.ticket_cost + service.fuel_cost + service.cost + service.cost_per_night
            service.save()
            messages.add_message(request, messages.SUCCESS, 'Service was updated successfully')
            return redirect('service:services_list')
        else:
            print(service_form.errors)
    else:  # http request
        service_form = FormAllowance(instance=instance)
        context = {'service_form': service_form}
    return render(request, 'add_allowance.html', {'service_form': service_form, 'service_id': id, 'employee': employee})


@login_required(login_url='/user_login/')
def services_delete(request, id):
    instance = get_object_or_404(Bussiness_Travel, id=id)
    instance.delete()
    messages.add_message(request, messages.SUCCESS, 'Service was deleted successfully')
    return redirect('service:services_list')


@login_required(login_url='/user_login/')
def services_create(request):
    flag = False
    try:
        employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    except Employee.DoesNotExist:
        messages.error(request,"You need to add employee for your user before accessing any service!!")
        return redirect('employee:employee-create' )
    employee_job = JobRoll.objects.get(end_date__isnull=True, emp_id=employee)
    if request.method == "POST":
        service_form = FormAllowance(data=request.POST)
        if service_form.is_valid():
            service_obj = service_form.save(commit=False)
            service_obj.emp = employee
            service_obj.manager = employee_job.manager
            service_obj.position = employee_job.position
            service_obj.department = employee_job.position.department
            service_obj.created_by = request.user
            service_obj.last_update_by = request.user
            service_obj.total = service_obj.ticket_cost + service_obj.fuel_cost + service_obj.cost + service_obj.cost_per_night
            service_obj.save()
            workflow = WorkflowStatus(service_obj, "travel")
            workflow.send_workflow_notification()
            messages.add_message(request, messages.SUCCESS, 'Service was created successfully')

            # NotificationHelper(employee, employee_job.manager, service_obj).send_notification()

            return redirect('service:services_list')
        else:
            messages.error(request, service_form.errors)
            print(service_form.errors)
    else:  # http request
        service_form = FormAllowance()
    return render(request, 'add_allowance.html', {'service_form': service_form, 'flag': flag})


def send_allowance_notification(request):
    manager = get_object_or_404(Employee, user=request.user.is_authenticated)
    if manager is not None:  # check is signed in user is manager
        pending = Bussiness_Travel.objects.filter(status='pending').order_by('creation_date')
        for request in pending:
            emp = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
        return


@login_required(login_url='home:user-login')
def service_approve(request, service_id,redirect_to):
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    instance = get_object_or_404(Bussiness_Travel, id=service_id)
    instance.status = 'Approved'
    instance.approval = employee
    instance.is_approved = True
    instance.save(update_fields=['status'])
    return redirect('service:services_list')


@login_required(login_url='home:user-login')
def service_unapprove(request, service_id,redirect_to):
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    instance = get_object_or_404(Bussiness_Travel, id=service_id)
    instance.status = 'Rejected'
    instance.is_approved = False
    instance.approval = employee
    instance.save(update_fields=['status'])
    return redirect('service:services_list')


######################################################################################################

@login_required(login_url='/user_login/')
def purchase_request_list(request):
    try:
        request_employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True ,enterprise= request.user.company)
    except Employee.DoesNotExist:
        messages.error(request,"You need to add employee for your user before accessing any service!!")
        return redirect('employee:employee-create' )
    purchase_request_list = Purchase_Request.objects.filter(ordered_by=request_employee).order_by('-creation_date')
    servicesContext = {
        'purchase_request_list': purchase_request_list
    }
    return render(request, 'list_purchase_request.html', servicesContext)


def getOrderSec(n):
    if n < 1:
        return str(1).zfill(5)
    else:
        return str(n + 1).zfill(5)


@login_required(login_url='home:user-login')
def purchase_request_create(request):
    purchase_form = PurchaseRequestForm()
    purchase_form.fields['department'].queryset = Department.objects.filter(
        enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
    purchase_items_form = Purchase_Item_formset()
    rows_num = Purchase_Request.objects.all().count()
    try:
        request_employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    except Employee.DoesNotExist:
        messages.error(request,"You need to add employee for your user before accessing any service!!")
        return redirect('employee:employee-create' )
    employee_job = JobRoll.objects.get(end_date__isnull=True, emp_id=request_employee)
    if request.method == 'POST':
        purchase_form = PurchaseRequestForm(request.POST)
        purchase_items_form = Purchase_Item_formset(request.POST)
        if purchase_form.is_valid() and purchase_items_form.is_valid():
            purchase_obj = purchase_form.save(commit=False)
            purchase_obj.order_number = str(date.today()) + "-" + getOrderSec(rows_num)
            purchase_obj.ordered_by = request_employee
            purchase_obj.created_by = request.user
            purchase_obj.last_update_by = request.user
            purchase_obj.save()
            workflow = WorkflowStatus(purchase_obj, "purchase")
            workflow.send_workflow_notification()
            purchase_items_form = Purchase_Item_formset(request.POST, instance=purchase_obj)
            if purchase_items_form.is_valid():
                purchase_items = purchase_items_form.save(commit=False)
                for item in purchase_items:
                    item.created_by = request.user
                    item.last_update_by = request.user
                    item.save()
            messages.success(request, 'Purchase Request was created successfully')
            return redirect('service:purchase-request-list')
        else:
            messages.error(request, 'Purchase Request was not created')

    purchaseContext = {
        'purchase_form': purchase_form,
        'purchase_items_form': purchase_items_form,

    }
    return render(request, 'create-purchase-order.html', purchaseContext)


@login_required(login_url='home:user-login')
def purchase_request_update(request, id):
    required_request = Purchase_Request.objects.get(pk=id)
    version = required_request.version 
    next_version = version + 1
    purchase_form = PurchaseRequestForm(instance=required_request)
    purchase_items_form = Purchase_Item_formset(instance=required_request)
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    employee_job = JobRoll.objects.get(end_date__isnull=True, emp_id=employee)
    purchase_form.fields['department'].queryset = Department.objects.filter(
        enterprise=request.user.company).filter(Q(end_date__gte=date.today()) | Q(end_date__isnull=True))
    rows_num = Purchase_Request.objects.all().count()
    request_employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    if request.method == 'POST':
        purchase_form = PurchaseRequestForm(request.POST ,instance=required_request)
        purchase_items_form = Purchase_Item_formset(request.POST ,instance=required_request)
        if purchase_form.is_valid():
            purchase_obj = purchase_form.save(commit=False)
            purchase_obj.version = next_version
            purchase_obj.order_number = str(date.today()) + "-" + getOrderSec(rows_num)
            purchase_obj.ordered_by = request_employee
            purchase_obj.created_by = request.user
            purchase_obj.last_update_by = request.user
            purchase_obj.status = 'pending'
            purchase_obj.save()
            purchase_items_form = Purchase_Item_formset(request.POST, instance=purchase_obj)
            if purchase_items_form.is_valid():
                purchase_items = purchase_items_form.save(commit=False)
                for item in purchase_items:
                    item.created_by = request.user
                    item.last_update_by = request.user
                    item.save()
                messages.success(request, 'Purchase Request was updated successfully')  
                workflow = WorkflowStatus(purchase_obj, "purchase")
                workflow.send_workflow_notification()    
            else:
                print(purchase_items_form.errors)           
        else:
            messages.error(request, 'Purchase Request was not updated')
            print(purchase_form.errors)

    purchaseContext = {
        'purchase_form': purchase_form,
        'purchase_items_form': purchase_items_form,
        'order_id': id
    }
    return render(request, 'edit_purchase_request.html', purchaseContext)


@login_required(login_url='home:user-login')
def purchase_request_approve(request, order_id):
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    instance = Purchase_Request.objects.get(pk=order_id)
    instance.status = 'Approved'
    instance.approval = employee
    # instance.is_approved = True
    instance.save(update_fields=['status'])
    return redirect('service:purchase-request-list')


@login_required(login_url='home:user-login')
def purchase_request_unapprove(request, order_id):
    employee = Employee.objects.get(user=request.user, emp_end_date__isnull=True)
    instance = Purchase_Request.objects.get(pk=order_id)
    instance.status = 'Rejected'
    instance.approval = employee
    # instance.is_approved = False
    instance.save(update_fields=['status'])
    return redirect('service:purchase-request-list')

@login_required(login_url='home:user-login')
def render_travel_report(request):
    '''
        By:Mamdouh
        Date: 08/06/2021
        Purpose: print report of travel forms
    '''
    template_path = 'travel-report.html'
    
    approved_travels = Bussiness_Travel.objects.filter(status = 'Approved', emp__enterprise=request.user.company)
    context = {
        'approved_travels': approved_travels,
        'company_name':request.user.company,
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
def render_purchase_orders(request):
    template_path = 'purchase_orders.html'
    purchase_orders = Purchase_Request.objects.filter(status = 'Approved',approval__enterprise=request.user.company)
    context = {
        'purchase_orders': purchase_orders,
        'company' : request.user.company,
    }
    response = HttpResponse(content_type="application/pdf")
    response[
        'Content-Disposition'] = "inline; filename={date}-donation-receipt.pdf".format(
        date=date.today().strftime('%Y-%m-%d'), )
    html = render_to_string(template_path, context)
    font_config = FontConfiguration()
    HTML(string=html).write_pdf(response, font_config=font_config)
    return response
