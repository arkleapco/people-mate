#!/usr/bin/env python	
from datetime import date
from os import EX_CANTCREAT
import requests
import base64
import xml.etree.ElementTree as ET
from django.contrib import messages
from datetime import datetime, timedelta
from django.shortcuts import  redirect





class EmployeeLastupdatedateReport:
   def __init__(self,request, last_update_date):
      self.request = request
      self.last_update_date = last_update_date





   def put_lastupdatedate_in_payload(self):
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
                  <pub:reportAbsolutePath>/Custom/Integration/PM8_Updates/PM8_Intgeration_Report.xdo</pub:reportAbsolutePath>
                  <pub:sizeOfDataChunkDownload>-1</pub:sizeOfDataChunkDownload>
                  <pub:parameterNameValues>
                     <!--Zero or more repetitions:-->
                     <pub:item>
                        <pub:name>ass_update_date</pub:name>
                        <pub:values>
                           <!--Zero or more repetitions:-->
                           <pub:item>{self.last_update_date}</pub:item>
                        </pub:values>
                     </pub:item>
                  </pub:parameterNameValues>
               </pub:reportRequest>
               <pub:appParams/>
            </pub:runReport>
         </soap:Body>
      </soap:Envelope>"""
      return payload



   def sent_request(self,payload ):
      # SOAP request URL
      url ="https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/xmlpserver/services/ExternalReportWSSService?wsdl"
      user_name = 'Integration.Shoura'
      password = 'Int_123456'
      # headers
      base64string = base64.encodestring(('%s:%s' % (user_name,password)).encode()).decode().strip()
      headers = {'Content-Type': 'application/soap+xml; charset=utf-8',"Authorization" : "Basic %s" % base64string}
      # POST request
      response = requests.request("POST", url,headers=headers , data=payload)
      if response.status_code == 200:
         return response
      else:
         print("errrrrrrrrror", response, response.content)
         return False
         # messages.error(self.request,"some thing wrong when sent request to last update date api , please connect to the adminstration ")
         # return redirect('employee:list-employee')   
      
            





   def decode_response(self, response):
      response_xml_as_string = response.text
      responseXml = ET.fromstring(response_xml_as_string)
      namespaces = {'env':'http://www.w3.org/2003/05/soap-envelope','ns2':'http://xmlns.oracle.com/oxp/service/PublicReportService'}
      names = responseXml.findall(
         './env:Body'
         '/ns2:runReportResponse'
         '/ns2:runReportReturn'
         '/ns2:reportBytes',
         namespaces,
      )
      for name in names:
         code=name.text
      data=base64.b64decode(code)
      DATA_DS = ET.fromstring(data)
      return DATA_DS
         

   def get_employees_last_update_date(self, DATA_DS):
      person_id = ''
      person_num= ''
      employees_data = {'PersonId':person_id,'PersonNum':person_num}
      employees_data_list = []
      for employee_data in DATA_DS.getiterator('G_1'):
         for data in employee_data:
            if data.tag == 'PERSON_ID':
               person_id = data.text
            if data.tag == 'PERSON_NUM':  
               person_num = data.text
         
         employees_data={'PersonId':int(person_id), 'PersonNum':person_num}
         employees_data_list.append(employees_data)
      return employees_data_list
     


   def run_employee_lastupdatedate_report(self):
      payload= self.put_lastupdatedate_in_payload()
      response =  self.sent_request(payload)
      if response:
         DATA_DS = self. decode_response(response)
         employees_list = self.get_employees_last_update_date(DATA_DS)
         return employees_list
      else:
         return False   
      








# obj = EmployeeLastupdatedateReport('request','01-01-2022')
# s = obj.put_lastupdatedate_in_payload()
# response = obj.sent_request(s)
# print(response)
