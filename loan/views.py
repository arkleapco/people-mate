# from django.shortcuts import render
# from .models import *
# from django.utils.translation import ugettext_lazy as _
# from django.contrib.auth.decorators import login_required
# from django.core.exceptions import ObjectDoesNotExist
# from custom_user.models import User
# from .forms import *


# # Create your views here.

# @login_required(login_url='home:user-login')
# def list_loan_types(request):
#     loan_types_list = LoanType.objects.filter(company=request.user.company, end_date__isnull=True)
#     context = {
#         'page_title': _('Loan Types List'),
#         'loan_types_list': loan_types_list,
#     }
#     return render(request, 'loan-types-list.html', context)


# @login_required(login_url='home:user-login')
# def loan_type_view(request,pk):
#     try:
#         loan_type = LoanType.objects.get(id=pk)
#     except ObjectDoesNotExist as e:
#         return False


#     context = {
#         'loan_type': 'loan_type Overview',
#         'page_title': _('Loan Types List'),

#     }
#     return render(request, 'loan_type_view.html', context)


# @login_required(login_url='home:user-login')
# def create_loan_type(request):
#     user = User.objects.get(id=request.user.id)
#     loan_type_form = Loan_Type_Form(user)
#     if request.method == 'POST':
#         loan_type_form = Loan_Type_Form(user, request.POST)
#         if loan_type_form.is_valid():
#           _obj = performance_form.save(commit=False)
#             performance_obj.company = company
#             performance_obj.performance_created_by = request.user
#             performance_obj.save()

#             success_msg = success('create', 'performance')
#             messages.success(request, success_msg)

#             if 'Save and exit' in request.POST:
#                     return redirect('performance:performance-list')
#             elif 'Save and add' in request.POST:
#                     return redirect('performance:create-performance-reate',
#                         per_id = performance_obj.id)
#         else:
#             error_msg = fail('create','performance')
#             messages.error(request, error_msg)

#             print(performance_form.errors)
#             return redirect('performance:performance-list')
#     else:
#         myContext = {
#         "page_title": _("create performance"),
#         "performance_form": performance_form,
#         "company":company,
#     }
#     return render(request, 'create-performance.html', myContext)

# @login_required(login_url='home:user-login')
# def updatePerformance(request, pk):
#     performance = Performance.objects.get(id=pk)
#     user = User.objects.get(id=request.user.id)
#     company = user.company
#     performance_form = PerformanceForm(company, instance=performance)
#     if request.method == 'POST':
#         performance_form = PerformanceForm(company, request.POST, instance=performance)
#         if performance_form.is_valid() :
#             performance_obj = performance_form.save(commit=False)
#             performance_obj.performance_update_by = request.user
#             performance_obj.company = company
#             performance_obj.save()

#             success_msg = success('update', 'performance')
#             messages.success(request, success_msg)

#             if 'Save and exit' in request.POST:
#                     return redirect('performance:performance-list')
#             elif 'Save and add' in request.POST:
#                     return redirect('performance:update-performance-reate',
#                         pk = pk)
#         else:
#             error_msg = fail('update', 'performance')
#             messages.error(request, error_msg)

#             return redirect('performance:performance-edit',pk=pk )
#     else:
#         myContext = {
#         "page_title": _("update performance"),
#         "performance_form": performance_form,
#         "company":company,
#     }
#     return render(request, 'create-performance.html', myContext)

# @login_required(login_url='home:user-login')
# def deletePerformance(request, pk):
#     try:
#         performance = Performance.objects.get(id=pk)
#         performance.end_date = date.today()
#         performance.save()
#         success_msg = deleted("success", 'performance')
#         messages.success(request, success_msg)

#     except Exception as e:
#         error_msg = deleted("failed", 'performance') + e 
#         messages.error(request, error_msg)
#         raise e

#     return redirect('performance:performance-list')


# @login_required(login_url='home:user-login')
# def get_positions_for_department(request):
#     """
#     load jobs and positions according to specific department ajax request
#     :param request:
#     :return:
#     by: gehad
#     date: 3/6/2021
#     """
#     department_id = request.GET.get('department_id')
#     department_obj = Department.objects.get(id=department_id)
#     positions = Position.objects.filter(department=department_obj, end_date__isnull = True)
#     context = {
#         'positions': positions,
#     }
#     return render(request, 'positions_dropdown_list.html', context)


# @login_required(login_url='home:user-login')
# def get_jobs_for_department(request):
#     """
#     load jobs  according to specific department ajax request
#     :param request:
#     :return:
#     by: gehad
#     date: 3/6/2021
#     """
#     department_id = request.GET.get('department_id')
#     department_obj = Department.objects.get(id=department_id)
#     jobs = Position.objects.filter(department=department_obj, end_date__isnull = True).values_list('job__job_name',flat=True)
#     context = {
#         'jobs' : jobs,
#     }
#     return render(request, 'jobs_dropdown_list.html', context)
