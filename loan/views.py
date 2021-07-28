from django.shortcuts import render , redirect
from .models import *
from django.utils.translation import ugettext_lazy as _
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ObjectDoesNotExist
from custom_user.models import User
from .forms import *
from django.utils.translation import to_locale, get_language
from django.contrib import messages




# Create your views here.

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

               success_msg = success('create', 'loan type')
               messages.success(request, success_msg)    

               return redirect('loan:create-loan-type',
                    pk = loan_type_obj.id)
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
     return render(request, 'update-loan-type.html', myContext)


@login_required(login_url='home:user-login')
def delete_loan_type(request, pk):
     user_lang = to_locale(get_language())
     try:
          loan_type = LoanType.objects.get(id=pk)
          LoanType.end_date = date.today()
          loan_type.save()
          success_msg = deleted("success", 'loan type')
          messages.success(request, success_msg)
    

     except Exception as e:
          error_msg = deleted("failed", 'loan type') + e 
          messages.error(request, error_msg)
          raise e

     return redirect('loan:loan-type-list')


