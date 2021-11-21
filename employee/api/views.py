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



user_name = 'cec.hcm'
password = '12345678'
employees_list = []


def convert_date(date_time):
     date = date_time
     date_splited = date.split('T', 1)[0] # take only date from datetime syt
     string_date = ''.join(date_splited) #convert it from list to str 
     date_obj = datetime.strptime(string_date, '%Y-%m-%d')
     return date_obj


############################### Employee #########################################################
def update_employee(user,employee):
     pass



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
               identification_type = employee['NationalIdType'],
               id_number = employee['NationalId'],
               nationality = employee['NationalIdCountry'],
               gender = employee['Gender'],
               military_status = get_emp_military_status(employee['MilitaryVetStatus']),
               religion =  employee['Religion'],
               oracle_erp_id = employee['PersonId'],
               emp_start_date = employee['EffectiveStartDate'],                         
               created_by = user,
               creation_date = date.today(),
               last_update_by = user,
               last_update_date = date_obj
               )
          employee_obj.save()
          employee_assignnments = EmployeeAssignments(user, employee["links"],employee_obj)
          errors = employee_assignnments.run_employee_assignnments()
          print(errors)
     except Exception as e:
          print(e)
          employees_list.append(employee['Name'])




def check_employee_is_exist(user,employee):
     orcale_employees = Employee.objects.filter(oracle_erp_id__isnull = False)
     if str(employee["PersonId"]) in orcale_employees:
          print("createeeee")
          update_employee(user,employee)
     else:
          print("createeeee")
          create_employee(user,employee)
          


def get_employee_response():
     orcale_employees = Employee.objects.filter(oracle_erp_id__isnull = False)
     if len(orcale_employees) !=0:
          last_updated_employees = orcale_employees.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
          params = {"limit":10000,"q":"LastUpdateDate >{}".format(last_updated_employees)}
     else:
          params = {"limit":10000}
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

     if len(employees_list) != 0:
          employees_str = ', '.join(employees_list) 
          error_msg = "thises emplyees cannot be created or updated" + employees_str
          messages.error(request,error_msg)
     else:
          success_msg = "employees imported successfuly " 
          messages.success(request, success_msg)
     return redirect('employee:list-employee')



