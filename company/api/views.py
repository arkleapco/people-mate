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
from custom_user.models import UserCompany
from rest_framework.permissions import IsAuthenticated 
from django.db import IntegrityError
from django.contrib import messages
from django.db.models import Count
from datetime import datetime
from custom_user.models import User
from django.contrib.auth.decorators import login_required




user_name = 'cec.hcm'
password = '12345678'
companies =  Enterprise.objects.all()
companies_orcale_values = list(companies.values_list("oracle_erp_id",flat=True))
companies_list = []
companies_not_assigened = []
########
departments_list = []
########
jobs_list = []
#######
grades_list=[]
#######
position_list = []
positions_without_jobs = []
positions_without_departments = []
######



def convert_date(date_time):
     date = date_time
     date_splited = date.split('T', 1)[0] # take only date from datetime syt
     string_date = ''.join(date_splited) #convert it from list to str 
     date_obj = datetime.strptime(string_date, '%Y-%m-%d')
     return date_obj


#################################### Company ################################################################
def assigen_company_to_user(request,company):
     try:
          user_company_obj = UserCompany(
                         user = request.user,
                         company = company,
                         active = False,
                         created_by = request.user,
                         creation_date = date.todat(),
                         last_update_by = request.user,
                         last_update_date = date.todat()
          )
          user_company_obj.save()
     except Exception as e:
          print(e)
          companies_not_assigened.append(company.name)

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
               companies_list.append(company["Name"])
               

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
          companies_list.append(company["Name"],)
     assigen_company_to_user(request,company_obj)
     

def check_company_is_exist(request,company):
     if str(company["BusinessUnitId"]) in companies_orcale_values:
          update_company(request,company)
     else:
          create_company(request,company)


def get_company_response():
     params = {"onlyData": "true"}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/hcmBusinessUnitsLOV?onlyData=true'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_companies =  response.json()["items"] 
     return orcale_companies

@login_required(login_url='home:user-login')
def list_company(request):
     orcale_companies =  get_company_response()
     if len(orcale_companies) != 0:
          for item in orcale_companies:
               check_company_is_exist(request,item)
     
     if len(companies_list) != 0 :
          companies_list_str = ', '.join(companies_list) 
          company_msg = companies_list_str + "this companies with this oracle_erp id cannot be created or updated  "     
          if  companies_not_assigened != 0:
               companies_not_assigened_str = ', '.join(companies_not_assigened) 
               company_assigen_msg = companies_not_assigened_str   + "this companies cannot be assigen to you   "  
               error_msg = company_msg + company_assigen_msg
          else:
               error_msg = company_msg 

          messages.error(request,error_msg)
     else:
          success_msg = "companies imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-company-information')

################################################## Department ##########################################################
def update_department(user,department,company):
     old_department = Department.objects.get(oracle_erp_id= department['OrganizationId'], enterprise = company)
     date_time = department['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          old_department.department_user = user
          old_department.dept_name = department['Name']
          old_department.dept_arabic_name = department['Name']
          old_department.start_date = department['EffectiveStartDate']
          old_department.end_date = department['EffectiveEndDate']
          old_department.last_update_by = user
          old_department.last_update_date = date_obj
          old_department.creation_date = date.today()
          old_department.save()
     except Exception as e:
          print(e)
          departments_list.append(department['Name'])


def create_department(user,department,company):
     date_time = department['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          department_obj = Department(
                    enterprise = company,
                    department_user = user, 
                    dept_name = department['Name'],
                    dept_arabic_name = department['Name'],
                    oracle_erp_id = department['OrganizationId'],
                    start_date = department['EffectiveStartDate'] ,
                    end_date = department['EffectiveEndDate'],
                    created_by = user, 
                    creation_date = date.today(),
                    last_update_by = user, 
                    last_update_date = date_obj
          )
          department_obj.save()
     except Exception as e:
          print(e)
          departments_list.append(department['Name'])

def check_department_is_exist(user,department,company):
     departments_orcale_values = list(Department.objects.filter(enterprise = company).values_list("oracle_erp_id",flat=True))
     if str(department['OrganizationId']) in departments_orcale_values:
          update_department(user,department,company)
     else:
          create_department(user,department,company)


def get_department_response():
     orcale_departments = Department.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_departments) !=0:
          last_updated_departments = orcale_departments.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"onlyData": "true","limit":10000,"q":"ClassificationCode=DEPARTMENT;LastUpdateDate >{}".format(last_updated_departments)}
     else:
          params = {"onlyData": "true","limit":10000,"q":"ClassificationCode=DEPARTMENT"}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/organizations'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_departments =  response.json()["items"] 
     return orcale_departments


