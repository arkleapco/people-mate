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

def deleted(message_type ,  obj_type):
    user_lang = to_locale(get_language())
    if message_type == "success":
        if user_lang == 'ar':
            msg = 'تم لحذف  ' + _('obj_type')
        else:
            msg = obj_type + ' Deleted successfully'
    else:
        if user_lang == 'ar':
            msg = ' لم يتم حذف ' + _('obj_type')
        else:
            msg = obj_type + ' Cannot be deletd '
    return msg



# loans

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



# loan types

@login_required(login_url='home:user-login')
def list_loan_types(request):
    loan_types_list = LoanType.objects.filter(company=request.user.company, end_date__isnull=True)
    context = {
        'page_title': _('Loan Types List'),
        'loan_types_list': loan_types_list,
    }
    return render(request, 'loan_types/list-loan-types.html', context)


@login_required(login_url='home:user-login')
def loan_type_view(request,pk):
    try:
        loan_type = LoanType.objects.get(id=pk)
    except ObjectDoesNotExist as e:
        return False


    context = {
        'loan_type': loan_type,
        'page_title': _('Loan Types List'),

    }
    return render(request, 'loan_types/view-loan-type.html', context)


@login_required(login_url='home:user-login')
def create_loan_type(request):
     company = request.user.company
     loan_type_form = Loan_Type_Form()
     if request.method == 'POST':
          loan_type_form = Loan_Type_Form(request.POST)
          if loan_type_form.is_valid():
               loan_type_obj = loan_type_form.save(commit=False)
               loan_type_obj.company = company
               loan_type_obj.created_by = request.user
               loan_type_obj.save()

               success_msg = success('create', 'loan type')
               messages.success(request, success_msg)    

               return redirect('loan:loan-types-list')
          else:
               error_msg = fail('create','loan type')
               messages.error(request, error_msg)     
               print(loan_type_form.errors)

               return redirect('loan:loan-type-list')
     else:
          myContext = {
          "page_title": _("Create Loan"),
          "loan_type_form": loan_type_form,
     }

     return render(request, 'loan_types/create-loan-type.html', myContext)

@login_required(login_url='home:user-login')
def update_loan_type(request, pk):
     loan_type = LoanType.objects.get(id=pk)
     company = request.user.company
     loan_type_form = Loan_Type_Form(instance=loan_type)
     if request.method == 'POST':
          loan_type_form = Loan_Type_Form(request.POST, instance=loan_type)
          if loan_type_form.is_valid() :
               loan_type_obj = loan_type_form.save(commit=False)
               loan_type_obj.last_update_by = request.user
               loan_type_obj.company = company
               loan_type_obj.save()

               success_msg = success('update', 'loan type')
               messages.success(request, success_msg)  

               return redirect('loan:update-loan-type',
                    pk = loan_type_obj.id)

          else:
               error_msg = fail('update', 'loan type')
               messages.error(request, error_msg)     
               print(loan_type_form.errors)
               return redirect('loan:update-loan-type',
                    pk = pk)

              
     else:
          myContext = {
          "page_title": _("Update Loan Type"),
          "loan_type_form": loan_type_form,
     }
     return render(request, 'loan_types/create-loan-type.html', myContext)


@login_required(login_url='home:user-login')
def delete_loan_type(request, pk):
     try:
          loan_type = LoanType.objects.get(id=pk)
          loan_type.end_date = date.today()
          loan_type.save()
          success_msg = deleted("success", 'loan type')
          messages.success(request, success_msg)
    

     except Exception as e:
          error_msg = deleted("failed", 'loan type') + e 
          messages.error(request, error_msg)
          raise e

     return redirect('loan:loan-types-list')


