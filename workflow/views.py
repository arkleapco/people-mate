from django.shortcuts import render, reverse, redirect
from .forms import ServiceForm, WorkflowInlineFormset
from django.utils.translation import ugettext_lazy as _
from .models import *
from django.contrib import messages
from datetime import datetime
from employee.models import JobRoll
from leave.models import Leave
from service.models import Bussiness_Travel,Purchase_Request


def list_service(request):
    """
    list services with structure
    By: Guehad, amira
    31/3/2021
    """
    services = Service.objects.all()
    context = {
        'page_title': _("Services"),
        'services': services,
    }
    return render(request, 'list_workflow.html', context=context)


def view_structure(request, service_id):
    """
    create service & its structure
    By: Guehad, amira
    31/3/2021
    """
    service = Service.objects.get(id=service_id)
    print(service)
    workflow_inlines = Workflow.objects.filter(service_id=service_id)
    print(workflow_inlines.values())
    context = {
        'page_title': _("View Workflow Structure"),
        'workflow_inlines': workflow_inlines,
        'service': service.service_name.capitalize(),
    }
    return render(request, 'view_structure.html', context=context)



def create_service_and_work_flow(request):
    """
    create service & its structure
    By: Guehad, amira
    31/3/2021
    """
    service_form = ServiceForm()
    workflow_inlines = WorkflowInlineFormset()

    if request.method == 'POST':
        service_form = ServiceForm(request.POST)

        if service_form.is_valid():
            service_obj = service_form.save(commit=False)
            service_exist = Service.objects.filter(service_name=service_obj.service_name)
            if service_exist:
                messages.error(request, _('Service already exist... You can update it instead.'))
                return redirect(reverse('workflow:list_workflow'))
            service_obj.service_created_by = request.user
            service_obj.save()

            workflow_inlines = WorkflowInlineFormset(request.POST, instance=service_obj)

            if workflow_inlines.is_valid():
                print('valid')
                workflow_objs = workflow_inlines.save(commit=False)
                for workflow_obj in workflow_objs:
                    workflow_obj.workflow_created_by = request.user
                    workflow_obj.save()
            else:
                print(workflow_inlines.errors)
            return redirect(reverse('workflow:list_workflow'))

    context = {
        'page_title': _("Create Workflow Structure"),
        'service_form': service_form,
        'workflow_inlines': workflow_inlines
    }
    return render(request, 'create_workflow.html', context=context)


def update_service_workflow(request, service_id):
    """
    update service & its structure
    By: Guehad, amira
    31/3/2021
    """
    service = Service.objects.get(id=service_id)
    service_form = ServiceForm(instance=service)
    workflow_inlines = WorkflowInlineFormset(instance=service)

    if request.method == 'POST':
        workflow_inlines = WorkflowInlineFormset(request.POST, instance=service)

        if workflow_inlines.is_valid():
            workflow_objs = workflow_inlines.save(commit=False)
            for workflow_obj in workflow_objs:
                workflow_obj.workflow_updated_by = request.user
                workflow_obj.updated_at = datetime.now()
                workflow_obj.save()
        return redirect(reverse('workflow:list_workflow'))

    context = {
        'page_title': _("Update Workflow Structure"),
        'service_form': service_form,
        'workflow_inlines': workflow_inlines,
        'service': service.service_name.capitalize(),
    }
    return render(request, 'create_workflow.html', context=context)


def delete_service_workflow(request, service_id):
    """
    delete service & its structure
    By: Guehad, amira
    31/3/2021
    """
    service = Service.objects.get(id=service_id)
    service.delete()
    messages.success(request, _('Structure deleted successfully.'))
    return redirect(reverse('workflow:list_workflow'))


def load_employees(request):
    """
    load employee according to specific position
    :param request:
    :return:
    by: amira
    date: 22/4/2021
    """
    position = request.GET.get('position')
    print(position, '00000')
    job_roll = JobRoll.objects.filter(position=position).values('emp_id')
    print(job_roll)
    employees = Employee.objects.filter(id__in=job_roll)
    print(employees)
    context = {
        'employees': employees
    }
    return render(request, 'employee_dropdown_list_options.html', context)


def render_action(request,type,id):
    print("*****" , id)
    print("########" , type)
    if type == "leave":
        service = Leave.objects.get(id=id)
        return redirect('leave:edit_leave' , id = service, type=type)
    elif type == "travel":
        service = Bussiness_Travel.objects.get(id = id)
        return redirect('workflow:take-action-travel' , id = service.id , type=type)
    elif type == "purchase":
        service = Purchase_Request.objects.get(id=id)
        return redirect('service:purchase-request-update' , id = service, type=type)

    
