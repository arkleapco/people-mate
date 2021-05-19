from django.http import request
from company.models import Enterprise
from .models import *
from notifications.signals import notify
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template import loader
from employee.models import JobRoll
from custom_user.models import User

def email_sender(subject, message, from_email, recipient_list, html_message):
    try:
        send_mail(subject=subject,
                  message=message,
                  from_email=from_email,
                  recipient_list=[recipient_list],
                  fail_silently=False,
                  html_message=html_message)
    except Exception as e:
        print(e)

def message_composer(html_template, service_type , service_request , employee):

    html_message = loader.render_to_string(
        html_template,
        {
           'service_type':service_type,
           'service_request':service_request,
           'employee':employee
        }
    )
    return html_message

class WorkflowStatus:
    def __init__(self,service_request,workflow_type):
        self.service_request = service_request
        self.workflow_type = workflow_type

    def send_workflow_notification(self , seq = 1):
        ''' purpose: send notificaion to target user to notify or ask for action on a specific service
            by: mamdouh & gehad
            date: 25/4/2021
        '''
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type , work_sequence=seq)
        if self.workflow_type == 'leave':
            employee = Employee.objects.get(emp_end_date__isnull=True, user=self.service_request.user)
        elif self.workflow_type == 'travel':
            employee = self.service_request.emp
        elif self.workflow_type == 'purchase':
            employee = self.service_request.ordered_by
        try:
            emp_jobroll = JobRoll.objects.get(end_date__isnull=True, emp_id=employee)
        except ObjectDoesNotExist as e:
            print(e)
        for workflow in workflows:
            if workflow.is_action:
                if workflow.is_manager:
                    if emp_jobroll.manager:
                        recipient = emp_jobroll.manager.user
                    else:
                        recipient = User.objects.filter(groups__name='HR')
                else:
                    if workflow.employee:
                        recipient = workflow.employee.user
                    else:
                        recipient_jobrolls = JobRoll.objects.filter(position=workflow.position)
                        recipient=[]
                        for jobroll in recipient_jobrolls:
                            recipient.append(jobroll.emp_id.user)

                ########## change in href down here and send data in notifications
                if self.workflow_type == "leave":
                    data = {"title": "Leave request","href": "workflow:render-action","type":"leave"}
                elif self.workflow_type == "purchase":
                    data = {"title": "Purchase order request","href": "workflow:render-action", "type":"purchase"}
                elif self.workflow_type == "travel":
                    data = {"title": "Business travel request","href": "workflow:render-action" , "type":"travel"}
                notify.send(sender= employee.user,
                            recipient=recipient,
                            verb='requested',action_object=self.service_request,
                             description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='action',data=data)

                message = "Please, take action for {employee} {self.workflow_type} request."
                subject = "{self.workflow_type} request"
                html_message = message_composer(html_template='take_action.html', service_type=self.workflow_type,
                                    service_request=self.service_request , employee=employee)
                if recipient:
                    if type(recipient) is list:
                        for recipient_user in recipient:
                            email_sender(subject, message, employee.user.email, recipient_user.email,html_message)
                    else:
                        email_sender(subject, message, employee.user.email, recipient.email,html_message)

                            
            elif workflow.is_notify:
                if workflow.is_manager:
                    if emp_jobroll.manager:
                        recipient = emp_jobroll.manager.user
                    else:
                        recipient = User.objects.filter(groups__name='HR')
                else:
                    if workflow.employee:
                        recipient = workflow.employee.user
                        print("yessss")
                    else:
                        recipient_jobrolls = JobRoll.objects.filter(position=workflow.position)
                        recipient=[]
                        for jobroll in recipient_jobrolls:
                            recipient.append(jobroll.emp_id.user)
                        print("******* users: ",recipient)
                if self.workflow_type == "leave":
                    data = {"title": "Leave request","type":"leave"}
                elif self.workflow_type == "purchase":
                    data = {"title": "Purchase order request", "type":"purchase"}
                elif self.workflow_type == "travel":
                    data = {"title": "Business travel request", "type":"travel"}
                notify.send(sender= employee.user,
                            recipient=recipient,
                            verb='requested', description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='notify',data=data)
                message = "Please, take action for {employee} {self.workflow_type} request."
                subject = "{self.workflow_type} request"
                html_message = ""
                if recipient:
                    if type(recipient) is list:
                        for recipient_user in recipient:
                            email_sender(subject, message, employee.user.email, recipient_user.email,html_message)
                    else:
                        email_sender(subject, message, employee.user.email, recipient.email,html_message)
                next_seq=self.get_next_sequence(seq) # next sequence to notify a user in this sequence
                print("yaaaaaaaaaaaaaaaaaa ",next_seq)
                if next_seq:
                    self.send_workflow_notification(next_seq)
                else:
                    self.change_service_overall_status()
             
            


    def create_service_request_workflow(self , action_by , status ,seq = 1):
        ''' purpose: create new record in 'ServiceRequestWorkflow' table after taking an action on service
                    based on sequence
            by: mamdouh
            date: 5/5/2021
        '''
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type , work_sequence=seq)
        employee_action_by = Employee.objects.get(user=action_by , emp_end_date__isnull = True) 
        for workflow in workflows:
            if workflow.is_action:
                workflow_requested_obj = ServiceRequestWorkflow(
                    status=status,
                    workflow=workflow, 
                    action_by=employee_action_by,  
                    created_by=action_by,    
                )
                if self.workflow_type == 'travel':
                    workflow_requested_obj.travel_request = self.service_request
                elif self.workflow_type == 'leave':
                    workflow_requested_obj.leave_request = self.service_request
                elif self.workflow_type == 'purchase':
                    workflow_requested_obj.purchase_request = self.service_request
                workflow_requested_obj.save()
                print("#########" , workflow_requested_obj.status)
                if workflow_requested_obj.status is not 'rejected':
                    next_seq=self.get_next_sequence(seq) # next sequence to notify a user in this sequence
                    print("********" ,next_seq)
                    if next_seq:
                        self.send_workflow_notification(next_seq)
                    else:
                        self.change_service_overall_status()
                else:
                    self.change_service_overall_status()
            
        return True

    def get_next_sequence(self,seq):
        ''' purpose: return next sequence workflow for a specific workflow type
            by: mamdouh
            date: 6/5/2021
        '''
        new_seq = seq + 1
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type , work_sequence=new_seq)
        if not workflows:
            return False
        else:
            return new_seq

    def change_service_overall_status(self):
        ''' purpose: change service status by the end of workflow cycle
            by: mamdouh
            date: 9/5/2021
        '''
        overall_status = 'Approved'
        if self.workflow_type == 'travel':
           service_requests = ServiceRequestWorkflow.objects.filter(travel_request=self.service_request)
        elif self.workflow_type == 'leave':
           service_requests = ServiceRequestWorkflow.objects.filter(leave_request=self.service_request)
        elif self.workflow_type == 'purchase':
           service_requests = ServiceRequestWorkflow.objects.filter(purchase_request=self.service_request)

        print("OOOOOOOOOOOOOOOOOOOOO", service_requests)   
        for request in service_requests:
            if request.status == 'rejected':
               overall_status = 'Rejected'
               break
        print("####" , overall_status)
        self.service_request.status = overall_status
        self.service_request.save()
