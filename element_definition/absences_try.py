#!/usr/bin/env python	
import requests
import base64
from requests.auth import HTTPBasicAuth
import xml.etree.ElementTree as ET
from datetime import date


class ImportAbsences:
     def __init__(self, request, from_date , to_date):
          self.request = 'request'
          self.from_date = 'from_date'
          self.to_date = 'to_date'
          self.employees_not_have_absences_element = []





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
                              <pub:item>03-20-2022</pub:item>
                         </pub:values>
                         </pub:item>
                         <pub:item>
                         <pub:name>P_END_DATE</pub:name>
                         <pub:values>
                              <!--Zero or more repetitions:-->
                              <pub:item>04-20-2022</pub:item>
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
                    print (data.tag, data.text)
                    # if data.tag == 'EMP_NUMBER':
                    #      emp_number = data.text
                    #      if emp_number == '3009':
                    #           print("11111111111", emp_number)
                    #           employee_company = self.check_if_employee_in_active_company(emp_number)
                    #           if employee_company:
                    #                self.make_employee_elements_values_zeros_befor_import(emp_number)
                    #                emp_days = self.check_employee_recordes(emp_number,DATA_DS)
                    #                self.assigen_days_to_employee(emp_number,emp_days)     



     def run_employee_penalties(self):
          payload = self.replace_parameters_in_payload()
          response = self.sent_request(payload)
          DATA_DS = self. decode_response(response)
          self.get_employees_penalties(DATA_DS)
          # return self.employees_not_have_penalties_element
          








obj = ImportAbsences('request', 'from_date' , 'to_date')
obj.run_employee_penalties()









# EMP_NUMBER 4029
# ABSENCE_PAY_FACTOR 0
# PERSON_ID 100000001579432
# DAYS 2
# PAY_FACTOR_WITHOUT_OVERRIDE 0
# START_DATETIME 2022-03-20T00:00:00.000+00:00
# END_DATETIME 2022-04-06T00:00:00.000+00:00
# ABSENCE_TYPE_ID 300000002604275


# 3056

 for employee_data in DATA_DS.getiterator('G_1'):
EMP_NUMBER 4029
ABSENCE_PAY_FACTOR 0
PERSON_ID 100000001579432
DAYS 2
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-04-06T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604275

EMP_NUMBER 4072
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001571415
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-03-20T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002456556

EMP_NUMBER 1127
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001579504
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-04-02T00:00:00.000+00:00
END_DATETIME 2022-04-20T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604239

EMP_NUMBER 3018
ABSENCE_PAY_FACTOR 0
PERSON_ID 100000001579386
DAYS 14
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-04-02T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604311

EMP_NUMBER 3056
ABSENCE_PAY_FACTOR 0
PERSON_ID 100000001579477
DAYS 32
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-04-20T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604311
EMP_NUMBER 4101
ABSENCE_PAY_FACTOR 0
PERSON_ID 300000014299998
DAYS 1
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-03-20T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604275
EMP_NUMBER 4087
ABSENCE_PAY_FACTOR 0
PERSON_ID 300000013142240
DAYS 6
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-04-04T00:00:00.000+00:00
END_DATETIME 2022-04-09T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604311
EMP_NUMBER 2045
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001571508
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-03-24T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002456556
EMP_NUMBER 3081
ABSENCE_PAY_FACTOR 0
PERSON_ID 100000001579503
DAYS 32
PAY_FACTOR_WITHOUT_OVERRIDE 0
START_DATETIME 2022-03-20T00:00:00.000+00:00
END_DATETIME 2022-04-20T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604311
EMP_NUMBER 1130
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001571433
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-04-10T00:00:00.000+00:00
END_DATETIME 2022-04-10T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002456556
EMP_NUMBER 1082
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001571291
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-03-27T00:00:00.000+00:00
END_DATETIME 2022-03-31T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002604202
EMP_NUMBER 4098
ABSENCE_PAY_FACTOR 100
PERSON_ID 300000013162749
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-03-23T00:00:00.000+00:00
END_DATETIME 2022-03-24T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002456556
EMP_NUMBER 1129
ABSENCE_PAY_FACTOR 100
PERSON_ID 100000001571432
DAYS 0
PAY_FACTOR_WITHOUT_OVERRIDE 100
START_DATETIME 2022-03-27T00:00:00.000+00:00
END_DATETIME 2022-04-17T00:00:00.000+00:00
ABSENCE_TYPE_ID 300000002456628
(inv) gehad@arkleap:~/Desktop/work/people_8_shoura/people-mate-shoura/element_definition$ 