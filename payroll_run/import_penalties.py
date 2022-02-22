#!/usr/bin/env python
from datetime import date
import requests
import base64
import xml.etree.ElementTree as ET
from django.core.checks import messages
from django.shortcuts import redirect
from employee.models import Employee_Element


class ImportPenalties:
     def __init__(self, request, from_date , to_date):
          self.request = request
          # self.employee = employee
          self.from_date = from_date
          self.to_date = to_date
          self.employees_not_have_penalties_element = []

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
                         emp_days = self.check_employee_recordes(emp_number,DATA_DS)
                         self.assigen_days_to_employee(emp_number,emp_days)     

          
     def check_employee_recordes(self,emp_number,DATA_DS):
          emp_days= 0
          for employee_data in DATA_DS.getiterator('G_1'):
               for data in employee_data:
                    if data.tag == 'EMP_NUMBER' and data.text == emp_number:
                         emp_days += int(employee_data.find("PENALITYDAYS").text)
          return emp_days                   

     def assigen_days_to_employee(self,emp_number,emp_days):  
          try:
               employee_element = Employee_Element.objects.get(element_id__element_name='Penalties Days', emp_id__emp_number = emp_number)
               employee_element.element_value = emp_days
               employee_element.save()
          except Employee_Element.DoesNotExist:
               self.employees_not_have_penalties_element.append(emp_number)



        

     def run_employee_penalties(self):
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          self.get_employees_penalties(DATA_DS)
          return self.employees_not_have_penalties_element
          






# <Element 'EMP_NUMBER' at 0x7fc3bf6ea250>
# <Element 'PERSON_ID' at 0x7fc3bf6ea4c0>
# <Element 'PENALITYDAYS' at 0x7fc3bf724eb0>



# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf724cd0>
# <Element 'EMP_NUMBER' at 0x7fc3bf7242b0>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf7249d0>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf724040>
# <Element 'PERSON_ID' at 0x7fc3bf7248b0>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf724130>
# <Element 'PENALTYDATE' at 0x7fc3bf7247f0>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf724640>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf724a60>
# <Element 'PENALITYDAYS' at 0x7fc3bf724250>


# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf724610>
# <Element 'EMP_NUMBER' at 0x7fc3bf724e20>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf724b50>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7240d0>
# <Element 'PERSON_ID' at 0x7fc3bf7244c0>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf724700>
# <Element 'PENALTYDATE' at 0x7fc3bf724280>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf724a90>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf724850>
# <Element 'PENALITYDAYS' at 0x7fc3bf724f10>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf724160>
# <Element 'EMP_NUMBER' at 0x7fc3bf724310>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf724d00>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7249a0>
# <Element 'PERSON_ID' at 0x7fc3bf724760>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf724790>
# <Element 'PENALTYDATE' at 0x7fc3bf724df0>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7244f0>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf724ca0>
# <Element 'PENALITYDAYS' at 0x7fc3bf724940>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf724c10>
# <Element 'EMP_NUMBER' at 0x7fc3bf7243d0>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf724190>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf724070>
# <Element 'PERSON_ID' at 0x7fc3bf7241f0>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf724e80>
# <Element 'PENALTYDATE' at 0x7fc3bf724af0>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7245e0>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf724730>
# <Element 'PENALITYDAYS' at 0x7fc3bf724c70>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf7e5ca0>
# <Element 'EMP_NUMBER' at 0x7fc3bf7e5790>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf7e5070>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7e50d0>
# <Element 'PERSON_ID' at 0x7fc3bf7e5850>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf7e5f10>
# <Element 'PENALTYDATE' at 0x7fc3bf7e5280>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7e5730>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf7e50a0>
# <Element 'PENALITYDAYS' at 0x7fc3bf7e5310>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf7e5400>
# <Element 'EMP_NUMBER' at 0x7fc3bf7e5130>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf7e56d0>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7e5cd0>
# <Element 'PERSON_ID' at 0x7fc3bf7e5250>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf7e5d00>
# <Element 'PENALTYDATE' at 0x7fc3bf7e5190>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7e57c0>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf7e5e20>
# <Element 'PENALITYDAYS' at 0x7fc3bf7e5760>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf7e59d0>
# <Element 'EMP_NUMBER' at 0x7fc3bf7e5550>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf7e5fd0>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7e5430>
# <Element 'PERSON_ID' at 0x7fc3bf7e5910>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf7e5460>
# <Element 'PENALTYDATE' at 0x7fc3bf7e5100>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7e5df0>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf7e5f70>
# <Element 'PENALITYDAYS' at 0x7fc3bf7e5ee0>
# <Element 'DOCUMENT_TYPE_ID' at 0x7fc3bf7e5970>
# <Element 'EMP_NUMBER' at 0x7fc3bf7e51f0>
# <Element 'DOCUMENTS_OF_RECORD_ID' at 0x7fc3bf7e5f40>
# <Element 'DOCUMENT_CODE' at 0x7fc3bf7e5940>
# <Element 'PERSON_ID' at 0x7fc3bf7e5be0>
# <Element 'DEI_ATTRIBUTE_CATEGORY' at 0x7fc3bf7e5040>
# <Element 'PENALTYDATE' at 0x7fc3bf7e53a0>
# <Element 'PENALITYEN_DESC' at 0x7fc3bf7e5af0>
# <Element 'PENALITYAR_DESC' at 0x7fc3bf7e52e0>
# <Element 'PENALITYDAYS' at 0x7fc3bf7e58e0>