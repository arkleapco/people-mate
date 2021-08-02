from django.contrib import admin
from .models import *

admin.site.register(Loan)
admin.site.register(LoanType)
admin.site.register(LoanInstallment)