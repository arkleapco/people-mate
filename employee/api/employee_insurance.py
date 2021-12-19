from company.api.serializer import *
import requests
from requests.auth import HTTPBasicAuth 




class EmployeeInsurance:
     def __init__(self, user,employee_links,employee_obj):
          self.employee_links = employee_links
          self.employee =employee_obj
          self.user = user
          self.user_name = 'Integration.Shoura'
          self.password = 'Int_123456'
          self.employee_not_assigen_insured = []



     def get_emp_hash_key_part(self): #1
          assignments_oracle_link = list(filter(lambda link: link['name'] == 'assignments', self.employee_links))
          assignments = assignments_oracle_link[0]['href']
          assignments_list = list(assignments.split("/"))
          return assignments_list[7]   


     def get_insurance_url(self,emp_hash_key_part): #2
          first_part = 'https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com:443/hcmRestApi/resources/11.13.18.05/emps/'
          insurance_url = first_part+emp_hash_key_part+'/child/personExtraInformation/'+str(self.employee.oracle_erp_id)+'/child/PersonExtraInformationContextSocial__InsuranceprivateVO'
          return insurance_url


     def get_insurance_response(self, insurance_url): #3
          response = requests.get(insurance_url, auth=HTTPBasicAuth(self.user_name, self.password))
          employee_data =  response.json()["items"] 
          return employee_data




     def assignmen_employee_insurance(self,employee_data):
          try:
               if employee_data[0]['socialInsuranceStatus'] == 'Insured':
                    self.employee.insured = True
                    self.employee.insurance_number = employee_data[0]['socialInsuranceNumber'] 
                    self.employee.insurance_salary = employee_data[0]['socialInsuranceAmount'] 
               elif employee_data[0]['socialInsuranceStatus'] == 'Not Insured':
                    self.employee.insured = False
               else:   
                    self.employee.insured = True
                    self.employee.insurance_number = employee_data[0]['socialInsuranceNumber'] 
                    self.employee.retirement_insurance_salary = employee_data[0]['socialInsuranceAmount'] 
               self.employee.save()
          except Exception as e :
               print (e) 
               self.employee_not_assigen_insured.append(self.employee)



     def run_employee_insurance(self):
          hash_key = self.get_emp_hash_key_part() 
          insurance_url = self.get_insurance_url(hash_key)   
          insurance_response = self.get_insurance_response(insurance_url)
          self.assignmen_employee_insurance(insurance_response)
          return self.employee_not_assigen_insured








# https://fa-eqar-test-saasfaprod1.fa.ocs.oraclecloud.com:443/hcmRestApi/resources/11.13.18.05/emps/00020000000EACED0005770800005AF3109259850000004AACED00057372000D6A6176612E73716C2E4461746514FA46683F3566970200007872000E6A6176612E7574696C2E44617465686A81014B597419030000787077080000017DBB63800078/child/personExtraInformation/100000001579397/child/PersonExtraInformationContextSocial__InsuranceprivateVO
