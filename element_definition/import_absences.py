#!/usr/bin/env python	
from operator import le
import requests
import base64
from django.shortcuts import redirect 
import xml.etree.ElementTree as ET
from django.contrib import messages
from employee.models import Employee_Element , Employee
from element_definition.import_sick_leave import ImportSickLeaveDays
from datetime import datetime , date



class ImportAbsences:
     def __init__(self, request, from_date , to_date,month,year,user):
          self.request = request
          self.from_date = from_date
          self.to_date = to_date
          self.month = month
          self.year = year
          self.user = user
          self.employees_have_absences = []
          self.employees_not_have_absence_element = []



     def make_employee_elements_values_zero_exclude_have_penalites(self):
               absence_types_name= ['Absent Days','Unpaid Days','SickLeave Days','SickLeave Days_25']
               employee_elements = Employee_Element.objects.filter(emp_id__enterprise= self.user.company,element_id__element_name__in= absence_types_name).exclude(
                    emp_id__emp_number__in = self.employees_have_absences)
               for employee in employee_elements:
                    employee.element_value = 0
                    employee.save()


     # def make_absence_element_zero_to_employees_imported_today(self):
     #      absence_types_name= ['Absent Days','Unpaid Days','SickLeave Days','SickLeave Days_25']
     #      employees_absence_elements = Employee_Element.objects.filter(
     #                element_id__element_name__in= absence_types_name,  emp_id__enterprise= self.user.company)
     #      for employee in employees_absence_elements:
     #           employee.element_value = 0
     #           employee.save()      




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





     def replace_parameters_in_payload(self):
          # structured XML
          payload = f"""<?xml version=\"1.0\" encoding=\"utf-8\"?>
          <soap:Envelope xmlns:pub=\"http://xmlns.oracle.com/oxp/service/PublicReportService\" xmlns:soap=\"http://www.w3.org/2003/05/soap-envelope\">
               <soap:Header/>
                    <soap:Body>
                         <pub:runReport>
                         <pub:reportRequest>
                         <pub:attributeFormat>xml</pub:attributeFormat>
                         <pub:attributeLocale/>
                         <pub:attributeTemplate/>
                         <pub:reportAbsolutePath> /Custom/Integration/Absences/Abscense/XX_ABSCENCES_REP_Report.xdo</pub:reportAbsolutePath>
                         <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                         <pub:parameterNameValues>
                              <!--Zero or more repetitions:-->
                         <pub:item>
                         <pub:name>P_START_DATE</pub:name>
                         <pub:values>
                              <!--Zero or more repetitions:-->
                              <pub:item>{self.from_date}</pub:item>
                         </pub:values>
                         </pub:item>
                         <pub:item>
                         <pub:name>P_END_DATE</pub:name>
                         <pub:values>
                              <!--Zero or more repetitions:-->
                              <pub:item>{self.to_date}</pub:item>
                         </pub:values>
                         </pub:item>
                         <pub:item>
                         <pub:name>p_emp_number</pub:name>
                         <pub:values>
                              <!--Zero or more repetitions:-->
                         <pub:item></pub:item>
                         </pub:values>
                         </pub:item>
                         </pub:parameterNameValues>
                         </pub:reportRequest>
                         <pub:appParams/>
                    </pub:runReport>
               </soap:Body>
          </soap:Envelope>"""
          return payload


     def sent_request(self, payload):
          # SOAP request URL
          url = "https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/xmlpserver/services/ExternalReportWSSService?wsdl"
          user_name = 'Integration.Shoura'
          password = 'Int_123456'
          # headers
          base64string = base64.encodestring(
               ('%s:%s' % (user_name, password)).encode()).decode().strip()
          headers = {'Content-Type': 'application/soap+xml; charset=utf-8',
                    "Authorization": "Basic %s" % base64string}
          # POST request
          response = requests.request("POST", url, headers=headers, data=payload)
          if response.status_code == 200:
               return response
          else:
               print(response.status_code)
               messages.error(self.request, 'something wrong please connect to your admin')
               return redirect('payroll_run:create-salary')     





     def decode_response(self, response):
          response_xml_as_string = response.text
          responseXml = ET.fromstring(response_xml_as_string)
          namespaces = {'env': 'http://www.w3.org/2003/05/soap-envelope',
                         'ns2': 'http://xmlns.oracle.com/oxp/service/PublicReportService'}
          names = responseXml.findall(
               './env:Body'
               '/ns2:runReportResponse'
               '/ns2:runReportReturn'
               '/ns2:reportBytes',
               namespaces,
          )
          for name in names:
               code = name.text
          data = base64.b64decode(code)
          DATA_DS = ET.fromstring(data)
          return DATA_DS

     
     
     def get_employees_absences(self, DATA_DS):
          for employee_data in DATA_DS.getiterator('G_1'):
               for data in employee_data:
                   if data.tag == 'EMP_NUMBER':
                         emp_number = data.text
                         employee_company = self.check_if_employee_in_active_company(emp_number)
                         if employee_company:
                              self.employees_have_absences.append(emp_number)
                              self.assigen_employee_absences(emp_number,employee_data)     




     def check_if_employee_in_active_company(self,emp_number):
          employee_element = Employee_Element.objects.filter(emp_id__emp_number = emp_number)
          if len(employee_element) > 0 :
               if employee_element.first().emp_id.enterprise == self.request.user.company:
                    return True
               else:
                    return False  






     def assigen_absences_days_to_employee(self,employee_absences_days,absence_type_id,emp_number):
          employee_element = None
          absence_type_name = self.absence_types(absence_type_id)
          if absence_type_name is not None:
               try:
                    employee_element = Employee_Element.objects.get(element_id__element_name= absence_type_name, emp_id__emp_number= emp_number)
               except Employee_Element.DoesNotExist:
                    if absence_type_name == 'SickLeave Days':
                         try:
                              employee_element = Employee_Element.objects.get(element_id__element_name= 'SickLeave Days_25', emp_id__emp_number= emp_number)
                         except Employee_Element.DoesNotExist:
                              self.employees_not_have_absence_element.append('this employee '+emp_number+' not have element '+ absence_type_name )
                    else:
                         self.employees_not_have_absence_element.append('this employee '+emp_number+' not have element '+ absence_type_name )
               if employee_element is not None:
                    if absence_type_name == 'SickLeave Days_25' or absence_type_name == 'SickLeave Days':
                         sick_leave_days_obj = ImportSickLeaveDays(self.from_date , self.to_date,employee_element)
                         sick_leave_days_obj.run_class()
                    else:
                         employee_element.element_value = float(employee_absences_days)
                         employee_element.last_update_date = date.today()
                         employee_element.save()
          
          
              
     





     def assigen_employee_absences(self,emp_number,employee_data):
          for data in employee_data:
               if data.tag == 'EMP_NUMBER' and data.text == emp_number:
                    absence_type_id = employee_data.find("ABSENCE_TYPE_ID").text
                    employee_absences_days = employee_data.find("DAYS").text
                    self.assigen_absences_days_to_employee(employee_absences_days,int(absence_type_id),emp_number)



                                        

     def run_employee_absence(self):
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          # self.make_absence_element_zero_to_employees_imported_today()
          self.get_employees_absences(DATA_DS)
          self.make_employee_elements_values_zero_exclude_have_penalites()
          return self.employees_not_have_absence_element
          






