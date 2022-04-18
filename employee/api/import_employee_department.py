
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from employee.models import Employee, JobRoll 




user_name =  'Integration.Shoura'
#'cec.hcm'
password = 'Int_123456'
#'12345678'


def get_data_for_one_employee(orcale_employees):
     employees_data = []
     for employee in orcale_employees:
          params = {'q':f'PersonNumber = {employee.emp_number}'}
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/emps'
          response = requests.get(url, auth=HTTPBasicAuth(user_name, password) , params=params)
          if response.status_code == 200:     
               employee =  response.json()["items"] 
               employees_data.append(employee[0])
     return employees_data      




def get_employee_assignments_url(employee_links,PersonId): #1
     assignments_oracle_link = list(filter(lambda link: link['name'] == 'assignments',employee_links))
     assignments_url = assignments_oracle_link[0]['href']
     get_employee_assignments_response(assignments_url,PersonId)



def get_employee_assignments_response(assignments_url,PersonId): #2
     params = {'q':'AssignmentStatus=ACTIVE'}
     response = requests.get(assignments_url, auth=HTTPBasicAuth(user_name,password),params=params) 
     if response.status_code == 200:
          employee_assignments =  response.json()["items"] 
          check_employee_assignments(employee_assignments,PersonId )


def check_employee_assignments(employee_assignments ,PersonId): #3
     if len(employee_assignments) != 0:
          employee_jobroll = JobRoll.objects.filter(emp_id__oracle_erp_id=PersonId)
          for jobroll in employee_jobroll:
               jobroll.employee_department_oracle_erp_id=employee_assignments[0]['DepartmentId']
               jobroll.save()












     def run_employee_assignnments(self):
          errors = []
          assignments_url =  self.get_employee_assignments_url()
          employee_assignments  = self.get_employee_assignments_response(assignments_url)
          self.check_employee_assignments(employee_assignments )
          if len(self.companies_not_founded) != 0:
               errors.append(self.companies_not_founded)
          if len(self.companies_not_assigen) != 0:
               errors.append(self.companies_not_assigen)
          if len(self.employees_not_founded) != 0:
               errors.append(self.employees_not_founded)
          if len(self.position_not_founded) != 0:
               errors.append(self.position_not_founded)
          if len(self.jobroll_not_created) != 0:
               errors.append(self.jobroll_not_created)  
          return errors     






def import_employee_department(request):
     employees = Employee.objects.all()
     orcale_employees = get_data_for_one_employee(employees)
     for employee in orcale_employees:
          employee_assignnments = get_employee_assignments_url(employee["links"],employee["PersonId"])











