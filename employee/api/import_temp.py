from django.core.checks import messages
from django.shortcuts import  redirect
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from django.contrib import messages
from employee.models import  ImportTemp
from .employee_last_updated_date import EmployeeLastupdatedateReport



user_name =  'Integration.Shoura'
password = 'Int_123456'





def get_employee_assignments_url(employee): #1
     assignments_oracle_link = list(filter(lambda link: link['name'] == 'assignments', employee["links"]))
     assignments_url = assignments_oracle_link[0]['href']
     get_employee_assignments_response(employee,assignments_url)




def get_employee_assignments_response(employee, assignments_url): #2
     response = requests.get(assignments_url, auth=HTTPBasicAuth(user_name,password)) #cannot be empty : new rec
     if response.status_code == 200:
          employee_assignments =  response.json()["items"] 
          check_employee_assignments(employee, employee_assignments)
    


def check_employee_assignments(employee, employee_assignments): #3
     positions = Position.objects.filter(oracle_erp_id=employee_assignments[0]['PositionId'])
     if len(positions)  > 0:
          department = Position.objects.filter(oracle_erp_id=employee_assignments[0]['PositionId']).last().department.oracle_erp_id
     else:
          department = 0

     obj = ImportTemp(
          employee = employee['PersonId'],
          position_oracle_id= employee_assignments[0]['PositionId'],
          department_oracle_id = employee_assignments[0]['DepartmentId'],
          department_position = department
     )
     obj.save()
         
        


def get_employee_response(request):
          last_updated_employees_for_api = '01-01-1999'
          class_obj = EmployeeLastupdatedateReport(request, last_updated_employees_for_api)
          orcale_employees = class_obj.run_employee_lastupdatedate_report()
          if orcale_employees != False:
               return orcale_employees  
          else:
               return False
            

def get_data_for_one_employee(orcale_employees):
     employees_data = []
     for employee in orcale_employees:
          params = {'q':f'PersonNumber = {employee["PersonNum"]}'}
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/emps'
          response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
          if response.status_code == 200:     
               employee =  response.json()["items"] 
               employees_data.append(employee[0])
     return employees_data 

def list_employees(request):
     orcale_employees  = get_employee_response(request)
     if orcale_employees:
          employees = get_data_for_one_employee(orcale_employees)
          orcale_employees = employees
          for employee in orcale_employees:
               get_employee_assignments_url(employee)
     success_msg = "employees imported successfuly " 
     messages.success(request, success_msg)
     return redirect('employee:list-employee')
     




