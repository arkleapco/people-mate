#!/usr/bin/env python	
import requests
import base64
import xml.etree.ElementTree as ET



class EmployeeLastupdatedateReport:
   def __init__(self, user,last_update_date):
      self.last_update_date = last_update_date
      self.user = user
      self.user_name = 'Integration.Shoura'
      self.password = 'Int_123456'



   def sent_payload(self):
      # structured XML
      payload = """<?xml version=\"1.0\" encoding=\"utf-8\"?>
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
                           <pub:item>01-01-2022</pub:item>
                        </pub:values>
                     </pub:item>
                  </pub:parameterNameValues>
               </pub:reportRequest>
               <pub:appParams/>
            </pub:runReport>
         </soap:Body>
      </soap:Envelope>"""
      # SOAP request URL
      self.url ="https://fa-eqar-saasfaprod1.fa.ocs.oraclecloud.com/xmlpserver/services/ExternalReportWSSService?wsdl"
      self.user_name = 'Integration.Shoura'
   # headers
   base64string = base64.encodestring(('%s:%s' % (user_name,password)).encode()).decode().strip()
   headers = {
      'Content-Type': 'application/soap+xml; charset=utf-8',"Authorization" : "Basic %s" % base64string
   }

# POST request
print(payload)	
response = requests.request("POST", url,headers=headers , data=payload)
  
# prints the response
print(response.text)
print(response)
response_xml_as_string = response.text
print(response_xml_as_string+"response_xml_as_string")
responseXml = ET.fromstring(response_xml_as_string)
#testId = responseXml.find('*/ns2:reportBytes')
#names = responseXml.findall('*/ns2:reportBytes')
#print (testId)
namespaces = {'env':'http://www.w3.org/2003/05/soap-envelope',
'ns2':'http://xmlns.oracle.com/oxp/service/PublicReportService'}
names = responseXml.findall(
   './env:Body'
    '/ns2:runReportResponse'
    '/ns2:runReportReturn'
    '/ns2:reportBytes',
    namespaces,
)
for name in names:
    S=name.text
    print(name.text)
Ss=base64.b64decode(S)
print(Ss)
myxml = ET.fromstring(Ss)
print(myxml)
for table in myxml.getiterator('G_1'):
    for child in table:
        print (child.tag, child.text)
#root= ET.tostring(myxml, encoding='utf8', method='xml')
#print(root)
#xml = ET.Element("PERSON_NUM", Name="John")
#print(myxml)
