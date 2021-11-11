from django.core.checks import messages
from rest_framework.decorators import api_view 
from rest_framework.response import Response
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from rest_framework.permissions import IsAuthenticated 
from rest_framework.decorators import api_view , permission_classes
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from rest_framework.permissions import IsAuthenticated 
from django.db import IntegrityError
from django.contrib import messages
from django.db.models import Count


user_name = 'cec.hcm'
password = '12345678'
companies =  Enterprise.objects.all()
companies_orcale_values = companies.values_list("oracle_erp_id",flat=True)
companies_list = []


#################################### Company ################################################################

def update_company(request,company):
     old_company = Enterprise.objects.get(oracle_erp_id= company["BusinessUnitId"])
     if old_company.name == company["Name"]:
          pass
     else:
          try:
               old_company.name = company["Name"]
               old_company.arabic_name = company["Name"]
               old_company.last_update_by =request.user
               old_company.last_update_date = date.today()
               old_company.save()
          except Exception as e:
               print(e)
               companies_list.append(company["BusinessUnitId"])
               

def create_company(request,company):
     try:
          company_obj = Enterprise(
                    name = company["Name"],
                    arabic_name = company["Name"],
                    oracle_erp_id = company["BusinessUnitId"],
                    last_update_by =request.user,
                    last_update_date = date.today(),
                    created_by = request.user,
                    creation_date = date.today()
                              )
          company_obj.save()                     
     except Exception as e:
          print(e)
          companies_list.append(company["BusinessUnitId"])



def check_company_is_exist(request,company):
     if company["BusinessUnitId"] in companies_orcale_values:
          update_company(request,company)
     else:
          create_company(request,company)


def get_company_response():
     params = {"onlyData": "true"}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/hcmBusinessUnitsLOV?onlyData=true'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_companies =  response.json()["items"] 
     return orcale_companies

@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_company(request):
     print("*********************************",companies_orcale_values)
     orcale_companies =  get_company_response()
     for item in orcale_companies:
          check_company_is_exist(request,item)
     
     if len(companies_list) != 0:
          companies_list_str = ', '.join(companies_list) 
          error_msg = "this companies with this oracle_erp id cannot be created or updated " + companies_list_str
          messages.error(request,error_msg)
     else:
          success_msg = "companies imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-company-information')

################################################## Department ##########################################################

# def check_department_is_exist(request,department):
#      if department["BusinessUnitId"] in companies_orcale_values:
#           update_company(request,company)
#      else:
#           create_company(request,company)



# def get_department_response(request):
#      last_updated_departments = Department.objects.filter(oracle_erp_id__isnull = False).values('last_update_date').annotate(dcount=Count('last_update_date')).order_by('last_update_date').last()["last_update_date"]
#      params = {"onlyData": "true","limit":10000,"q":"ClassificationCode=DEPARTMENT;LastUpdateDate >{}".format(last_updated_departments)}
#      url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/organizations?limit=10000&onlyData=true&q=ClassificationCode=DEPARTMENT'
#      response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
#      orcale_departments =  response.json()["items"] 
#      return orcale_departments
     


# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def list_department(request):
#      orcale_departments = get_department_response()
#      departments = []
#      for company in companies:
#           for department in orcale_departments:
#                check_department_is_exist(request,department)
     
          



# #           # try:
# #           #      for item in orcale_departments:
# #           #           department_obj = Department(
# #           #                enterprise = company,
# #           #                department_user = request.user, 
# #           #                dept_name = item['Name'],
# #           #                dept_arabic_name = item['Name'],
# #           #                oracle_erp_id = item['OrganizationId'],
# #           #                start_date = item['EffectiveStartDate'] ,
# #           #                end_date = item['EffectiveEndDate'],
# #           #                created_by = request.user, 
# #           #                creation_date = item['CreationDate'],
# #           #                last_update_by = request.user, 
# #           #                last_update_date = item['LastUpdateDate'],
# #           #           )
# #           #           department_obj.save()
# #           # except Exception as e:
# #           #      print(e)
# #           #      departments.append(item['Name'])
# #      if len(departments) != 0:     
# #           error_msg = "this departments cannot be created" + departments
# #           messages.error(request,error_msg)
# #      else:
# #           success_msg = "departments imported successfuly " 
# #           messages.success(request, success_msg)
# #      return redirect('company:list-department')





# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def list_job(request):
#      params = {"onlyData": "true","limit":10000}
#      url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/jobs?onlyData=true&limit=1000'
#      response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
#      companies =  Enterprise.objects.all()
#      jobs = []
#      for company in companies:
#           try:
#                for item in response.json()["items"]:
#                     job_obj = Job(
#                          enterprise = company,
#                          job_user = request.user, 
#                          job_name = item['Name'],
#                          job_arabic_name = item['Name'],
#                          oracle_erp_id = item["300000002423273"],
#                          start_date = item['EffectiveStartDate'] ,
#                          end_date = item['EffectiveEndDate'],
#                          created_by = request.user, 
#                          creation_date = item['CreationDate'],
#                          last_update_by = request.user, 
#                          last_update_date = item['LastUpdateDate'],
#                     )
#                     job_obj.save()
#           except Exception as e:
#                print(e)
#                jobs.append(item['Name'])
#      if len(jobs) != 0:     
#           error_msg = "this jobs cannot be created" + jobs
#           messages.error(request,error_msg)
#      else:
#           success_msg = "jobs imported successfuly " 
#           messages.success(request, success_msg)
#      return redirect('company:list-jobs')

          




# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def list_grade(request):
#      params = {"onlyData": "true","limit":10000}
#      url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/grades?onlyData=true&limit=10000'
#      response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
#      companies =  Enterprise.objects.all()
#      grades = []
#      for company in companies:
#           try:
#                for item in response.json()["items"]:
#                     grade_obj = Grade(
#                          enterprise = company,
#                          grade_user = request.user, 
#                          grade_name = item['GradeName'],
#                          grade_arabic_name = item['GradeName'],
#                          oracle_erp_id = item["GradeId"],
#                          start_date = item['EffectiveStartDate'] ,
#                          end_date = item['EffectiveEndDate'],
#                          created_by = request.user, 
#                          creation_date = item['CreationDate'],
#                          last_update_by = request.user, 
#                          last_update_date = item['LastUpdateDate'],
#                     )
#                     grade_obj.save()
#           except Exception as e:
#                print(e)
#                grades.append(item['GradeName'])
#      if len(grades) != 0:     
#           error_msg = "this grades cannot be created" + grades
#           messages.error(request,error_msg)
#      else:
#           success_msg = "grades imported successfuly " 
#           messages.success(request, success_msg)
#      return redirect('company:list-grades')






# @api_view(['GET',])
# @permission_classes([IsAuthenticated])
# def list_position(request):
#      params = {"onlyData": "true","limit":10000}
#      url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/positions?onlyData=true&limit=10000'
#      response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
#      companies =  Enterprise.objects.all()
#      positions= []
#      for company in companies:
#           try:
#                for item in response.json()["items"]:
#                     try:
#                          company = Enterprise.objects.get(oracle_erp_id=item['BusinessUnitId'])
#                          department = Department.objects.get(oracle_erp_id=item["DepartmentId"],enterprise=company)
#                          job = Job.objects.get(oracle_erp_id=item["JobId"],enterprise=company)
#                     except Enterprise.DoesNotExist:
#                          data = {"success": False, "data": "there is no company with this id "}
#                          return Response(data)
#                     position_obj = Position(
#                          job = job,
#                          department = department,
#                          position_name = item['Name'], 
#                          position_arabic_name = item["Name"],
#                          oracle_erp_id = item["PositionId"],
#                          start_date = item['EffectiveStartDate'] ,
#                          end_date = item['EffectiveEndDate'],
#                          created_by = request.user, 
#                          creation_date = item['CreationDate'],
#                          last_update_by = request.user, 
#                          last_update_date = item['LastUpdateDate'],
#                     )
#                     position_obj.save()
#           except Exception as e:
#                print(e)
#                positions.append(item['Name'])
#      if len(positions) != 0:     
#           error_msg = "this positions cannot be created" + positions
#           messages.error(request,error_msg)
#      else:
#           success_msg = "positions imported successfuly " 
#           messages.success(request, success_msg)
#      return redirect('company:list-positions')

