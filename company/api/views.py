from django.core.checks import messages
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from custom_user.models import Enterprise
from django.contrib import messages
from django.db.models import Count
from datetime import datetime
from django.contrib.auth.decorators import login_required
from company.models import EnterpriseIntegration
from company.forms import EnterpriseIntegrationForm , JobIntegrationForm , DepartmentIntegrationForm , GradeIntegrationForm , PositionIntegrationForm
from django.shortcuts import redirect
from custom_user.models import UserCompany




user_name = 'cec.hcm'
password = '12345678'
companies =  EnterpriseIntegration.objects.all()
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

def check_status(status):
     if status == "I":
          end_date = date.today()
     if status == "A":
          end_date = None 
     return  end_date   
#################################### Company ################################################################
def assigen_company_to_user(user,company):
     try:
          UserCompany.objects.get(user= user, company=company)
     except UserCompany.DoesNotExist:     
          user_company_obj = UserCompany(
                         user = user,
                         company = company,
                         active = False,
                         created_by = user,
                         creation_date = date.today(),
                         last_update_by = user,
                         last_update_date = date.today()
                         )
          user_company_obj.save()
     except Exception as e:
          print("gggggggggggggggggggggggggg",e)
          companies_not_assigened.append(company.name)

def update_company(user,company):
     old_company = EnterpriseIntegration.objects.get(oracle_erp_id= company["BusinessUnitId"])
     data =  {'name': company["Name"],'oracle_erp_id': company["BusinessUnitId"],
              'status': company["Status"], 'imported_date':datetime.now()} 
     form = EnterpriseIntegrationForm(data, instance=old_company) 
     if form.is_valid():
          form.save()
          enterprise_integration_obj = form.save()
          end_date = check_status(enterprise_integration_obj.status)    
          try :
               old_enterprise = Enterprise.objects.get(oracle_erp_id = enterprise_integration_obj.oracle_erp_id)
               old_enterprise.name = enterprise_integration_obj.name
               old_enterprise.arabic_name = enterprise_integration_obj.name
               old_enterprise.oracle_erp_id = enterprise_integration_obj.oracle_erp_id
               old_enterprise.enterprise_user = user
               old_enterprise.last_update_by =user
               old_enterprise.last_update_date = date.today()
               old_enterprise.save()
               old_enterprise.end_date = end_date 
               old_enterprise.save()
               assigen_company_to_user(user,old_enterprise)
          except Exception as e:
               print("jjjjjjjjjjjjjjjjjjjjjjjjj",e)
               companies_list.append(company["Name"])
               

def create_company(user,company):
     data =  {'name': company["Name"],'oracle_erp_id': company["BusinessUnitId"],
              'status': company["Status"], 'imported_date':datetime.now()} 
     form = EnterpriseIntegrationForm(data) 
     if form.is_valid():
          form.save()
          enterprise_integration_obj = form.save()
          end_date = check_status(enterprise_integration_obj.status )    
          try :
               enterprise_obj = Enterprise(
                    name = enterprise_integration_obj.name,
                    arabic_name = enterprise_integration_obj.name,
                    oracle_erp_id = enterprise_integration_obj.oracle_erp_id,
                    last_update_by =user ,
                    last_update_date = date.today(),
                    enterprise_user =user,
                    created_by =user,
                    creation_date = date.today(),
                    end_date = end_date
                              )
               enterprise_obj.save()
               assigen_company_to_user(user,enterprise_obj)
          except Exception as e:
               print(e)
               companies_not_assigened.append(company["Name"])
     else:
          print(form.errors)
          companies_not_assigened.append(company["Name"])
          