@login_required(login_url='home:user-login')
def list_department(request):
     orcale_departments = get_department_response()
     if len(orcale_departments) != 0:
          for company in companies:
               for department in orcale_departments:
                    check_department_is_exist(request.user,department, company)
     
     if len(departments_list) != 0:
          departments_not_assigened_str = ', '.join(departments_list) 
          error_msg = "thises departments cannot be created" + departments_not_assigened_str
          messages.error(request,error_msg)
     else:
          success_msg = "departments imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-department')


################################################## Job ##########################################################
def update_job(user,job,company):
     old_job = Job.objects.get(oracle_erp_id= job['JobId'], enterprise = company)
     date_time = job['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          old_job.enterprise = company
          old_job.job_user = user
          old_job.job_name = job['Name']
          old_job.job_arabic_name = job['Name']
          old_job.oracle_erp_id = job["JobId"]
          old_job.start_date = job['EffectiveStartDate']
          old_job.end_date = job['EffectiveEndDate']
          old_job.creation_date = date.today()
          old_job.last_update_by = user
          old_job.last_update_date = date_obj
     except Exception as e:
          print(e)
          jobs_list.append(job['Name'])


def create_job(user,job,company):
     date_time = job['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          job_obj = Job(
               enterprise = company,
               job_user = user, 
               job_name = job['Name'],
               job_arabic_name = job['Name'],
               oracle_erp_id = job["JobId"],
               start_date = job['EffectiveStartDate'] ,
               end_date = job['EffectiveEndDate'],
               created_by = user, 
               creation_date = date.today(),
               last_update_by = user, 
               last_update_date = date_obj,
          )
          job_obj.save()
     except Exception as e:
          print(e)
          jobs_list.append(job['Name'])

def check_job_is_exist(user,job,company):
     jobs_orcale_values = list(Job.objects.filter(enterprise = company).values_list("oracle_erp_id",flat=True))
     if str(job['JobId']) in jobs_orcale_values:
          update_job(user,job,company)
     else:
          create_job(user,job,company)

def get_job_response():
     orcale_jobs = Job.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_jobs) !=0:
          last_updated_jobs = orcale_jobs.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"onlyData": "true","limit":10000,"q":"LastUpdateDate >{}".format(last_updated_jobs)}
     else:
          params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/jobs'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_jobs =  response.json()["items"] 
     return orcale_jobs



@login_required(login_url='home:user-login')
def list_job(request):
     orcale_jobs = get_job_response()
     if len(orcale_jobs) != 0:
          for company in companies:
               for job in orcale_jobs:
                    check_job_is_exist(request.user,job, company)
     
     if len(jobs_list) != 0:
          jobs_not_assigened_str = ', '.join(jobs_list) 
          error_msg = "thises jobs cannot be created or updated" + jobs_not_assigened_str
          messages.error(request,error_msg)
     else:
          success_msg = "jobs imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-jobs')


    
################################################## Grade ##########################################################
def update_grade(user,job,company):
     old_grade = Grade.objects.get(oracle_erp_id= job["GradeId"], enterprise = company)
     date_time = job['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          old_grade.grade_user = user
          old_grade.grade_name = job['GradeName']
          old_grade.grade_arabic_name = job['GradeName']
          old_grade.oracle_erp_id = job["GradeId"]
          old_grade.start_date = job['EffectiveStartDate']
          old_grade.end_date = job['EffectiveEndDate']
          old_grade.creation_date = job['CreationDate']
          old_grade.last_update_by = user
          old_grade.last_update_date = date_obj
     except Exception as e:
          print(e)
          grades_list.append(job['GradeName'])


def create_grade(user,job,company):
     date_time = job['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          grade_obj = Grade(
                    enterprise = company,
                    grade_user = user, 
                    grade_name = job['GradeName'],
                    grade_arabic_name = job['GradeName'],
                    oracle_erp_id = job["GradeId"],
                    start_date = job['EffectiveStartDate'] ,
                    end_date = job['EffectiveEndDate'],
                    created_by = user, 
                    creation_date = job['CreationDate'],
                    last_update_by = user, 
                    last_update_date = date_obj,
               )
          grade_obj.save()
     except Exception as e:
          print(e)
          grades_list.append(job['GradeName'])

def check_grade_is_exist(user,grade,company):
     greade_orcale_values = list(Grade.objects.filter(enterprise = company).values_list("oracle_erp_id",flat=True))
     if str(grade['GradeId']) in greade_orcale_values:
          update_grade(user,grade,company)
     else:
          create_grade(user,grade,company)

def get_grade_response():
     orcale_grads = Grade.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_grads) !=0:
          last_updated_grads = orcale_grads.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"onlyData": "true","limit":10000,"q":"LastUpdateDate >{}".format(last_updated_grads)}
     else:
          params = {"onlyData": "true","limit":10000}

     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/grades'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_grades =  response.json()["items"] 
     return orcale_grades



