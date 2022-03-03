#!/usr/bin/env python
import requests
from requests.auth import HTTPBasicAuth 
from django.core.checks import messages
from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 
from company.models import *
from django.contrib import messages
from datetime import datetime , date
from django.shortcuts import redirect
from employee.models import Employee_Element
from element_definition.import_sick_leave import ImportSickLeaveDays




class ImportAbsences:
     def __init__(self, request,start_date,end_date):
          self.request = request
          self.start_date = start_date
          self.end_date = end_date
          self.user_name = 'Integration.Shoura'
          self.password = 'Int_123456'
          self.employees_not_have_absence_element = []



     def absence_types(self,ABSENCE_TYPE_ID):
          if ABSENCE_TYPE_ID == 300000002604275:
               element_name = 'Absent Days'  #Absent Days
          elif ABSENCE_TYPE_ID == 300000002604311:
                element_name = 'Unpaid Days' # Unpaid Days
          elif ABSENCE_TYPE_ID == 300000002604347:
               element_name = 'SickLeave Days' #SickLeave Days
          elif ABSENCE_TYPE_ID == 300000002604388:
               element_name = 'SickLeave Days_25' # shour/starchem = SickLeave Days_25
          else:
               element_name = None
          return element_name        


          


     def assigen_absences_days_to_employee(self,employee_absences_days,absence_type_id,person_id):
          absence_type_name = self.absence_types(absence_type_id)
          if absence_type_name is not None:
               try:
                    employee_element = Employee_Element.objects.get(element_id__element_name= absence_type_name, emp_id__oracle_erp_id= person_id)
                    if absence_type_name == 'SickLeave Days_25' or absence_type_name == 'SickLeave Days':
                         sick_leave_days_obj = ImportSickLeaveDays(self.start_date , self.end_date,employee_element)
                         sick_leave_days_obj.run_class()
                    else:
                         employee_element.element_value = int(float(employee_absences_days))
                         employee_element.last_update_date = date.today()
                         employee_element.save()
               except Employee_Element.DoesNotExist:
                    self.employees_not_have_absence_element.append('this employee '+str(person_id)+' not have element '+ absence_type_name +' with this id '+ str(absence_type_id))




     def calc_employee_absences_days(self,start_date,end_date):
          start =  datetime.strptime(start_date.split('T')[0],'%Y-%m-%d')
          end = datetime.strptime(end_date.split('T')[0],'%Y-%m-%d')
          employee_absences_days = end- start
          return employee_absences_days.days

     
     def assigen_employee_absences(self,employee):
          employee_absences_days = self.calc_employee_absences_days(employee["startDateTime"],employee["endDateTime"])
          self.assigen_absences_days_to_employee(employee_absences_days,employee["absenceTypeId"],employee["personId"])



     def get_employee_absence_response(self):
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/absences'
          params = {"onlyData": "true","limit":10000,
          "q":f"startDate >={self.start_date};endDate<={self.end_date};approvalStatusCd=APPROVED;absenceTypeId=300000002604275 or 300000002604311 or 300000002604347 or 300000002604388"}
          response = requests.get(url, auth=HTTPBasicAuth(self.user_name, self.password) , params=params)
          if response.status_code == 200:     
               employees_absences =  response.json()["items"] 
               return employees_absences
          else:
               messages.error(self.request,"some thing wrong when import from to oracle api , please connect to the adminstration ")
               return redirect('payroll_run:create-salary')  


     def run_employee_absence(self):
          employees_absences = self.get_employee_absence_response()
          for employee in employees_absences:
               self.assigen_employee_absences(employee)
          return self.employees_not_have_absence_element

     



         