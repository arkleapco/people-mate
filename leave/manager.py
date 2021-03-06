from django.db import models
import datetime

from django.http import request


class LeaveManager(models.Manager):
	def get_queryset(self):
		'''
		overrides objects.all()
		return all leaves including pending or approved
		'''
		return super().get_queryset()

	def all_pending_leaves(self, user):
		'''
		gets all pending leaves -> Leave.objects.all_pending_leaves()
		'''
		return super().get_queryset().filter(status = 'pending',enterprise=user.company).order_by('creation_date')# applying FIFO

	def all_cancel_leaves(self,user):
		return super().get_queryset().filter(status = 'cancelled',enterprise=user.company).order_by('creation_date')

	def all_rejected_leaves(self,user):
		return super().get_queryset().filter(status = 'rejected',enterprise=user.company).order_by('creation_date')

	def all_approved_leaves(self):
		'''
		gets all approved leaves -> Leave.objects.all_approved_leaves()
		'''
		return super().get_queryset().filter(status = 'approved')

	def current_year_leaves(self):
		'''
		returns all leaves in current year; Leave.objects.all_leaves_current_year()
		or add all_leaves_current_year().count() -> int total
		this include leave approved,pending,rejected,cancelled

		'''
		return super().get_queryset().filter(startdate__year = datetime.date.today().year)
