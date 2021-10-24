from django.contrib import admin
from .models import *

admin.site.register(Loan)

class LoanTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'company')
admin.site.register(LoanType , LoanTypeAdmin)
admin.site.register(LoanInstallment)