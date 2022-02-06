from django.core.checks import messages
from django.shortcuts import  redirect
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from django.contrib import messages
from django.db.models import Count
from datetime import datetime
from django.contrib.auth.decorators import login_required
from employee.models import Employee 
from .employee_assignment import EmployeeAssignments
from .employee_insurance import EmployeeInsurance
from trace_log import views
from .employee_last_updated_date import EmployeeLastupdatedateReport



user_name =  'Integration.Shoura'
#'cec.hcm'
password = 'Int_123456'
#'12345678'
employees_list = []
assignment_errors_list= []
insurance_errors_list = []
all_errors = []



def convert_date(date_time):
     date = date_time
     date_splited = date.split('T', 1)[0] # take only date from datetime syt
     string_date = ''.join(date_splited) #convert it from list to str 
     date_obj = datetime.strptime(string_date, '%Y-%m-%d')
     return date_obj



def get_data_for_one_employee(orcale_employees):
     employees_data = []
     for employee in orcale_employees:
          params = {'q':f'PersonNumber = {employee["PersonNum"]}'}
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/emps'
          response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
          if response.status_code == 200:     
               employee =  response.json()["items"] 
               employees_data.append(employee[0])
          else:
               employees_list.append("this employee cannot be created or updated"+employee['PersonNum'])
          break
     return employees_data  



############################### Employee #########################################################
def update_employee(user,old_employee):
     employee = Employee.objects.get(oracle_erp_id=old_employee["PersonId"] ,emp_end_date__isnull=True)
     date_time = old_employee['LastUpdateDate']
     date_obj = convert_date(date_time)
     # create new rec to keep history with updates
     try:
          backup_recored = Employee(
                    emp_number = employee.emp_number,
                    enterprise = employee.enterprise,
                    emp_type = employee.emp_type,
                    emp_name = employee.emp_name,
                    emp_arabic_name = employee.emp_arabic_name,
                    address1 = employee.address1,
                    mobile = employee.mobile,
                    date_of_birth = employee.date_of_birth,
                    hiredate =employee.hiredate,
                    terminationdate =employee.terminationdate,
                    email = employee.email,
                    identification_type = employee.identification_type,
                    id_number = employee.id_number,
                    nationality = employee.nationality,
                    gender = employee.gender,
                    military_status = employee.military_status,
                    religion =  employee.religion,
                    has_medical = False,
                    oracle_erp_id = employee.oracle_erp_id,
                    emp_start_date = employee.emp_start_date,    
                    emp_end_date = date.today(),            
                    creation_date = employee.creation_date,
                    last_update_by = employee.last_update_by,
                    last_update_date = employee.last_update_date,
                    created_by = user,
                    insurance_number = employee.insurance_number,
                    insurance_salary = employee.insurance_salary,
                    retirement_insurance_salary = employee.retirement_insurance_salary 
                    )
          backup_recored.save()  
     except Exception as e:
          print(e)
          views.create_trace_log(user.company.name,'exception in create new rec with enddate when update employee '+ str(e),'oracle_old_employee = '+  str(old_employee["PersonId"]) ,'def update_employee()',user.user_name)       

     try:
          employee.emp_number = old_employee['PersonNumber']
          employee.emp_type = get_emp_type(old_employee['WorkerType'])
          employee.emp_name = old_employee['DisplayName']
          employee.emp_arabic_name = old_employee['DisplayName']
          employee.address1 = old_employee['AddressLine1']
          employee.mobile = old_employee['WorkMobilePhoneNumber']
          employee.date_of_birth = old_employee['DateOfBirth']
          employee.hiredate = old_employee['HireDate']
          employee.terminationdate =old_employee['TerminationDate']
          employee.email = old_employee['WorkEmail']
          employee.identification_type =   get_identification_type(old_employee['NationalIdType'])
          employee.id_number = old_employee['NationalId']
          employee.nationality = old_employee['NationalIdCountry']
          employee.gender = old_employee['Gender']
          employee.military_status = get_emp_military_status(old_employee['MilitaryVetStatus'])
          employee.religion =  get_emp_religion(old_employee['Religion'])
          employee.has_medical = False
          employee.oracle_erp_id = old_employee['PersonId']
          employee.emp_start_date = old_employee['EffectiveStartDate']   
          employee.emp_end_date = old_employee['TerminationDate']    
          employee.creation_date = date.today()
          employee.last_update_by = user
          employee.last_update_date = date_obj
          employee.save()
     except Exception as e:
          print(e)
          employees_list.append("this employee cannot be  updated "+old_employee['DisplayName'])


     employee_assignnments = EmployeeAssignments(user, old_employee["links"],employee)
     assignment_errors = employee_assignnments.run_employee_assignnments()
     if len(assignment_errors) != 0 :
          assignment_errors_list.append(assignment_errors)

     employee_insurance = EmployeeInsurance(user, old_employee["links"],employee)
     insurance_errors = employee_insurance.run_employee_insurance()
     if len(insurance_errors) != 0 :
          insurance_errors_list.append(insurance_errors)
    