def check_company_is_exist(user,company):
     if str(company["BusinessUnitId"]) in companies_orcale_values:
          update_company(user,company)
     else:
          create_company(user,company)


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
          for company in orcale_companies:
               check_company_is_exist(request.user,company)
     
     company_msg =""
     if len(companies_list) != 0  and  companies_not_assigened != 0:
          companies_list_str = ', '.join(companies_list) 
          company_msg = companies_list_str + "this companies with this oracle_erp id cannot be created or updated  "     
          
          companies_not_assigened_str = ', '.join(companies_not_assigened) 
          company_assigen_msg = companies_not_assigened_str   + "this companies cannot be assigen to you   "  
          error_msg = company_msg + company_assigen_msg
          
          messages.error(request,error_msg)
     else:
          success_msg = "companies imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-company-information')

################################################## Department ##########################################################
def update_department(user,department):
     oracle_old_department = DepartmentIntegration.objects.get(oracle_erp_id= department["BusinessUnitId"])
     data =  {'name': department["Name"],'oracle_erp_id': department["BusinessUnitId"],
              'status': department["Status"], 'start_date' : department["EffectiveStartDate"] , "end_date" :department["EffectiveEndDate"],
              'creation_date' :department["CreationDate"], 'last_update_date' :department["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = DepartmentIntegrationForm(data,  instance=oracle_old_department)
     if form.is_valid():
          form.save()
          department_integration_obj = form.save()
          end_date = check_status(department_integration_obj.status)
          creation_date =  convert_date(department_integration_obj.creation_date) 
          last_update_date = convert_date(department_integration_obj.last_update_date) 
          try :
               old_department = Department.objects.get(oracle_erp_id = department_integration_obj.oracle_erp_id)
               old_department.department_user = user
               old_department.dept_name = department_integration_obj.name
               old_department.dept_arabic_name = department_integration_obj.name
               old_department.start_date = department_integration_obj.start_date
               old_department.end_date = end_date
               old_department.last_update_by = user
               old_department.last_update_date = last_update_date
               old_department.creation_date = creation_date
               old_department.save()
          except Exception as e:
               print(e)
               departments_list.append(department_integration_obj.name)
     else:
          print(form.errors)
          departments_list.append(department["Name"])


def create_department(user,department):
     data =  {'name': department["Name"],'oracle_erp_id': department["OrganizationId"],
              'status': department["Status"], 'start_date' : department["EffectiveStartDate"] , "end_date" :department["EffectiveEndDate"],
              'creation_date' :department["CreationDate"], 'last_update_date' :department["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = DepartmentIntegrationForm(data) 
     if form.is_valid():
          form.save()
          department_integration_obj = form.save()
          end_date = check_status(department_integration_obj.status)
          creation_date =  convert_date(department_integration_obj.creation_date) 
          last_update_date = convert_date(department_integration_obj.last_update_date) 
          try :
               department_obj = Department(
                    department_user = user, 
                    dept_name = department_integration_obj.name,
                    dept_arabic_name = department_integration_obj.name,
                    oracle_erp_id = department_integration_obj.oracle_erp_id,
                    start_date = department_integration_obj.start_date,
                    end_date =end_date,
                    created_by = user,
                    creation_date = creation_date,
                    last_update_by = user,
                    last_update_date = last_update_date,
               )
               department_obj.save()
          except Exception as e:
               print(e)
               departments_list.append(department_integration_obj.name)
     else:        
          print(form.errors)
          departments_list.append(department["Name"])


def check_department_is_exist(user,department):
     departments_orcale_values = list(DepartmentIntegration.objects.all().values_list("oracle_erp_id",flat=True))
     if str(department['OrganizationId']) in departments_orcale_values:
          update_department(user,department)
     else:
          create_department(user,department)


def get_department_response():
     orcale_departments = DepartmentIntegration.objects.all()
     if len(orcale_departments) !=0:
          last_updated_departments = orcale_departments.values('imported_date').annotate(dcount=Count('imported_date')).order_by('imported_date').last()["imported_date"]
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
          for department in orcale_departments:
               check_department_is_exist(request.user,department)
     
     if len(departments_list) != 0:
          departments_not_assigened_str = ', '.join(departments_list) 
          error_msg = "thises departments cannot be created" + departments_not_assigened_str
          messages.error(request,error_msg)
     else:
          success_msg = "departments imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-department')


################################################## Job ##########################################################
def update_job(user,job):
     oracle_old_job= JobIntegrationForm.objects.get(oracle_erp_id= job["JobId"])
     data =  {'name': job["Name"],'oracle_erp_id': job["JobId"],
              'status': job["ActiveStatus"], 'start_date' : job["EffectiveStartDate"] , "end_date" :job["EffectiveEndDate"],
              'creation_date' :job["CreationDate"], 'last_update_date' :job["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = JobIntegrationForm(data,  instance=oracle_old_job)
     if form.is_valid():
          form.save()
          job_integration_obj = form.save()
          end_date = check_status(job_integration_obj.status)
          creation_date =  convert_date(job_integration_obj.creation_date) 
          last_update_date = convert_date(job_integration_obj.last_update_date) 
          try :
               old_job = Job.objects.get(oracle_erp_id = job_integration_obj.oracle_erp_id)
               old_job.department_user = user
               old_job.dept_name = job_integration_obj.name
               old_job.dept_arabic_name = job_integration_obj.name
               old_job.start_date = job_integration_obj.start_date
               old_job.end_date = end_date
               old_job.last_update_by = user
               old_job.last_update_date = last_update_date
               old_job.creation_date = creation_date
               old_job.save()
          except Exception as e:
               print(e)
               departments_list.append(job_integration_obj.name)
     else:
          print(form.errors)
          jobs_list.append(job["Name"])


def create_job(user,job):
     data =  {'name': job["Name"],'oracle_erp_id': job["JobId"],
              'status': job["ActiveStatus"], 'start_date' : job["EffectiveStartDate"] , "end_date" :job["EffectiveEndDate"],
              'creation_date' :job["CreationDate"], 'last_update_date' :job["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = JobIntegrationForm(data) 
     if form.is_valid():
          form.save()
          job_integration_obj = form.save()
          end_date = check_status(job_integration_obj.status)
          creation_date =  convert_date(job_integration_obj.creation_date) 
          last_update_date = convert_date(job_integration_obj.last_update_date) 
          try :
               job_obj = Job(
                    job_user = user, 
                    job_name = job_integration_obj.name,
                    job_arabic_name = job_integration_obj.name,
                    oracle_erp_id = job_integration_obj.oracle_erp_id,
                    start_date = job_integration_obj.start_date,
                    end_date =end_date,
                    created_by = user,
                    creation_date = creation_date,
                    last_update_by = user,
                    last_update_date = last_update_date,
               )
               job_obj.save()
          except Exception as e:
               print(e)
               departments_list.append(job_integration_obj.name)
     else:        
          print(form.errors)
          jobs_list.append(job["Name"])


def check_job_is_exist(user,job):
     job_orcale_values = list(DepartmentIntegration.objects.all().values_list("oracle_erp_id",flat=True))
     if str(job['JobId']) in job_orcale_values:
          update_job(user,job)
     else:
          create_department(user,job)


def get_job_response():
     orcale_jobs = JobIntegration.objects.all()
     if len(orcale_jobs) !=0:
          last_updated_departments = orcale_jobs.values('imported_date').annotate(dcount=Count('imported_date')).order_by('imported_date').last()["imported_date"]
          params = {"onlyData": "true","limit":10000,"q":"LastUpdateDate >{}".format(last_updated_departments)}
     else:
          params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/organizations'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_departments =  response.json()["items"] 
     return orcale_departments


@login_required(login_url='home:user-login')
def list_job(request):
     orcale_jobs = get_job_response()
     if len(orcale_jobs) != 0:
          for job in orcale_jobs:
               check_job_is_exist(request.user,job)
     
     if len(jobs_list) != 0:
          jobs_not_assigened_str = ', '.join(jobs_list) 
          error_msg = "thises jobs cannot be created or updated" + jobs_not_assigened_str
          messages.error(request,error_msg)
     else:
          success_msg = "jobs imported successfuly " 
          messages.success(request, success_msg)
     return redirect('company:list-jobs')
################################################## Grade ##########################################################
def update_grade(user,grade):
     oracle_old_grade= JobIntegrationForm.objects.get(oracle_erp_id= grade["GradeId"])
     data =  {'name': grade["GradeName"],'oracle_erp_id': grade["GradeId"],
              'status': grade["ActiveStatus"], 'start_date' : grade["EffectiveStartDate"] , "end_date" :grade["EffectiveEndDate"],
              'creation_date' :grade["CreationDate"], 'last_update_date' :grade["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = GradeIntegrationForm(data,  instance=oracle_old_grade)
     if form.is_valid():
          form.save()
          grade_integration_obj = form.save()
          end_date = check_status(grade_integration_obj.status)
          creation_date =  convert_date(grade_integration_obj.creation_date) 
          last_update_date = convert_date(grade_integration_obj.last_update_date) 
          try :
               old_grade = Grade.objects.get(oracle_erp_id = grade_integration_obj.oracle_erp_id)
               old_grade.department_user = user
               old_grade.dept_name = grade_integration_obj.name
               old_grade.dept_arabic_name = grade_integration_obj.name
               old_grade.start_date = grade_integration_obj.start_date
               old_grade.end_date = end_date
               old_grade.last_update_by = user
               old_grade.last_update_date = last_update_date
               old_grade.creation_date = creation_date
               old_grade.save()
          except Exception as e:
               print(e)
               grades_list.append(grade_integration_obj.name)
     else:
          print(form.errors)
          grades_list.append(grade["GradeName"])


def create_grade(user,grade):
     data =  {'name': grade["GradeName"],'oracle_erp_id': grade["GradeId"],
              'status': grade["ActiveStatus"], 'start_date' : grade["EffectiveStartDate"] , "end_date" :grade["EffectiveEndDate"],
              'creation_date' :grade["CreationDate"], 'last_update_date' :grade["LastUpdateDate"] ,'imported_date':datetime.now() } 
     form = GradeIntegrationForm(data) 
     if form.is_valid():
          form.save()
          grade_integration_obj = form.save()
          end_date = check_status(grade_integration_obj.status)
          creation_date =  convert_date(grade_integration_obj.creation_date) 
          last_update_date = convert_date(grade_integration_obj.last_update_date) 
          try :
               grade_obj = Grade(
                         grade_user = user, 
                         grade_name = grade_integration_obj.name,
                         grade_arabic_name = grade_integration_obj.name,
                         oracle_erp_id = grade_integration_obj.oracle_erp_id,
                         start_date = grade_integration_obj.start_date,
                         end_date = end_date,
                         created_by = user,
                         creation_date = creation_date,
                         last_update_by = user,
                         last_update_date =last_update_date,
                    )
               grade_obj.save()
          except Exception as e:
               print(e)
               grades_list.append(grade_integration_obj.name)
     else:        
          print(form.errors)
          grades_list.append(grade["GradeName"])

def check_grade_is_exist(user,grade):
     job_grade_values = list(GradeIntegration.objects.all().values_list("oracle_erp_id",flat=True))
     if str(grade['OrganizationId']) in job_grade_values:
          update_grade(user,grade)
     else:
          create_grade(user,grade)

def get_grade_response():
     orcale_grades = GradeIntegration.objects.all()
     if len(orcale_grades) !=0:
          last_updated_departments = orcale_grades.values('imported_date').annotate(dcount=Count('imported_date')).order_by('imported_date').last()["imported_date"]
          params = {"onlyData": "true","limit":10000,"q":"LastUpdateDate >{}".format(last_updated_departments)}
     else:
          params = {"onlyData": "true","limit":10000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/organizations'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_grades =  response.json()["items"] 
     return orcale_grades



@login_required(login_url='home:user-login')
def list_grade(request):
     orcale_grades = get_grade_response()
     if len(orcale_grades) != 0:
          for grade in orcale_grades:
               check_grade_is_exist(request.user,grade)
     
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
          position_without_departments_msg = positions_without_departments_str   + " this positions department id not exist,  " 
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
          positions_without_jobs.append(position_name)
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

     







