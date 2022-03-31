#!/usr/bin/env python
from pickle import FALSE
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
from employee.models import Employee, Employee_Element
from element_definition.import_sick_leave import ImportSickLeaveDays
from calendar import monthrange





class ImportAbsences:
     def __init__(self, request,start_date,end_date,month,year):
          self.request = request
          self.start_date = start_date
          self.end_date = end_date
          self.month = month
          self.year = year
          self.user_name = 'Integration.Shoura'
          self.password = 'Int_123456'
          self.employees_not_have_absence_element = []


     def check_if_employee_in_active_company(self,person_id):
          employee_element = Employee_Element.objects.filter(emp_id__oracle_erp_id= person_id)
          if len(employee_element) > 0 :
               if employee_element.first().emp_id.enterprise == self.request.user.company:
                    return True
               else:
                    return False  

     def check_employee_is_aprroved(self,employee_processingStatus):
          if employee_processingStatus == "P":
               return True
          else:
               return False     
               

                  




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


          


     def assigen_absences_days_to_employee(self,employee_absences_days,absence_type_id,person_id,more_than_recored):
          employee_element = None
          employee_code_number = Employee.objects.filter(oracle_erp_id=person_id).first().emp_number
          absence_type_name = self.absence_types(absence_type_id)
          if absence_type_name is not None:
               try:
                    employee_element = Employee_Element.objects.get(element_id__element_name= absence_type_name, emp_id__oracle_erp_id= person_id)
               except Employee_Element.DoesNotExist:
                    if absence_type_name == 'SickLeave Days':
                         try:
                              employee_element = Employee_Element.objects.get(element_id__element_name= 'SickLeave Days_25', emp_id__oracle_erp_id= person_id)
                         except Employee_Element.DoesNotExist:
                              self.employees_not_have_absence_element.append('this employee '+str(employee_code_number)+' not have element '+ absence_type_name )
                    else:
                         self.employees_not_have_absence_element.append('this employee '+str(employee_code_number)+' not have element '+ absence_type_name )
               if employee_element is not None:
                    if absence_type_name == 'SickLeave Days_25' or absence_type_name == 'SickLeave Days':
                         sick_leave_days_obj = ImportSickLeaveDays(self.start_date , self.end_date,employee_element, more_than_recored)
                         sick_leave_days_obj.run_class()
                    else:
                         if more_than_recored == True:
                              employee_element.element_value += float(employee_absences_days)
                         elif more_than_recored == False:
                              employee_element.element_value = float(employee_absences_days)
                         employee_element.last_update_date = date.today()
                         employee_element.save()
              
              
              
              


     def check_if_employee_absences_days_equel_month_days(self,employee_absences_days):
          real_month_num_days = monthrange(int(self.year), int(self.month))[1] # like: num_days = 28
          if employee_absences_days == real_month_num_days :
               return 30  
          else:
               return employee_absences_days







     def calc_employee_absences_days(self,start_date,end_date):
          start =  datetime.strptime(start_date.split('T')[0],'%Y-%m-%d')
          end = datetime.strptime(end_date.split('T')[0],'%Y-%m-%d')
          employee_absences_days = end- start
          # if employee_absences_days.days == 0 :
               # absences_days = self.check_if_employee_absences_days_equel_month_days(employee_absences_days.days)
          # else:
          absences_days = self.check_if_employee_absences_days_equel_month_days(employee_absences_days.days + 1)
          return absences_days

     
     def assigen_employee_absences(self,employee,more_than_recored):
          employee_absences_days = self.calc_employee_absences_days(employee["startDateTime"],employee["endDateTime"])
          self.assigen_absences_days_to_employee(employee_absences_days,employee["absenceTypeId"],employee["personId"],more_than_recored)



     def get_employee_absence_response(self):
          url = 'https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/hcmRestApi/resources/11.13.18.05/absences'
          params = {"onlyData": "true","limit":10000,
          "q":f"startDate >={self.start_date};endDate<={self.end_date};approvalStatusCd=APPROVED or AWAITING ;absenceStatusCd <>ORA_WITHDRAWN;absenceTypeId=300000002604275 or 300000002604311 or 300000002604347 or 300000002604388"}
          # absenceDispStatus=COMPLETED
          response = requests.get(url, auth=HTTPBasicAuth(self.user_name, self.password) , params=params)
          if response.status_code == 200:     
               employees_absences =  response.json()["items"] 
               return employees_absences
          else:
               messages.error(self.request,"some thing wrong when import from to oracle api , please connect to the adminstration ")
               return redirect('payroll_run:create-salary')  


     def run_employee_absence(self):
          employees_ids_list = []
          employees_absences = self.get_employee_absence_response()
          for employee in employees_absences:
               employee_company = self.check_if_employee_in_active_company(employee["personId"])
               employee_is_aprroved = self.check_employee_is_aprroved(employee["processingStatus"])
               if employee_company and employee_is_aprroved:
                    if employee["personId"] in employees_ids_list: # to check if employee have more than one recored in response
                         more_than_recored = True
                    else:
                         more_than_recored = False     
                    employees_ids_list.append(employee["personId"])
                    self.assigen_employee_absences(employee, more_than_recored)
          return self.employees_not_have_absence_element

     



         