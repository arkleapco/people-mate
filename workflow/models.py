from django.db import models

# Create your models here.
from django.db import models
from django.utils.translation import ugettext_lazy as _
from employee.models import Employee
from company.models import Position
from django.conf import settings


class Service(models.Model):
    """
    to identify certain service
    By: amira, Guehad
    date: 30/3/2021
    """
    SERVICE_NAME = [
        ('leave', _('Leave')),
        ('purchase', _('Purchase')),
        ('travel', _('Travel'))
    ]
    service_name = models.CharField(max_length=10, choices=SERVICE_NAME)
    service_created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                           blank=True, null=True, related_name='service_created_by')
    created_at = models.DateField(auto_now=True)
    service_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                          blank=True, null=True, related_name='service_last_updated_by')
    updated_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.service_name


class Workflow(models.Model):
    """
    basic workflow structure
    by: Guehad, amira
    date: 30/3/2021
    """
    OPERATION_OPTIONS = [
        ('next_must_approve', _('Next Must Approve')),
        ('next_may_approve', _('Next May Approve'))
    ]
    is_manager = models.BooleanField(default=True)  # go to manager directly
    is_action = models.BooleanField(default=False)  # needs approve
    is_notify = models.BooleanField(default=False)  # only inform
    work_sequence = models.IntegerField(null=False, default=1)  # sequence of actions to be taken
    # to check the sequence and or or
    operation_options = models.CharField(choices=OPERATION_OPTIONS, null=True, blank=True, max_length=5)

    service = models.ForeignKey(Service, on_delete=models.CASCADE)
    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, null=True)
    position = models.ForeignKey(Position, on_delete=models.CASCADE, null=False)
    workflow_created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                            blank=True, null=True, related_name='workflow_created_by')
    created_at = models.DateField(auto_now=True)
    workflow_update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                           blank=True, null=True, related_name='workflow_last_updated_by')
    updated_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return f'{self.service.service_name, self.position.position_name}'


class ServiceRequestWorkflow(models.Model):
    """
        connecting workflow and employee
        by: Guehad, amira, mamdouh
        date: 20/4/2021
    """
    STATUS = [
        ('pending', _('Pending')),
        ('approved', _('Approved')),
        ('rejected', _('Rejected')),
    ]
    service_name = models.CharField(max_length=10)
    status = models.CharField(max_length=25, choices=STATUS)
    reason = models.TextField(null=True, blank=True)

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE)  # employee who requested service
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)

    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                   blank=True, null=True, related_name='service_workflow_created_by')
    created_at = models.DateField(auto_now=True)
    update_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
                                  blank=True, null=True, related_name='service_workflow_last_updated_by')
    updated_at = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.service_name
