from django.core.checks import messages
from django.shortcuts import render, redirect, get_object_or_404, HttpResponse
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from custom_user.models import UserCompany
from rest_framework.permissions import IsAuthenticated 
from django.contrib import messages
from django.db.models import Count
from datetime import datetime
from custom_user.models import User
from django.contrib.auth.decorators import login_required
from employee.models import Employee , JobRoll
from manage_payroll.models import Payroll_Master
from defenition.models import LookupDet





class EmployeeAssignments:
     def __init__(self, user,employee_links,employee_obj):
          self.employee_links = employee_links
          self.employee =employee_obj
          self.user = user
          self.user_name =  'Integration.Shoura'
          self.password = 'Int_123456'
          self.companies_not_founded=[]
          self.companies_not_assigen = []
          self.employees_not_founded = []
          self.position_not_founded=[]
          self.jobroll_not_created=[]

  

     def convert_date(self,date_time):
          date = date_time
          date_splited = date.split('T', 1)[0] # take only date from datetime syt
          string_date = ''.join(date_splited) #convert it from list to str 
          date_obj = datetime.strptime(string_date, '%Y-%m-%d')
          return date_obj     
     
     
     def get_jobroll(self):
          payroll = Payroll_Master.objects.filter(enterprise= self.user.company).first()
          return payroll


     def get_lookupdet(self):
          # contract_type= LookupDet.objects.filter(code = 'CONTRACT' , lookup_type_fk__enterprise= self.user.company).first()
          try:
               employee_company = Employee.objects.get(id= self.employee).enterprise
          except Employee.DoesNotExist:
               employee_company = self.user.company
          contract_type= LookupDet.objects.filter(lookup_type_fk__lookup_type_name='EMPLOYEE_TYPE' , lookup_type_fk__enterprise= employee_company).first()
          return contract_type


     def get_employee_assignments_url(self): #1
          assignments_oracle_link = list(filter(lambda link: link['name'] == 'assignments', self.employee_links))
          assignments_url = assignments_oracle_link[0]['href']
          return assignments_url 




     def get_employee_assignments_response(self, assignments_url): #2
          employee_jobroll = JobRoll.objects.filter(emp_id=self.employee)
          if len(employee_jobroll) != 0: 
               last_assignments_updates=employee_jobroll.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
               params = {"q":"LastUpdateDate >{}".format(last_assignments_updates)}
               response = requests.get(assignments_url, auth=HTTPBasicAuth(self.user_name, self.password) , params=params) #can be empty 
          else:
               response = requests.get(assignments_url, auth=HTTPBasicAuth(self.user_name, self.password)) #cannot be empty : new rec
          if response.status_code == 200:
               employee_assignments =  response.json()["items"] 
               return employee_assignments
          else:
               self.employees_not_founded = []
              




     def check_employee_assignments(self, employee_assignments ): #3
          if len(employee_assignments) != 0:
               self.assign_company_to_employee(employee_assignments[0]['BusinessUnitId'])
               job_roll = JobRoll.objects.filter(emp_id=employee_assignments[0]['PositionId'])
               if len(job_roll) !=  0 :
                    self.update_employee_jobroll(employee_assignments)
               else:
                    self.create_employee_jobroll(employee_assignments)





     def assign_company_to_employee(self,oracle_company):
          try:
               company = Enterprise.objects.get(oracle_erp_id = oracle_company)
               try:
                    self.employee.enterprise = company
                    self.employee.save()
               except Exception as e:
                    self.companies_not_assigen.append("this company "+str(oracle_company) +" to "+ self.employee.emp_name + " not assigen")

          except Enterprise.DoesNotExist:
               self.companies_not_founded.append("employee "+self.employee.emp_name+"-->" + "  this company"+str(oracle_company))+ " not found"

     
          
          

     def create_employee_jobroll(self , employee_assignments):
          try:
               position = Position.objects.get(oracle_erp_id=employee_assignments[0]['PositionId'])
               date_obj = self.convert_date(employee_assignments[0]['LastUpdateDate'])
               jobroll_obj = JobRoll(
                              emp_id = self.employee,
                              position = position,
                              contract_type = self.get_lookupdet(), 
                              payroll = self.get_jobroll(),
                              start_date = employee_assignments[0]['EffectiveStartDate'],
                              end_date =employee_assignments[0]['EffectiveEndDate'],
                              created_by = self.user,
                              creation_date = date.today(),
                              last_update_by = self.user,
                              last_update_date = date_obj,
               )
               jobroll_obj.save()
          except Position.DoesNotExist:
               self.position_not_founded.append("employee "+self.employee.emp_name+"-->" + "  this position"+str(employee_assignments[0]['PositionId'])+ " not found")
          except Exception as e :
               self.jobroll_not_created.append("jobroll for this employee "+self.employee.emp_name +"cannot created or updated")


          
     def update_employee_jobroll(self,employee_assignments):
          try:
               position = Position.objects.get(oracle_erp_id=employee_assignments[0]['PositionId'], department__enterprise=self.user.company)
               date_obj = self.convert_date(employee_assignments[0]['LastUpdateDate'])
               try:
                    JobRoll.objects.get(emp_id = self.employee, position=position,end_date__isnull=True)
               except JobRoll.DoesNotExist:
                    try:
                         last_jobroll = JobRoll.objects.get(emp_id = self.employee,end_date__isnull=True)
                    except Exception as e:
                         print(e)
                         last_jobroll = JobRoll.objects.filter(emp_id = self.employee).last()
                    last_jobroll.end_date = date.today()
                    last_jobroll.save()
                    jobroll_obj = JobRoll(
                                   emp_id = self.employee,
                                   position = position,
                                   contract_type = self.get_lookupdet(), 
                                   payroll = self.get_jobroll(),
                                   start_date = employee_assignments[0]['EffectiveStartDate'],
                                   end_date =employee_assignments[0]['EffectiveEndDate'],
                                   created_by = self.user,
                                   creation_date = date.today(),
                                   last_update_by = self.user,
                                   last_update_date = date_obj,
                    )
                    jobroll_obj.save()
          except Position.DoesNotExist:
               self.position_not_founded.append("employee "+self.employee.emp_name+"-->" + "  this position"+str(employee_assignments[0]['PositionId'])+ " not found")
          except Exception as e :
               self.jobroll_not_created.append("jobroll for this employee "+self.employee.emp_name +"cannot created or updated")






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
     


















# 00020000000EACED0005770800005AF31092431B0000004AACED00057372000D6A6176612E73716C2E4461746514FA46683F3566970200007872000E6A6176612E7574696C2E44617465686A81014B597419030000787077080000017DC089DC0078  
# 00020000000EACED0005770800005AF31092431B0000004AACED00057372000D6A6176612E73716C2E4461746514FA46683F3566970200007872000E6A6176612E7574696C2E44617465686A81014B597419030000787077080000017DC089DC0078   