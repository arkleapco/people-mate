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



user_name =  'cec.hcm'
# 'Integration.Shoura'
password = '12345678'
# 'Int_123456'
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


############################### Employee #########################################################
def update_employee(user,old_employee):
     employee = Employee.objects.get(oracle_erp_id=old_employee["PersonId"] ,emp_end_date__isnull=True)
     date_time = old_employee['LastUpdateDate']
     date_obj = convert_date(date_time)
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
          employee.creation_date = date.today()
          employee.last_update_by = user
          employee.last_update_date = date_obj
          employee.save()

          employee_assignnments = EmployeeAssignments(user, old_employee["links"],employee)
          assignment_errors = employee_assignnments.run_employee_assignnments()
          assignment_errors_list.append(assignment_errors)

          employee_insurance = EmployeeInsurance(user, old_employee["links"],employee)
          insurance_errors = employee_insurance.run_employee_insurance()
          insurance_errors_list.append(insurance_errors)
     except Exception as e:
          print(e)
          employees_list.append(old_employee['DisplayName'])



def get_emp_type(oracle_emp_type):
     if oracle_emp_type  == "A":
          emp_type = "E"
     elif oracle_emp_type == "E":
          emp_type = "EX"
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
          employee_assignnments = EmployeeAssignments(user, employee["links"],employee_obj)
          assignment_errors = employee_assignnments.run_employee_assignnments()
          assignment_errors_list.append(assignment_errors)

          employee_insurance = EmployeeInsurance(user, employee["links"],employee_obj)
          insurance_errors = employee_insurance.run_employee_insurance()
          insurance_errors_list.append(insurance_errors)
     except Exception as e:
          print(e)
          employees_list.append(employee['DisplayName'])




def check_employee_is_exist(user,employee):
     orcale_employees = list(Employee.objects.filter(oracle_erp_id__isnull = False).values_list("oracle_erp_id",flat=True))
     if str(employee["PersonId"]) in orcale_employees:
          update_employee(user,employee)
     else:
          create_employee(user,employee)
          


def get_employee_response():
     orcale_employees = Employee.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_employees) !=0:
          last_updated_employees = orcale_employees.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"limit":1000,"q":"LastUpdateDate >{}".format(last_updated_employees)}
     else:
          params = {"limit":1000}
     url = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/emps'
     response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
     orcale_employees =  response.json()["items"] 
     return orcale_employees



@login_required(login_url='home:user-login')
def list_employees(request):
     orcale_employees = get_employee_response()
     if len(orcale_employees) != 0:
          for employee in orcale_employees:
               check_employee_is_exist(request.user,employee)

     if len(assignment_errors_list) != 0 or len(insurance_errors_list)  or len(employees_list) :
          # errors = ', '.join(assignment_errors_list) 
          # assignments_errors = "thises emplyees assignments cannot be created or updated  " + errors
          
          # insurance_errors_str = ', '.join(insurance_errors_list)   
          # insurance_errors = "thises emplyees insurance  cannot be created or updated  " + insurance_errors_str
          
          # employees_str = ', '.join(employees_list) 
          # employees_error= "thises emplyees cannot be created or updated  " + employees_str 
          # error_msg = (assignments_errors + insurance_errors +  employees_error)
          
          # messages.error(request,error_msg)
          print(assignment_errors_list)
          print(insurance_errors_list)
          print(employees_list)
     else:   
          success_msg = "employees imported successfuly " 
          messages.success(request, success_msg)
     return redirect('employee:list-employee')



