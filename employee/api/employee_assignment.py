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
          self.user_name = 'Integration.Shoura'
          self.password = 'Int_123456'
          self.companies_not_founded=[]
          self.companies_not_assigen = []
          self.employees_not_founded = []
          self.position_not_founded=[]

  

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
          contract_type= LookupDet.objects.get(code = 'CONTRACT')
          return contract_type


     def get_employee_assignments_url(self): #1
          assignments_oracle_link = list(filter(lambda link: link['name'] == 'assignments', self.employee_links))
          assignments_url = assignments_oracle_link[0]['href']
          employee_jobroll = JobRoll.objects.filter(emp_id=self.employee)
          if len(employee_jobroll) != 0: #update
               last_assignments_updates=employee_jobroll.values('creation_date').annotate(dcount=Count('creation_date')).order_by('creation_date').last()["creation_date"]
               params = {"q":"LastUpdateDate >{}".format(last_assignments_updates)}
               response = requests.get(assignments_url, auth=HTTPBasicAuth(self.user_name, self.password) , params=params) #can be empty 
               status = 'update'
          else: #create
               response = requests.get(assignments_url, auth=HTTPBasicAuth(self.user_name, self.password)) #cannot be empty : new rec
               status = 'create'
          assignments_url =  response.json()["items"]      
          return assignments_url , status

     

     def get_employee_assignments_response(self, assignments_url ,status): #2
          url = assignments_url
          response = requests.get(url, auth=HTTPBasicAuth(self.user_name, self.password))
          employee_assignments =  response.json()["items"] 
          return employee_assignments , status



     def check_employee_assignments(self, employee_assignments , status): #3
          self.assign_company_to_employee(employee_assignments['BusinessUnitId'])
          if status == 'update':
               if len(employee_assignments) != 0:
                    self.update_employee_jobroll(employee_assignments)
          if status == 'create':
               self.assign_company_to_employee(employee_assignments)




     def assign_company_to_employee(self,oracle_company):
          employee = Employee.objects.get(id = self.employee)
          try:
               company = Enterprise.objects.get(oracle_erp_id = oracle_company)
               if employee.enterprise != company:
                    try:
                         employee.enterprise = company
                         employee.save()
                    except Exception as e:
                         print(e)
                         self.companies_not_assigen.append(str(oracle_company) +" to "+ self.employee.emp_name)
          except Enterprise.DoesNotExist:
               self.companies_not_founded.append(str(oracle_company))
          
          

     def create_employee_jobroll(self , employee_assignments):
          try:
               position = Position.objects.get(oracle_erp_id=employee_assignments['PositionId'])
               date_obj = self.convert_date(employee_assignments['LastUpdateDate'])
               jobroll_obj = JobRoll(
                              emp_id = self.employee,
                              position = position,
                              contract_type = self.get_lookupdet(), 
                              payroll = self.get_jobroll(),
                              start_date = employee_assignments['EffectiveStartDate'],
                              end_date =employee_assignments['EffectiveStartDate'],
                              created_by = self.user,
                              creation_date = date.today(),
                              last_update_by = self.user,
                              last_update_date = date_obj,
               )
               jobroll_obj.save()
          except Position.DoesNotExist:
               self.position_not_founded.append(str(employee_assignments['PositionId']))


          
     def update_employee_jobroll(self,employee_assignments):
          try:
               position = Position.objects.get(oracle_erp_id=employee_assignments['PositionId'])
               date_obj = self.convert_date(employee_assignments['LastUpdateDate'])
               try:
                    JobRoll.objects.get(emp_id = self.employee, position=position,end_date__isnull=True)
               except JobRoll.DoesNotExist:
                    last_jobroll = JobRoll.objects.get(emp_id = self.employee,end_date__isnull=True)
                    last_jobroll.end_date = date.today()
                    jobroll_obj = JobRoll(
                                   emp_id = self.employee,
                                   position = position,
                                   contract_type = self.get_lookupdet(), 
                                   payroll = self.get_jobroll(),
                                   start_date = employee_assignments['EffectiveStartDate'],
                                   end_date =employee_assignments['EffectiveStartDate'],
                                   created_by = self.user,
                                   creation_date = date.today(),
                                   last_update_by = self.user,
                                   last_update_date = date_obj,
                    )
                    jobroll_obj.save()
          except Position.DoesNotExist:
               self.position_not_founded.append(str(employee_assignments['PositionId']))




     def run_employee_assignnments(self):
          errors = []
          assignments_url, status =  self.get_employee_assignments_url()
          employee_assignments , status = self.get_employee_assignments_response(assignments_url, status)
          self.check_employee_assignments(employee_assignments , status)
          if len(self.companies_not_founded) != 0:
               errors.append(self.companies_not_founded)
          if len(self.companies_not_assigen) != 0:
               errors.append(self.companies_not_assigen)
          if len(self.employees_not_founded) != 0:
               errors.append(self.employees_not_founded)
          if len(self.position_not_founded) != 0:
               errors.append(self.position_not_founded)
          return errors     
     