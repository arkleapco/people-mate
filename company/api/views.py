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



user_name = 'cec.hcm'
password = '12345678'


@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_company(request):
     params = {"onlyData": "true"}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/hcmBusinessUnitsLOV?onlyData=true'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     return redirect('company:list-company-information')




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_department(request):
     params = {"onlyData": "true","limit":10000,"q":"ClassificationCode=DEPARTMENT"}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/organizations?limit=10000&onlyData=true&q=ClassificationCode=DEPARTMENT'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     companies =  Enterprise.objects.all()
     departments = []
     for company in companies:
          try:
               for item in response.json()["items"]:
                    department_obj = Department(
                         enterprise = company,
                         department_user = request.user, 
                         dept_name = item['Name'],
                         dept_arabic_name = item['Name'],
                         oracle_erp_id = item['OrganizationId'],
                         start_date = item['EffectiveStartDate'] ,
                         end_date = item['EffectiveEndDate'],
                         created_by = request.user, 
                         creation_date = item['CreationDate'],
                         last_update_by = request.user, 
                         last_update_date = item['LastUpdateDate'],
                    )
                    department_obj.save()
          except Exception as e:
               print(e)
               departments.append(item['Name'])
     if len(departments) != 0:     
          error_msg = "this departments cannot be created" + departments
          messages.error(request,error_msg)
     else:
          success_msg = "departments imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-department')





@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_job(request):
     params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/jobs?onlyData=true&limit=1000'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     companies =  Enterprise.objects.all()
     jobs = []
     for company in companies:
          try:
               for item in response.json()["items"]:
                    job_obj = Job(
                         enterprise = company,
                         job_user = request.user, 
                         job_name = item['Name'],
                         job_arabic_name = item['Name'],
                         oracle_erp_id = item["300000002423273"],
                         start_date = item['EffectiveStartDate'] ,
                         end_date = item['EffectiveEndDate'],
                         created_by = request.user, 
                         creation_date = item['CreationDate'],
                         last_update_by = request.user, 
                         last_update_date = item['LastUpdateDate'],
                    )
                    job_obj.save()
          except Exception as e:
               print(e)
               jobs.append(item['Name'])
     if len(jobs) != 0:     
          error_msg = "this jobs cannot be created" + jobs
          messages.error(request,error_msg)
     else:
          success_msg = "jobs imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-jobs')

          




@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_grade(request):
     params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/grades?onlyData=true&limit=10000'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     companies =  Enterprise.objects.all()
     grades = []
     for company in companies:
          try:
               for item in response.json()["items"]:
                    grade_obj = Grade(
                         enterprise = company,
                         grade_user = request.user, 
                         grade_name = item['GradeName'],
                         grade_arabic_name = item['GradeName'],
                         oracle_erp_id = item["GradeId"],
                         start_date = item['EffectiveStartDate'] ,
                         end_date = item['EffectiveEndDate'],
                         created_by = request.user, 
                         creation_date = item['CreationDate'],
                         last_update_by = request.user, 
                         last_update_date = item['LastUpdateDate'],
                    )
                    grade_obj.save()
          except Exception as e:
               print(e)
               grades.append(item['GradeName'])
     if len(grades) != 0:     
          error_msg = "this grades cannot be created" + grades
          messages.error(request,error_msg)
     else:
          success_msg = "grades imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-grades')






@api_view(['GET',])
@permission_classes([IsAuthenticated])
def list_position(request):
     params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/positions?onlyData=true&limit=10000'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     companies =  Enterprise.objects.all()
     positions= []
     for company in companies:
          try:
               for item in response.json()["items"]:
                    try:
                         company = Enterprise.objects.get(oracle_erp_id=item['BusinessUnitId'])
                         department = Department.objects.get(oracle_erp_id=item["DepartmentId"],enterprise=company)
                         job = Job.objects.get(oracle_erp_id=item["JobId"],enterprise=company)
                    except Enterprise.DoesNotExist:
                         data = {"success": False, "data": "there is no company with this id "}
                         return Response(data)
                    position_obj = Position(
                         job = job,
                         department = department,
                         position_name = item['Name'], 
                         position_arabic_name = item["Name"],
                         oracle_erp_id = item["PositionId"],
                         start_date = item['EffectiveStartDate'] ,
                         end_date = item['EffectiveEndDate'],
                         created_by = request.user, 
                         creation_date = item['CreationDate'],
                         last_update_by = request.user, 
                         last_update_date = item['LastUpdateDate'],
                    )
                    position_obj.save()
          except Exception as e:
               print(e)
               positions.append(item['Name'])
     if len(positions) != 0:     
          error_msg = "this positions cannot be created" + positions
          messages.error(request,error_msg)
     else:
          success_msg = "positions imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-positions')

