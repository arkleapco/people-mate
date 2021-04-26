from .models import *
from notifications.signals import notify
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.template import loader
from employee.models import JobRoll

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
    def __init__(self,service_request,workflow_type, sender):
        self.service_request = service_request
        self.workflow_type = workflow_type
        self.sender = sender

    def send_workflow_notification(self , seq = 1):
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type , work_sequence=seq)
        employee = Employee.objects.get(user=self.sender ,emp_end_date__isnull=True)
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
                    recipient = workflow.employee.user

                ########## change in href down here and send data in notifications
                if self.workflow_type == "leave":
                    data = {"title": "Leave request",
                        "href": "leave:edit_leave"}
                elif self.workflow_type == "purchase":
                    data = {"title": "Purchase order request",
                        "href": "service:services_edit id={self.service_request.id}"}
                elif self.workflow_type == "travel":
                    data = {"title": "Business travel request",
                        "href": "service:services_edit"}

                notify.send(sender= self.sender,
                            recipient=recipient,
                            verb='requested', description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='notify',data=data)

                message = "Please, take action for {employee} {self.workflow_type} request."
                subject = "{self.workflow_type} request"
                html_message = message_composer(html_template='take_action.html', service_type=self.workflow_type,
                                    service_request=self.service_request , employee=employee)
                email_sender(subject, message, self.sender.email, recipient.email,html_message)

                            
            elif workflow.is_notify:
                if workflow.is_manager:
                    if emp_jobroll.manager:
                        recipient = emp_jobroll.manager.user
                    else:
                        recipient = User.objects.filter(groups__name='HR')
                else:
                    recipient = workflow.employee.user

                notify.send(sender= self.sender,
                            recipient=recipient,
                            verb='requested', description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='notify')
                message = "Please, take action for {employee} {self.workflow_type} request."
                subject = "{self.workflow_type} request"
                html_message = ""
                email_sender(subject, message, self.sender.email, recipient.email,html_message)
             
            


    def create_service_request_workflow(self):
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type).order_by('work_sequence')
        print(workflows)
        employee = Employee.objects.get(user=self.sender)
        for workflow in workflows:
            workflow_requested_obj = ServiceRequestWorkflow(
                employee = employee,
                status='pending',
                workflow=workflow,       
            )
            workflow_requested_obj.save()





    




