from django.shortcuts import render, reverse, redirect
from .forms import ServiceForm, WorkflowInlineFormset
from django.utils.translation import ugettext_lazy as _
from .models import *
from django.contrib import messages
from datetime import datetime
from employee.models import JobRoll
from leave.models import Leave
from service.models import Bussiness_Travel,Purchase_Request
from workflow.workflow_status import WorkflowStatus 
from service.models import Purchase_Item


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
    workflow_inlines = WorkflowInlineFormset(form_kwargs={'user': request.user})

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

            workflow_inlines = WorkflowInlineFormset(request.POST, instance=service_obj ,form_kwargs={'user': request.user})

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
    workflow_inlines = WorkflowInlineFormset(instance=service,form_kwargs={'user': request.user})

    if request.method == 'POST':
        workflow_inlines = WorkflowInlineFormset(request.POST, instance=service,form_kwargs={'user': request.user})

        if workflow_inlines.is_valid():
            workflow_objs = workflow_inlines.save(commit=False)
            for workflow_obj in workflow_objs:
                workflow_obj.workflow_updated_by = request.user
                workflow_obj.updated_at = datetime.now()
                workflow_obj.save()
        else:
            messages.error(request,workflow_inlines.errors )
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


def render_action(request,type,id,is_notify,notification_id):
    ''' purpose: render action function based on service type
        by: mamdouh
        date: 2/5/2021
    '''
    notification = request.user.notifications.get(id=notification_id)
    notification.mark_as_read()
    print(id)
    if type == "leave":
        service = Leave.objects.get(id=id)
        return redirect('workflow:take-action-leave' , id = service.id, type=type,is_notify=is_notify)
    elif type == "travel":
        service = Bussiness_Travel.objects.get(id = id)
        return redirect('workflow:take-action-travel' , id = service.id , type=type,is_notify=is_notify)
    elif type == "purchase":
        service = Purchase_Request.objects.get(id=id)
        return redirect('workflow:take-action-purchase' , id = service.id, type=type,is_notify=is_notify)

    
def take_action_travel(request,id,type,is_notify):
    ''' purpose: take action on service travel request due to workflow sequence
        by: mamdouh
        date: 2/5/2021
    '''
    service = Bussiness_Travel.objects.get(id = id)
    employee_action_by = Employee.objects.get(user=request.user , emp_end_date__isnull = True)
    try:
        workflow_action = ServiceRequestWorkflow.objects.get(business_travel=service , action_by=employee_action_by , version=service.version)
        has_action = workflow_action.status
    except Exception as e:
        has_action = False
    if is_notify=="notify":
        has_action = "is_notify" 
    if request.method == "POST":
        try:
            ###### to get the last action taken on this service
            all_previous_workflow_actions = ServiceRequestWorkflow.objects.filter(business_travel=service , version=service.version).order_by('workflow__work_sequence').last()
            seq = all_previous_workflow_actions.workflow.work_sequence
            flag = True
            while flag:  #### to get the current sequence to be sent to function create_service_request_workflow()
                workflows = Workflow.objects.filter(work_sequence=seq,service__service_name='travel')
                if len(workflows) == 0:
                    flag=False
                for workflow in workflows:
                    if workflow.is_notify: ### if notify then this is not the required sequence and try the next sequence
                        seq+=1
                    else:
                        flag = False

        except Exception as e:
            seq = 1
        if 'approve' in request.POST:
            status = "approved"
        elif 'reject' in request.POST:
            status = "rejected"
        workflow_status = WorkflowStatus(service , "travel")
        workflow_status.create_service_request_workflow(request.user , status,seq)
        return redirect('home:homepage')
    context = {
        "service":service,
        "has_action":has_action,
    }
    return render(request , 'travel_service_request.html' , context)

def take_action_leave(request,id,type,is_notify):
    ''' purpose: take action on service travel request due to workflow sequence
        by: mamdouh
        date: 2/5/2021
    '''
    service = Leave.objects.get(id = id)
    employee_action_by = Employee.objects.get(user=request.user , emp_end_date__isnull = True)
    try:
        workflow_action = ServiceRequestWorkflow.objects.get(leave=service , action_by=employee_action_by, version=service.version)
        has_action = workflow_action.status
    except Exception as e:
        has_action = False
    if is_notify=="notify":
        has_action = "is_notify" 
    if request.method == "POST":
        try:
            ###### to get the last action taken on this service
            all_previous_workflow_actions = ServiceRequestWorkflow.objects.filter(leave=service , version=service.version).order_by('workflow__work_sequence').last()
            print(" tryyyy:  " ,all_previous_workflow_actions)
            seq = all_previous_workflow_actions.workflow.work_sequence
            flag = True
            while flag:  #### to get the current sequence to be sent to function create_service_request_workflow()
                workflows = Workflow.objects.filter(work_sequence=seq)
                for workflow in workflows:
                    if workflow.is_notify: ### if notify then this is not the required sequence and try the next sequence
                        seq+=1
                    else:
                        flag = False

        except Exception as e:
            seq = 1
            print(e)
        if 'approve' in request.POST:
            status = "approved"
        elif 'reject' in request.POST:
            status = "rejected"
        workflow_status = WorkflowStatus(service , "leave")
        workflow_status.create_service_request_workflow(request.user , status,seq)
        return redirect('home:homepage')
    context = {
        "service":service,
        "has_action":has_action,
    }
    return render(request , 'leave_service_request.html' , context)

def take_action_purchase(request,id,type,is_notify):
    ''' purpose: take action on service travel request due to workflow sequence
        by: mamdouh
        date: 2/5/2021
    '''
    service = Purchase_Request.objects.get(id = id)
    employee_action_by = Employee.objects.get(user=request.user , emp_end_date__isnull = True)
    purchase_items = Purchase_Item.objects.filter(purchase_request=service)

    try:
        workflow_action = ServiceRequestWorkflow.objects.get(purchase_request=service , action_by=employee_action_by, version=service.version)
        has_action = workflow_action.status
    except Exception as e:
        has_action = False
    if is_notify=="notify":
        has_action = "is_notify" 
    if request.method == "POST":
        try:
            ###### to get the last action taken on this service
            all_previous_workflow_actions = ServiceRequestWorkflow.objects.filter(purchase_request=service, version=service.version).order_by('workflow__work_sequence').last()
            seq = all_previous_workflow_actions.workflow.work_sequence
            flag = True
            while flag:  #### to get the current sequence to be sent to function create_service_request_workflow()
                workflows = Workflow.objects.filter(work_sequence=seq)
                for workflow in workflows:
                    if workflow.is_notify: ### if notify then this is not the required sequence and try the next sequence
                        seq+=1
                    else:
                        flag = False

        except Exception as e:
            seq = 1
            print(e)
        if 'approve' in request.POST:
            status = "approved"
        elif 'reject' in request.POST:
            status = "rejected"
        workflow_status = WorkflowStatus(service , "purchase")
        workflow_status.create_service_request_workflow(request.user , status,seq)
        return redirect('home:homepage')
    context = {
        "service":service,
        "purchase_items":purchase_items,
        "has_action":has_action,
    }
    return render(request , 'purchase_service_request.html' , context)