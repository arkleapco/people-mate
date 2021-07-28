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


# loans

@login_required(login_url='home:user-login')
def list_loans(request):
     loans = Loan.objects.filter(loan_type__company = request.user.company)
     context = {
          "loans":loans
     }
     return render(request,'list-loans.html' , context)

@login_required(login_url='home:user-login')
def create_loan(request):
     loan_form = Loan_Form()
     try:
          employee = Employee.objects.get(user=request.user , emp_end_date__isnull=True)
     except Exception as e:
          print("###### ",e)
     if request.method == "POST":
          loan_form = Loan_Form(request.POST)
          if loan_form.is_valid():
               loan_obj = loan_form.save(commit = False)
               loan_obj.employee = employee
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

@login_required(login_url='home:user-login')
def get_loan(request,id):
     try:
          loan = Loan.objects.get(id=id)
     except ObjectDoesNotExist:
          messages.error("This loan does not exist")
     context = {
          "loan":loan
     }
     return render(request,'get-loan.html' , context)


# loan types

@login_required(login_url='home:user-login')
def list_loan_types(request):
    loan_types_list = LoanType.objects.filter(company=request.user.company, end_date__isnull=True)
    context = {
        'page_title': _('Loan Types List'),
        'loan_types_list': loan_types_list,
    }
    return render(request, 'loan-types-list.html', context)


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
    return render(request, 'loan_type_view.html', context)


@login_required(login_url='home:user-login')
def create_loan_type(request):
     company = request.user.company
     loan_type_form = Loan_Type_Form()
     user_lang = to_locale(get_language())
     if request.method == 'POST':
          loan_type_form = Loan_Type_Form(request.POST)
          if loan_type_form.is_valid():
               loan_type_obj = loan_type_form.save(commit=False)
               loan_type_obj.company = company
               loan_type_obj.created_by = request.user
               loan_type_obj.save()

               if user_lang == 'ar':
                    success_msg = 'تم الانشاء بنجاح'
               else:
                    success_msg = 'Create Successfully'
               messages.success(request, success_msg)     

               return redirect('loan:create-loan-type',
                    pk = loan_type_obj.id)
          else:
               if user_lang == 'ar':
                    errormsg = 'لم تم الانشاء بنجاح'
               else:
                    error_msg = 'Not Created'
               messages.error(request, error_msg)     
               print(loan_type_form.errors)

               return redirect('loan:loan-type-list')
     else:
          myContext = {
          "page_title": _("Create Loan"),
          "loan_type_form": loan_type_form,
     }

     return render(request, 'create-loan-type.html', myContext)

@login_required(login_url='home:user-login')
def update_loan_type(request, pk):
     loan_type = LoanType.objects.get(id=pk)
     company = request.user.company
     loan_type_form = Loan_Type_Form(instance=loan_type)
     user_lang = to_locale(get_language())
     if request.method == 'POST':
          loan_type_form = Loan_Type_Form(request.POST, instance=loan_type)
          if loan_type_form.is_valid() :
               loan_type_obj = loan_type_form.save(commit=False)
               loan_type_obj.last_update_by = request.user
               loan_type_obj.company = company
               loan_type_obj.save()

               if user_lang == 'ar':
                    success_msg = 'تم التعديل بنجاح'
               else:
                    success_msg = 'Updated Successfully'
               messages.success(request, success_msg)     

               return redirect('loan:update-loan-type',
                    pk = loan_type_obj.id)

          else:
               if user_lang == 'ar':
                    errormsg = 'لم يتم  العديل بنجاح'
               else:
                    error_msg = 'Not updated'
               messages.error(request, error_msg)     
               print(loan_type_form.errors)
               return redirect('loan:update-loan-type',
                    pk = pk)

              
     else:
          myContext = {
          "page_title": _("Update Loan Type"),
          "loan_type_form": loan_type_form,
     }
     return render(request, 'update-loan-type.html', myContext)


@login_required(login_url='home:user-login')
def delete_loan_type(request, pk):
     user_lang = to_locale(get_language())
     try:
          loan_type = LoanType.objects.get(id=pk)
          LoanType.end_date = date.today()
          loan_type.save()
          if user_lang == 'ar':
               success_msg = 'تم المسح بنجاح'
          else:
               success_msg = 'Deleted Successfully'
          messages.success(request, success_msg)     

     except Exception as e:
          if user_lang == 'ar':
               errormsg = 'لم يتم  المسج '
          else:
               error_msg = 'Not Dealated'
          messages.error(request, error_msg)
          raise e

     return redirect('loan:loan-type-list')


