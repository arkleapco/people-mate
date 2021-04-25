from .models import *
from notifications.signals import notify
from django.core.exceptions import ObjectDoesNotExist


class WorkflowStatus:
    def __init__(self,service_request,workflow_type, sender):
        self.service_request = service_request
        self.workflow_type = workflow_type
        self.sender = sender

    def get_service_workflows(self):
        workflows = Workflow.objects.filter(service__service_name = self.workflow_type).order_by('work_sequence')
        print(workflows)
        for workflow in workflows:
            print("##### ",workflow.is_notify)
            employee = Employee.objects.get(user=self.sender)
            try:
                emp_jobroll = JobRoll.objects.get(end_date__isnull=True, emp_id=employee)
            except ObjectDoesNotExist as e:
                print(e)
            if workflow.is_action:
                if workflow.is_manager:
                    if emp_jobroll.manager:
                        recipient = emp_jobroll.manager.user
                    else:
                        recipient = User.objects.filter(groups__name='HR')
                    

                    ########## change in href down here and send email and send data in notifications

                    if self.workflow_type == "leave":
                        data = {"title": "Leave request",
                            "href": "leave:edit_leave"}
                    elif self.workflow_type == "purchase":
                        data = {"title": "Purchase order request",
                            "href": "service:edit_leave"}
                    elif self.workflow_type == "travel":
                        data = {"title": "Business travel request",
                            "href": "leave:edit_leave"}
                else:
                    recipient = workflow.employee.user

                notify.send(sender= self.sender,
                            recipient=recipient,
                            verb='requested', description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='notify')

                            
            elif workflow.is_notify:
                if workflow.is_manager:
                    try:
                        emp_jobroll = JobRoll.objects.get(end_date__isnull=True, emp_id=employee)
                    except ObjectDoesNotExist as e:
                        print(e)
                    if emp_jobroll.manager:
                        recipient = emp_jobroll.manager.user
                    else:
                        recipient = User.objects.filter(groups__name='HR')

                    

                    if self.workflow_type == "leave":
                        data = {"title": "Leave request",
                            "href": "leave:edit_leave"}
                    elif self.workflow_type == "purchase":
                        data = {"title": "Purchase order request",
                            "href": "service:edit_leave"}
                    elif self.workflow_type == "travel":
                        data = {"title": "Business travel request",
                            "href": "leave:edit_leave"}
                else:
                    recipient = workflow.employee.user

                notify.send(sender= self.sender,
                            recipient=recipient,
                            verb='requested', description="{sender} has requested {workflow_type}".format(sender=employee,
                                                                                            workflow_type=self.workflow_type),
                             level='notify')
            
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





    




