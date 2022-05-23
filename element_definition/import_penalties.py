#!/usr/bin/env python
from datetime import date
import requests
import base64
import xml.etree.ElementTree as ET
from employee.models import Employee_Element


class ImportPenalties:
     def __init__(self, request, from_date , to_date):
          self.request = request
          self.from_date = from_date
          self.to_date = to_date
          self.employees_not_have_penalties_element = []


     def make_employee_elements_values_zeros_befor_import(self,emp_number):
          try:
               employee_element = Employee_Element.objects.get(element_id__element_name='Penalties Days', emp_id__emp_number = emp_number)
               employee_element.element_value = 0
          except Employee_Element.DoesNotExist:
               pass     


             

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
                                   <pub:reportAbsolutePath>/Custom/Integration/Penalties/XX_Shoura_Penalty_Rep.xdo</pub:reportAbsolutePath>
                                   <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                                   <pub:parameterNameValues>
                                        <!--Zero or more repetitions:-->
                                        <pub:item>
                                        <pub:name>p_date</pub:name>
                                        <pub:values>
                                             <!--Zero or more repetitions:-->
                                             <pub:item>{self.from_date}</pub:item> 
                                   </pub:values>
                                   </pub:item>
                                   <pub:item>
                                   <pub:name>p_to_date</pub:name>
                                   <pub:values>
                                        <!--Zero or more repetitions:-->
                                        <pub:item>{self.to_date}</pub:item> 
                                   </pub:values>
                                   </pub:item>
                                   <pub:item>
                                   <pub:name></pub:name>
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

     
     
     def get_employees_penalties(self, DATA_DS):
          for employee_data in DATA_DS.getiterator('G_1'):
               for data in employee_data:
                    if data.tag == 'EMP_NUMBER':
                         emp_number = data.text
                         employee_company = self.check_if_employee_in_active_company(emp_number)
                         if employee_company:
                              self.make_employee_elements_values_zeros_befor_import(emp_number)
                              emp_days = self.check_employee_recordes(emp_number,DATA_DS)
                              self.assigen_days_to_employee(emp_number,emp_days)     

     
     def check_if_employee_in_active_company(self,emp_number):
          employee_element = Employee_Element.objects.filter(emp_id__emp_number = emp_number)
          if len(employee_element) > 0 :
               if employee_element.first().emp_id.enterprise == self.request.user.company:
                    return True
               else:
                    return False     






          
     def check_employee_recordes(self,emp_number,DATA_DS):
          emp_days= 0
          for employee_data in DATA_DS.getiterator('G_1'):
               for data in employee_data:
                    if data.tag == 'EMP_NUMBER' and data.text == emp_number:
                         emp_days += float(employee_data.find("PENALITYDAYS").text)
          # for data in employee_data:
          #      if data.tag == 'EMP_NUMBER' and data.text == emp_number:
          #           emp_days += float(employee_data.find("PENALITYDAYS").text)
          return emp_days                   

     def assigen_days_to_employee(self,emp_number,emp_days):  
          try:
               employee_element = Employee_Element.objects.get(element_id__element_name='Penalties Days', emp_id__emp_number = emp_number)
               employee_element.element_value = emp_days
               employee_element.last_update_date = date.today()
               employee_element.save()
          except Employee_Element.DoesNotExist:
               self.employees_not_have_penalties_element.append(emp_number)



        

     def run_employee_penalties(self):
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          self.get_employees_penalties(DATA_DS)
          return self.employees_not_have_penalties_element
          


