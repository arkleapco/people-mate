from django.shortcuts import redirect, render
from .models import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from custom_user.models import User
from .forms import *
from django.utils.translation import to_locale, get_language
from django.contrib import messages

################## Messages ##########################################
def success(message_type, obj_type):
    user_lang = to_locale(get_language())
    if message_type == "create":
        if user_lang == 'ar':
            success_msg = '  تم التعديل' + _('obj_type')
        else:
            success_msg = obj_type + ' Created successfully'
    else:
        if user_lang == 'ar':
            success_msg = '  تم الإنشاء' + _('obj_type')
        else:
            success_msg = obj_type +' Updated successfully'

    return success_msg


def fail(message_type,obj_type):
    user_lang = to_locale(get_language())
    if message_type == "create":
        if user_lang == 'ar':
            error_msg = ' لم يتم إنشاء ' + _('obj_type')
        else:
            error_msg = obj_type + ' Cannot be created '
    else:
        if user_lang == 'ar':
            error_msg = ' لم يتم تعديل '  + _('obj_type')
        else:
            error_msg = obj_type + ' Cannot be updated '
    return error_msg


@login_required(login_url='home:user-login')
def list_loan(request):
     loans = Loan.objects.filter(loan_type__loan_type__company = request.user.company)
     context = {
          "loans":loans
     }
     return render(request,'list-loans.html' , context)

@login_required(login_url='home:user-login')
def create_loan(request):
     loan_form = Loan_Form()
     if request.method == "POST":
          loan_form = Loan_Form(request.POST)
          if loan_form.is_valid():
               loan_obj = loan_form.save(commit = False)
               loan_obj.created_by = request.user
               loan_obj.save()

               success_msg = success('create', 'loan')
               messages.success(request, success_msg)
               return redirect('loan:list-loans')
          else:
               fail_msg = fail('create' , 'loan')
               messages.error(request,fail_msg)

     context = {
          'page_title':_('create loan'),
          'loan_form':loan_form
     }
     return render(request , 'create-loan.html', context)