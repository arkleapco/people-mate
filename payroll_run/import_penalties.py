#!/usr/bin/env python
import requests
import base64
import xml.etree.ElementTree as ET
from django.core.checks import messages
from django.shortcuts import redirect
from employee.models import Employee_Element


class ImportPenalties:
     def __init__(self, request, employee, from_date , to_date):
          self.request = request
          self.employee = employee
          self.from_date = from_date
          self.to_date = to_date
          self.employees_not_have_penalties_element = None
          self.employees_error_in_response= None

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
                                   <pub:name>{self.employee.emp_number}</pub:name>
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
          try:
               response = requests.request("POST", url, headers=headers, data=payload)
               if response.status_code == 200:
                    return response
               else:
                    self.employees_error_in_response = self.employee.emp_name
          except:
               self.employees_error_in_response = self.employee.emp_name


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
          days = 0
          for employee_data in DATA_DS.getiterator('G_1'):
               for data in employee_data:
                    if data.tag == 'PENALITYDAYS':
                         PENALITY_DAYS = data.text
                         days += int(PENALITY_DAYS)
          try:
               employee_element = Employee_Element.objects.get(element_id__element_name='Penalties Days', emp_id = self.employee)
               employee_element.element_value = days
               employee_element.save()
          except Employee_Element.DoesNotExist:
               self.employees_not_have_penalties_element = self.employee.emp_name



        

     def run_employee_penalties(self):
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          self.get_employees_penalties(DATA_DS)
          return self.employees_not_have_penalties_element , self.employees_error_in_response 
          
