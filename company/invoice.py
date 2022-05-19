from payroll_run.models  import Element
from django.db.models import Q
from datetime import date
from datetime import datetime
from company.models import Department 
from employee.models import JobRoll , Employee_Element_History , Employee
from payroll_run.models import Salary_elements
from django.db.models.aggregates import Sum
import calendar
import requests
from calendar import monthrange
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
          # run_date = str(self.year)+'-'+str(self.month).zfill(2)+'-01'
          from_date = str(self.year)+'-'+str(self.month).zfill(2)+'-01'
          last_day_in_month  = monthrange(self.year, self.month)[1] # like: num_days = 28
          to_date = str(self.year)+'-'+str(self.month).zfill(2)+'-'+str(last_day_in_month)
          # emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=self.user.company).filter(
          #                                         Q(end_date__gte=run_date)| Q(end_date__isnull=True,emp_id__terminationdate__isnull=True)).filter(
          #                                              Q(emp_id__emp_end_date__gte=run_date ,emp_id__terminationdate__gte=run_date) | 
          #                                                   Q(emp_id__emp_end_date__isnull=True,emp_id__terminationdate__isnull=True))                        
          
          emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=self.user.company).filter(Q(end_date__gte=from_date) |Q(end_date__lte=to_date) |
             Q(end_date__isnull=True)).filter(Q(emp_id__emp_end_date__gte=from_date) |Q(emp_id__emp_end_date__lte=to_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
            Q(emp_id__terminationdate__gte=from_date)|Q(emp_id__terminationdate__lte=to_date) |Q(emp_id__terminationdate__isnull=True))
        
          # emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=self.user.company).filter(Q(end_date__gte=from_date)  |Q(end_date__isnull=True)).filter(
          #      Q(emp_id__emp_end_date__gte=from_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
          #   Q(emp_id__terminationdate__gte=from_date) |Q(emp_id__terminationdate__isnull=True))
          # for i in   emp_job_roll_query :
          #      print("lllllllll",i.emp_id.emp_number)
                


        
        

#  employees_list = JobRoll.objects.filter(emp_id__enterprise=request.user.company).filter(Q(end_date__gte=from_date) |Q(end_date__lte=to_date) |
#              Q(end_date__isnull=True)).filter(Q(emp_id__emp_end_date__gte=from_date) |Q(emp_id__emp_end_date__lte=to_date) | Q(emp_id__emp_end_date__isnull=True)).filter(
#             Q(emp_id__terminationdate__gte=from_date)|Q(emp_id__terminationdate__lte=to_date) |Q(emp_id__terminationdate__isnull=True))
        
          
          elements = Element.objects.filter(enterprise=self.user.company,account__isnull=False).filter((Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
          earning_elements = elements.filter(classification__code='earn').order_by("sequence")
          deduct_elements = elements.filter(classification__code='deduct').order_by("sequence")

          dept_list = Department.objects.filter(cost_center__isnull=False).filter(Q(end_date__gte=date.today()) |
                                                                           Q(end_date__isnull=True)).order_by('tree_id')

          lines_amount = 0.0
          department_list=[]
          # list1=[]
          # list2=[]
          emp_numbers_list=[]
          for dep in dept_list:
               jobroll_ids = emp_job_roll_query.filter(employee_department_oracle_erp_id=dep.oracle_erp_id)
               # .values_list("emp_id",flat=True) 
               for emp in jobroll_ids:
                    emp_jobroll = JobRoll.objects.filter(emp_id = emp.emp_id).first()
                    if emp_jobroll.emp_id.emp_number in emp_numbers_list:
                         # print(">>>>> ",emp_jobroll.emp_id.emp_number)
                         pass  
                    else:
                         emp_numbers_list.append(emp_jobroll.emp_id.emp_number)
               emps_ids = Employee.objects.filter(enterprise=self.user.company,emp_number__in = emp_numbers_list).filter(Q(emp_end_date__gte=from_date) |Q(emp_end_date__lte=to_date) | Q(emp_end_date__isnull=True)).filter(
               Q(terminationdate__gte=from_date)|Q(terminationdate__lte=to_date) |Q(terminationdate__isnull=True))
               
          #      for i in emps_ids:
          #           if i.emp_number in list1:
          #                list2.append(i.emp_number)
          #           else:
          #                list1.append(i.emp_number)
          # print("list1", list1)
          # print("list2", list2) 
               salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month=self.month,salary_year=self.year)    
               

               if supplier == 'EMPLOYEE INSURANCE':
                    insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
                    if insurance_amount is not None and insurance_amount > 0 :
                         lines_amount +=  insurance_amount
                         department_dic = {
                              'cost_center' : '0000',
                              'amount' : round(insurance_amount,2),
                              'type': 'employee_share'
                              }
                         department_list.append(department_dic)
                    company_insurance_amount = salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum']
                    if company_insurance_amount is not None and company_insurance_amount > 0 :
                         lines_amount +=  company_insurance_amount
                         department_dic = {
                              'cost_center' : dep.cost_center,
                              'amount' : round(company_insurance_amount,2),
                              'type': 'company_share'
                         }
                         department_list.append(department_dic)
     
               
               
               # elif supplier == 'COMPANY SHARE':
               #      company_insurance_amount = salary_elements_query.aggregate(Sum('company_insurance_amount'))['company_insurance_amount__sum']
               #      if company_insurance_amount is not None and company_insurance_amount > 0 :
               #           lines_amount +=  company_insurance_amount
               #           department_dic = {
               #                'cost_center' : dep.cost_center,
               #                'amount' : round(company_insurance_amount,2)

               #           }
               #           department_list.append(department_dic)

               elif supplier == 'SALARY TAX':
                    taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
                    if taxs is not None and taxs > 0 :
                         lines_amount += taxs
                    # else:
                    #      taxs = 0.0
                         department_dic = {
                              'cost_center' : '0000',
                              'amount' : round(taxs,2)
                         }
                         department_list.append(department_dic)
               
               elif supplier == 'Accrued salaries':
                    employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month= self.month,salary_year=self.year)
                    for element in earning_elements:
                         sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                         if sum_of_element is not None and sum_of_element >0  :
                              lines_amount += sum_of_element
                              if element.account[0] == '5':
                                   department_dic = {
                                        'cost_center' : dep.cost_center,
                                        'account' : element.account,
                                        'amount' : round(sum_of_element,2),
                                        'element_name' : element.element_name
                                   }
                              else:
                                   department_dic = {
                                        'cost_center' : '0000',
                                        'account' : element.account,
                                        'amount' : round(sum_of_element,2),
                                        'element_name' : element.element_name
                                        }
                              department_list.append(department_dic)
                    
                    for element in deduct_elements:
                         sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                         if sum_of_element is not None and sum_of_element > 0:
                              lines_amount -= sum_of_element
                         # else:
                         #      sum_of_element = 0.0
                              if element.account[0] == '5':
                                   department_dic = {
                                        'cost_center' : dep.cost_center,
                                        'account' : element.account,
                                        'amount' : -abs(round(sum_of_element,2)),
                                        'element_name' : element.element_name
                                   }
                              else:     
                                   department_dic = {
                                        'cost_center' : '0000',
                                        'cost_center' : dep.cost_center,
                                        'account' : element.account,
                                        'amount' : -abs(round(sum_of_element,2)),
                                        'element_name' : element.element_name
                                   }
                              department_list.append(department_dic)
                    insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
                    if insurance_amount is not None and insurance_amount > 0 :
                         lines_amount -=  insurance_amount
                         department_dic = {
                              'cost_center' : '0000',
                              'account':'261101',
                              'amount' : -abs(round(insurance_amount,2)),
                              'element_name' : 'Insurance'
                         }   
                         department_list.append(department_dic)
                    taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
                    if taxs is not None and taxs > 0 :
                         lines_amount -= taxs
                         department_dic = {
                              'cost_center' :'0000',
                              'account':'251103',
                              'amount' : -abs(round(taxs,2)),
                              'element_name' : 'Tax'
                         }
                         department_list.append(department_dic)     
          department_list.append(round(lines_amount,2))
          return department_list 
          
     




     def send_company_insurance_invoice(self):
          supplier = 'EMPLOYEE INSURANCE'
          lines = self.get_invoice_date('COMPANY SHARE')
          InvoiceAmount = lines.pop()
          invoiceLines = []
          for count,line in enumerate(lines):
               invoiceLines.append(
                    {
                         "LineNumber": count+1,
                         "LineAmount": line['amount'],  
                         "Description":'COMPANY SHARE',
                         "DistributionCombination":self.distribution_combination(self.user.company.company_segment,line['cost_center'],'531104',self.user.company.company_segment),
                         "invoiceDistributions": [{
                              "DistributionLineNumber": 1,
                              "DistributionLineType": "Item",
                              "DistributionAmount": line['amount'],
                              "DistributionCombination": self.distribution_combination(self.user.company.company_segment,line['cost_center'],'531104',self.user.company.company_segment)
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
          response = requests.post(self.url,verify=True, auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                              json=invoice_data)
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('company insurance invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('company insurance invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8")+ '/ ')












     def send_insurance_invoice(self):
          supplier = 'EMPLOYEE INSURANCE'
          lines = self.get_invoice_date(supplier)
          InvoiceAmount = lines.pop()
          invoiceLines = []
          for count,line in enumerate(lines):
               if line['type'] == 'company_share':
                    invoiceLines.append(
                    {
                    "LineNumber": count+1,
                    "LineAmount": line['amount'],  
                    "Description":'COMPANY SHARE',
                    "DistributionCombination":self.distribution_combination(self.user.company.company_segment,line['cost_center'],'531104',self.user.company.company_segment),
                    "invoiceDistributions": [{
                         "DistributionLineNumber": 1,
                         "DistributionLineType": "Item",
                         "DistributionAmount": line['amount'],
                         "DistributionCombination": self.distribution_combination(self.user.company.company_segment,line['cost_center'],'531104',self.user.company.company_segment)
                    }] }) 
               else:     
                    invoiceLines.append(
                         {
                         "LineNumber": count+1,
                         "LineAmount": line['amount'],  
                         "Description":'EMPLOYEE SHARE',
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
          response = requests.post(self.url,verify=True, auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                              json=invoice_data)
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('employee insurance invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('employee insurance invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8")+ '/ ')





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
                         "Description": line['element_name'],
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
          response = requests.post(self.url, verify=True,auth=HTTPBasicAuth(self.user_name, self.password),
                                   headers={'Content-Type': 'application/json'},
                              json=invoice_data)
          if response.status_code == 201:
               json_response =  json.loads(response.text)
               self.success_list.append('salaries invoice sent success, InvoiceNumber  is  '+json_response['InvoiceNumber']+ '/ ')

          else:
               self.error_list.append('salaries invoice did not sent, status code is  '+str(response.status_code)+' ,error is '+response.content.decode("utf-8")+ '/ ')

          




     def run_class(self):     
          # self.send_insurance_invoice()
          # self.send_company_insurance_invoice()
          # self.send_tax_invoice()
          self.send_salaries_invoice()
          return self.error_list , self.success_list   
