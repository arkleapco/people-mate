from payroll_run.models  import Element
from django.db.models import Q
from datetime import date
from datetime import datetime
from company.models import Department 
from employee.models import JobRoll , Employee_Element_History
from payroll_run.models import Salary_elements
from django.db.models.aggregates import Sum
import calendar
import requests
from requests.auth import HTTPBasicAuth 
import json
import random




class Send_Invoice:

     def __init__(self, user, month,year):
          self.month = month
          self.year = year
          self.user = user
          self.user_name = 'Integration.Shoura'
          self.password = '12345678'
          self.url = 'https://fa-eqar-TEST-saasfaprod1.fa.ocs.oraclecloud.com:443/fscmRestApi/resources/11.13.18.05/invoices'
          self.error_list = []
          self.success_list = []
          







     def invoice_number_compaination(self,supplier,mon,year):
          #"InvoiceNumber": "Jan-21-Salaries1",
          month = calendar.month_abbr[mon]
          year = str(year)[-2:]
          random_num = random.random()
          invoice_number = f'{month}-{year}-{supplier}-{random_num}'
          return invoice_number


     def distribution_combination(self,company_segment,cost_center,account,intercompany):
          #DistributionCombination = 'company_segment.Cost Center.Account.Product.Project.Intercompany.Future  1.Future 2'
          #'company_segment - Cost Center - Account - 0000 - 0000 - Intercompany-0000- 0000'
          distribution_combination = f'{company_segment}-{cost_center}-{account}-0000-000-{intercompany}-0000-0000'
          return distribution_combination


     def get_string_date(self):
          today_date = datetime.now()
          date_time_str = today_date.strftime("%Y-%m-%d")
          return date_time_str



          




     def get_invoice_date(self,supplier):
          run_date = str(self.year)+'-'+str(self.month).zfill(2)+'-01'
          emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=self.user.company).filter(
                                                  Q(end_date__gte=run_date)| Q(end_date__isnull=True,emp_id__terminationdate__isnull=True)).filter(
                                                       Q(emp_id__emp_end_date__gte=run_date ,emp_id__terminationdate__gte=run_date) | 
                                                            Q(emp_id__emp_end_date__isnull=True,emp_id__terminationdate__isnull=True))                        

          
          elements = Element.objects.filter(enterprise=self.user.company,supplier_name__isnull=False).filter((Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
          earning_elements = elements.filter(classification__code='earn').order_by("sequence")
          deduct_elements = elements.filter(classification__code='deduct').order_by("sequence")

          dept_list = Department.objects.filter(cost_center__isnull=False).filter(Q(end_date__gte=date.today()) |
                                                                           Q(end_date__isnull=True)).order_by('tree_id')
          lines_amount = 0.0
          department_list=[]
          for dep in dept_list:
               emp_job_roll_list = emp_job_roll_query.filter(position__department=dep).values_list("emp_id",flat=True)   
               emps_ids = set(emp_job_roll_list) #get uniqe only
               
               salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month=self.month,salary_year=self.year)          
               
               if supplier == 'EMPLOYEE INSURANCE':
                    insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
                    if insurance_amount is not None and insurance_amount > 0 :
                         lines_amount +=  insurance_amount
                    # else:
                    #      insurance_amount = 0.0
                         department_dic = {
                              'cost_center' : dep.cost_center,
                              'amount' : -abs(round(insurance_amount,2))
                         }
                         department_list.append(department_dic)

               elif supplier == 'SALARY TAX':
                    taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
                    if taxs is not None and taxs > 0 :
                         lines_amount += taxs
                    # else:
                    #      taxs = 0.0
                         department_dic = {
                              'cost_center' : dep.cost_center,
                              'amount' : -abs(round(taxs,2))
                         }
                         department_list.append(department_dic)
               
               elif supplier == 'Accrued salaries':
                    employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month= self.month,salary_year=self.year)
                    for element in earning_elements:
                         sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                         if sum_of_element is not None and sum_of_element >0  :
                              lines_amount += sum_of_element
                         # else:
                         #      sum_of_element = 0.0
                              department_dic = {
                              'cost_center' : dep.cost_center,
                              'account' : element.account,
                              'amount' : round(sum_of_element,2)
                                   }
                              department_list.append(department_dic)
                    
                    for element in deduct_elements:
                         sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                         if sum_of_element is not None and sum_of_element > 0:
                              lines_amount -= sum_of_element
                         # else:
                         #      sum_of_element = 0.0
                              department_dic = {
                              'cost_center' : dep.cost_center,
                              'account' : element.account,
                              'amount' : -abs(round(-sum_of_element,2))
                              }
                              department_list.append(department_dic)
                    insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
                    if insurance_amount is not None and insurance_amount > 0 :
                         lines_amount -=  insurance_amount
                         department_dic = {
                              'cost_center' : dep.cost_center,
                              'account':'261101',
                              'amount' : -abs(round(insurance_amount,2))
                         }   
                         department_list.append(department_dic)
                    taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
                    if taxs is not None and taxs > 0 :
                         lines_amount -= taxs
                         department_dic = {
                              'cost_center' : dep.cost_center,
                              'account':'251103',
                              'amount' : -abs(round(taxs,2))
                         }
                         department_list.append(department_dic)     
          department_list.append(round(lines_amount,2))
          return department_list 
               
     
     



     def send_insurance_invoice(self):
          supplier = 'EMPLOYEE INSURANCE'
          lines = self.get_invoice_date(supplier)
          InvoiceAmount = lines.pop()
          invoiceLines = []
          for count,line in enumerate(lines):
               invoiceLines.append(
                    {
                         "LineNumber": count+1,
                         "LineAmount": line['amount'],  
                         "Description":'EMPLOYEE INSURANCE',
                         "DistributionCombination":self.distribution_combination(self.user.company.company_segment,line['cost_center'],'261101',self.user.company.company_segment),
                         "invoiceDistributions": [{
                              "DistributionLineNumber": 1,
                              "DistributionLineType": "Item",
                              "DistributionAmount": line['amount'],
                              "DistributionCombination": self.distribution_combination(self.user.company.company_segment,line['cost_center'],'261101',self.user.company.company_segment)
                    }] })     
          business_name = self.user.company.name
          invoice_data = {
               "InvoiceNumber": self.invoice_number_compaination(supplier,self.month,self.year),
               "InvoiceCurrency": "EGP",
               "InvoiceAmount": InvoiceAmount,
               "InvoiceDate": self.get_string_date(),
               "BusinessUnit":  business_name,
               "Supplier" : 'EMPLOYEE INSURANCE',
               "PaymentMethodCode": "CHECK",
               "PaymentMethod": "Check",
               "PaymentTerms": "Immediate",
               "SupplierSite": "EGYPT",
               "InvoiceSource": "Manual invoice entry",
               "InvoiceType": "Standard",
               "Description": self.invoice_number_compaination(supplier,self.month,self.year),
               "attachments": [],
               "invoiceInstallments":[],
               "invoiceLines": invoiceLines,
          }
          print("111", invoice_data)
          response = requests.post(self.url,verify=True, auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                              json=invoice_data)
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('insurance invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('insurance invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8")+ '/ ')





     def send_tax_invoice(self):
          supplier = 'SALARY TAX'
          lines = self.get_invoice_date(supplier)
          InvoiceAmount = lines.pop()
          invoiceLines = []
          for count,line in enumerate(lines):
               invoiceLines.append(
                    {
                         "LineNumber": count+1,
                         "LineAmount": line['amount'],  
                         "Description":'SALARY TAX',
                         "DistributionCombination":self.distribution_combination(self.user.company.company_segment,line['cost_center'],'251103',self.user.company.company_segment),
                         "invoiceDistributions": [{
                              "DistributionLineNumber": 1,
                              "DistributionLineType": "Item",
                              "DistributionAmount": line['amount'],
                              "DistributionCombination": self.distribution_combination(self.user.company.company_segment,line['cost_center'],'251103',self.user.company.company_segment)
                    }] })     
          business_name = self.user.company.name
          invoice_data = {
               "InvoiceNumber": self.invoice_number_compaination(supplier,self.month,self.year),
               "InvoiceCurrency": "EGP" ,
               "InvoiceAmount": InvoiceAmount,
               "InvoiceDate": self.get_string_date(),
               "BusinessUnit":  business_name,
               "Supplier" : 'SALARY TAX',
               "PaymentMethodCode": "CHECK",
               "PaymentMethod": "Check",
               "PaymentTerms": "Immediate",
               "SupplierSite": "EGYPT",
               "InvoiceSource": "Manual invoice entry",
               "InvoiceType": "Standard",
               "Description": self.invoice_number_compaination(supplier,self.month,self.year),
               "attachments": [],
               "invoiceInstallments":[],
               "invoiceLines": invoiceLines,
          }
          print("22222222", invoice_data)
          response = requests.post(self.url,verify=True, auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                                   json=invoice_data)
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('tax invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('tax invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8"+ '/ '))

     






     def send_salaries_invoice(self):
          supplier = 'Accrued salaries'
          lines = self.get_invoice_date(supplier)
          InvoiceAmount = lines.pop()
          invoiceLines = []
          for count,line in enumerate(lines):
               invoiceLines.append(
                    {
                         "LineNumber": count+1,
                         "LineAmount": line['amount'],  
                         "Description":'Accrued salaries',
                         "DistributionCombination":self.distribution_combination(self.user.company.company_segment,line['cost_center'],line['account'],self.user.company.company_segment),
                         "invoiceDistributions": [{
                              "DistributionLineNumber": 1,
                              "DistributionLineType": "Item",
                              "DistributionAmount": line['amount'],
                              "DistributionCombination": self.distribution_combination(self.user.company.company_segment,line['cost_center'],line['account'],self.user.company.company_segment)
                    }] })     
          business_name = self.user.company.name
          invoice_data = {
               "InvoiceNumber": self.invoice_number_compaination(supplier,self.month,self.year),
               "InvoiceCurrency": "EGP" ,
               "InvoiceAmount": InvoiceAmount,
               "InvoiceDate": self.get_string_date(),
               "BusinessUnit":  business_name,
               "Supplier" : 'Accrued salaries',
               "PaymentMethodCode": "CHECK",
               "PaymentMethod": "Check",
               "PaymentTerms": "Immediate",
               "SupplierSite": "Giza",
               "InvoiceSource": "Manual invoice entry",
               "InvoiceType": "Standard",
               "Description": self.invoice_number_compaination(supplier,self.month,self.year),
               "attachments": [],
               "invoiceInstallments":[],
               "invoiceLines": invoiceLines,
          }
          print("33333333", invoice_data)
          response = requests.post(self.url, verify=True,auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                              json=invoice_data)
          
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('insurance invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('salaries invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8")+ '/ ')

          




     def run_class(self):     
          self.send_insurance_invoice()
          self.send_tax_invoice()
          self.send_salaries_invoice()
          return self.error_list , self.success_list   
