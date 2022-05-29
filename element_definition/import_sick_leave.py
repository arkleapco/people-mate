#!/usr/bin/env python
from datetime import date
import requests
import base64
import xml.etree.ElementTree as ET
from datetime import  date



class ImportSickLeaveDays:
     def __init__(self,from_date , to_date,employee_element_obj):
          self.employee_element_obj = employee_element_obj
          self.from_date = from_date
          self.to_date = to_date

     
     # def edit_date_format(self):
     #      start = self.from_date.strftime("%m-%d-%Y")
     #      end = self.to_date.strftime("%m-%d-%Y")
     #      self.from_date = start
     #      self.to_date = end



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
                    <pub:reportAbsolutePath> /Custom/Integration/SickLeaves/XX_SHOURA_SICK_LEAVE_REP.xdo</pub:reportAbsolutePath>
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
                              <pub:item>{self.employee_element_obj.emp_id.emp_number}</pub:item>
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
          base64string = base64.encodebytes(
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

     def get_employees_sick_leave_days(self, DATA_DS):
          for employee_data in DATA_DS.iter():
               for data in employee_data:
                    if data.text == 'SickLeave Days_25' or data.text == 'SickLeave Days_100' or data.text == 'SickLeave Days_15':
                         emp_days = float(employee_data.find("DAYS").text)
                         self.assigen_days_to_employee(emp_days)     


     def assigen_days_to_employee(self,emp_days):  
          # if self.more_than_recored == True:
          #      self.employee_element_obj.element_value += emp_days
          # elif self.more_than_recored == False:     
          self.employee_element_obj.element_value = emp_days
          self.employee_element_obj.last_update_date = date.today()
          self.employee_element_obj.save()
          
        

     def run_class(self):
          # self.edit_date_format()
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          self.get_employees_sick_leave_days(DATA_DS)