@login_required(login_url='home:user-login')
def list_grade(request):
     orcale_grades = get_grade_response()
     if len(orcale_grades) != 0:
          for company in companies:
               for grade in orcale_grades:
                    check_grade_is_exist(request.user,grade, company)
     if len(grades_list) != 0:
          grades_not_assigened_str = ', '.join(grades_list) 
          error_msg = "thises grades cannot be created or updated" + grades_not_assigened_str
          messages.error(request,error_msg)
     else:
          success_msg = "grades imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-grades')


################################################## Position ##########################################################
def get_error_msg():
     error_msg = []
     if len(position_list) != 0:
          position_list_str = ', '.join(position_list) 
          position_msg = position_list_str + "thises positions cannot be created or updated,  " 
          error_msg.append(position_msg)
     if len(positions_without_jobs) != 0:
          positions_without_jobs_str = ', '.join(positions_without_jobs) 
          position_without_jobs_msg = positions_without_jobs_str   + "this positions job id not exist,  "  
          error_msg.append(position_without_jobs_msg)
     if len(positions_without_departments) != 0:
          positions_without_departments_str = ', '.join(positions_without_departments) 
          position_without_departments_msg = positions_without_departments_str   + "this positions department id not exist,  " 
          error_msg.append(position_without_departments_msg)
     return error_msg    
 
          

def get_department(position_name,department_id,company):
     try:
          department = Department.objects.get(oracle_erp_id=department_id,enterprise=company)
          return department
     except Department.DoesNotExist:
          positions_without_departments.append(position_name)
          return False



def get_job(position_name,job_id,company):
     try:
          job = Job.objects.get(oracle_erp_id=job_id,enterprise=company)
          return job
     except Job.DoesNotExist:
          positions_without_departments.append(position_name)
          return False


def update_position(user,position,company):
     department = get_department( position['Name'],position['DepartmentId'],company)
     job = get_job(position['Name'],position['JobId'],company)
     if department and job:
          old_position = Position.objects.get(oracle_erp_id= position["PositionId"],job= job, department=department)
          date_time = position['LastUpdateDate']
          date_obj = convert_date(date_time)
          try:
               old_position.job = job
               old_position.department = department
               old_position.position_name = position['Name']
               old_position.position_arabic_name = position["Name"]
               old_position.oracle_erp_id = position["PositionId"]
               old_position.start_date = position['EffectiveStartDate']
               old_position.end_date = position['EffectiveEndDate']
               old_position.creation_date = date.today()
               old_position.last_update_by = user
               old_position.last_update_date = date_obj
               old_position.save()
          except Exception as e:
               print(e)
               position_list.append(position['Name'])



def create_position(user,position,company):
     department = get_department( position['Name'],position['DepartmentId'],company)
     job = get_job(position['Name'],position['JobId'],company)
     if department and job:
          date_time = position['LastUpdateDate']
          date_obj = convert_date(date_time)
          try:
               position_obj = Position(
                    job = job,
                    department = department,
                    position_name = position['Name'], 
                    position_arabic_name = position["Name"],
                    oracle_erp_id = position["PositionId"],
                    start_date = position['EffectiveStartDate'] ,
                    end_date = position['EffectiveEndDate'],
                    created_by = user, 
                    creation_date = date.today(),
                    last_update_by = user, 
                    last_update_date = date_obj
               )
               position_obj.save()
          except Exception as e:
               print(e)
               position_list.append(position['Name'])



def check_position_is_exist(user,position, company):
     Position_orcale_values = list(Position.objects.filter(job= position['JobId'] , department=position['DepartmentId']).values_list("oracle_erp_id",flat=True))
     if str(position['PositionId']) in Position_orcale_values:
          update_position(user,position,company)
     else:
          create_position(user,position,company)


def get_position_response():
     orcale_positions = Position.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_positions) !=0:
          last_updated_positions = orcale_positions.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"onlyData": "true","limit":10000,"q":"LastUpdateDate >{}".format(last_updated_positions)}
     else:
          params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/positions'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_position =  response.json()["items"] 
     return orcale_position



@login_required(login_url='home:user-login')
def list_position(request):
     orcale_position= get_position_response()
     if len(orcale_position) != 0:
          for company in companies:
               for position in orcale_position:
                    check_position_is_exist(request.user,position, company)
     error_msg = get_error_msg()
     if len( error_msg) != 0:
          messages.error(request,error_msg)
     else:
          success_msg = "positions imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-positions')

     