def get_emp_type(oracle_emp_type):
     if oracle_emp_type  == "EX":
          emp_type = "EX"
     elif oracle_emp_type == "E":
          emp_type = "E"
     else:
          emp_type = None
     return  emp_type   



def get_emp_military_status(oracle_emp_military_status):
     if oracle_emp_military_status ==  "N":
          military_status = "P"
     elif oracle_emp_military_status == "Y": 
          military_status = "C"
     else:
          military_status = "E"
     return  military_status    
          

def get_emp_religion(oracle_emp_religion):
     if oracle_emp_religion ==  "MUSLIM":
          emp_religion = "M"
     else:
          emp_religion = "C"  
     return emp_religion     



def get_identification_type(oracle_emp_NationalIdType):
     if oracle_emp_NationalIdType ==  "NID":
          type = "N"
     else:     
          type= "P"
     return type     


def create_employee(user,employee):
     date_time = employee['LastUpdateDate']
     date_obj = convert_date(date_time)
     try:
          employee_obj = Employee(
               emp_number = employee['PersonNumber'],
               emp_type = get_emp_type(employee['WorkerType']),
               emp_name = employee['DisplayName'],
               emp_arabic_name = employee['DisplayName'],
               address1 = employee['AddressLine1'],
               mobile = employee['WorkMobilePhoneNumber'],
               date_of_birth = employee['DateOfBirth'],
               hiredate = employee['HireDate'],
               terminationdate =employee['TerminationDate'],
               email = employee['WorkEmail'],
               identification_type =   get_identification_type(employee['NationalIdType']),
               id_number = employee['NationalId'],
               nationality = employee['NationalIdCountry'],
               gender = employee['Gender'],
               military_status = get_emp_military_status(employee['MilitaryVetStatus']),
               religion =  get_emp_religion(employee['Religion']),
               has_medical = False,
               oracle_erp_id = employee['PersonId'],
               emp_start_date = employee['EffectiveStartDate'],                         
               created_by = user,
               creation_date = date.today(),
               last_update_by = user,
               last_update_date = date_obj
               )
          employee_obj.save()
     except Exception as e:
          print(e)
          employees_list.append("this employee cannot be created "+employee['DisplayName'])

     employee_assignnments = EmployeeAssignments(user, employee["links"],employee_obj)
     assignment_errors = employee_assignnments.run_employee_assignnments()
     if len(assignment_errors) != 0 :
          assignment_errors_list.append(assignment_errors)

     employee_insurance = EmployeeInsurance(user, employee["links"],employee_obj)
     insurance_errors = employee_insurance.run_employee_insurance()
     if len(insurance_errors) != 0 :
          insurance_errors_list.append(insurance_errors)
    




def check_employee_is_exist(user,employee):     
     orcale_employees = list(Employee.objects.filter(oracle_erp_id__isnull = False).values_list("oracle_erp_id",flat=True))
     if str(employee["PersonId"]) in orcale_employees:
          update_employee(user,employee)
     else:
          create_employee(user,employee)
          


def get_employee_response(request):
     orcale_employees = Employee.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_employees) !=0:
          last_updated_employees = orcale_employees.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          last_updated_employees_for_api = f'{str(last_updated_employees.month).zfill(2)}-{str(last_updated_employees.day).zfill(2)}-{last_updated_employees.year}'
          class_obj = EmployeeLastupdatedateReport(request, last_updated_employees_for_api)
          orcale_employees = class_obj.run_employee_lastupdatedate_report()
          from_last_update_date = True
     else:
          params = {"limit":1000}
          # params = {"q":"PersonNumber = 1204"} 
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/emps'
          response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
          if response.status_code == 200:     
               orcale_employees =  response.json()["items"] 
               from_last_update_date = False
          else:
               messages.error(request,"some thing wrong when sent request to oracle api , please connect to the adminstration ")
               return redirect('employee:list-employee')
     return orcale_employees , from_last_update_date 

     



@login_required(login_url='home:user-login')
def list_employees(request):
     orcale_employees , from_last_update_date = get_employee_response(request)
     if from_last_update_date == True:
          employees_data_list = get_data_for_one_employee(orcale_employees)
          orcale_employees = employees_data_list
     if len(orcale_employees) != 0:
          for employee in orcale_employees:
               check_employee_is_exist(request.user,employee)

     if len(assignment_errors_list) != 0 or len(insurance_errors_list) != 0 or len(employees_list) != 0:
          all_errors.append(assignment_errors_list)
          all_errors.append(insurance_errors_list)
          all_errors.append(employees_list)
     
          print(assignment_errors_list)
          print(insurance_errors_list)
          print(employees_list)
          messages.error(request, all_errors)
     else:   
          success_msg = "employees imported successfuly " 
          messages.success(request, success_msg)
     return redirect('employee:list-employee')



