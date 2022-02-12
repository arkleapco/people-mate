from django.http import response
from payroll_run.models  import Element
from django.db.models import Q
from django.shortcuts import HttpResponse
from datetime import date
from datetime import datetime
from company.models import Department 
from employee.models import JobRoll , Employee_Element_History
from payroll_run.models import Salary_elements
from django.db.models.aggregates import Sum
import calendar
import requests
from requests.auth import HTTPBasicAuth 
from django.contrib.auth.decorators import login_required
import json
import random

########### handel erorr

user_name = 'Mohamed.mahran@jawraa.com'
password = 'Jawraa@123456'




def invoice_number_compaination(supplier,mon,year):
     #"InvoiceNumber": "Jan-21-Salaries1",
     month = calendar.month_abbr[mon]
     year = str(year)[-2:]
     random_num = random.random()
     invoice_number = f'{month}-{year}-{supplier}-{random_num}'
     return invoice_number


def distribution_combination(company_segment,cost_center,account,intercompany):
     #DistributionCombination = 'company_segment.Cost Center.Account.Product.Project.Intercompany.Future  1.Future 2'
     #'company_segment - Cost Center - Account - 0000 - 0000 - Intercompany-0000- 0000'
     distribution_combination = f'{company_segment}.{cost_center}.{account}.0000.0000.{intercompany}.0000.0000'
     return distribution_combination


def get_string_date():
     today_date = datetime.now()
     date_time_str = today_date.strftime("%Y-%m-%d")
     return date_time_str



     




def get_invoice_date_as_excel(month,year,supplier,user):
     run_date = str(year)+'-'+str(month).zfill(2)+'-01'
     emp_job_roll_query = JobRoll.objects.filter(emp_id__enterprise=user.company).filter(
                                             Q(end_date__gte=run_date)| Q(end_date__isnull=True,emp_id__terminationdate__isnull=True)).filter(
                                                  Q(emp_id__emp_end_date__gte=run_date ,emp_id__terminationdate__gte=run_date) | 
                                                       Q(emp_id__emp_end_date__isnull=True,emp_id__terminationdate__isnull=True))                        

     
     dept_list = Department.objects.filter(cost_center__isnull=False).filter(Q(end_date__gte=date.today()) |
                                                                      Q(end_date__isnull=True)).order_by('tree_id')
     lines_amount = 0.0
     department_list=[]
     for dep in dept_list:
          emp_job_roll_list = emp_job_roll_query.filter(position__department=dep).values_list("emp_id",flat=True)   
          emps_ids = set(emp_job_roll_list) #get uniqe only
          
          salary_elements_query= Salary_elements.objects.filter(emp_id__in = emps_ids,salary_month=month,salary_year=year)          
          
          if supplier == 'EMPLOYEE INSURANCE':
               insurance_amount = salary_elements_query.aggregate(Sum('insurance_amount'))['insurance_amount__sum']
               if insurance_amount is not None:
                    lines_amount +=  insurance_amount
               else:
                    insurance_amount = 0.0
               department_dic = {
                    'cost_center' : dep.cost_center,
                    'amount' : round(insurance_amount,2)
               }
               department_list.append(department_dic)

          elif supplier == 'SALARY TAX':
               taxs = salary_elements_query.aggregate(Sum('tax_amount'))['tax_amount__sum']  
               if taxs is not None:
                    lines_amount += taxs
               else:
                    taxs = 0.0
               department_dic = {
                    'cost_center' : dep.cost_center,
                    'amount' : round(taxs,2)
               }
               department_list.append(department_dic)
          
          elif supplier == 'Accrued salaries':
               elements = Element.objects.filter(enterprise=user.company,supplier_name__isnull=False).filter((Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
               earning_elements = elements.filter(classification__code='earn').order_by("sequence")
               deduct_elements = elements.filter(classification__code='deduct').order_by("sequence")
               employees_elements_query = Employee_Element_History.objects.filter(emp_id__in=emps_ids,salary_month= month,salary_year=year)

               
               for element in earning_elements:
                    sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                    if sum_of_element is not None:
                         lines_amount += sum_of_element
                    else:
                         sum_of_element = 0.0
                    department_dic = {
                    'cost_center' : dep.cost_center,
                    'account' : element.supplier_name,
                    'amount' : round(sum_of_element,2)
                         }
                    department_list.append(department_dic)
               
               for element in deduct_elements:
                    sum_of_element = employees_elements_query.filter(element_id=element).aggregate(Sum('element_value'))['element_value__sum']
                    if sum_of_element is not None:
                         lines_amount += sum_of_element
                    else:
                         sum_of_element = 0.0
                    department_dic = {
                    'cost_center' : dep.cost_center,
                    'account' : element.supplier_name,
                    'amount' : round(sum_of_element,2)
                    }
                    department_list.append(department_dic)
     department_list.append(round(lines_amount))
     print(department_list)
     print("****************************************")
     return department_list 
           
  
    



def send_insurance_invoice(request,month,year):
     supplier = 'EMPLOYEE INSURANCE'
     lines = get_invoice_date_as_excel(month,year,supplier,request.user)
     InvoiceAmount = lines.pop()
     invoiceLines = []
     for count,line in enumerate(lines):
          invoiceLines.append(
               {
                    "LineNumber": count+1,
                    "LineAmount": line['amount'],  
                    "Description":'EMPLOYEE INSURANCE',
                    "invoiceDistributions": [{
                         "DistributionLineNumber": 1,
                         "DistributionLineType": "Item",
                         "DistributionAmount": line['amount'],
                         # "DistributionCombination": distribution_combination(request.user.company.company_segment,line['cost_center'],'EMPLOYEE INSURANCE',request.user.company.company_segment)
                         "DistributionCombination": "01.00.00000.00.41632.0000.00.00.00"
               }] })     
     
     invoice_data = {
          "InvoiceNumber": invoice_number_compaination(supplier,month,year),
          # "InvoiceCurrency": "EG" for shoura,
          "InvoiceCurrency": "SAR",
          "InvoiceAmount": InvoiceAmount,
          "InvoiceDate": get_string_date(),
          # "BusinessUnit":  "Shoura",
          "BusinessUnit":  "Future Networks Telecom Company BU",
          # "Supplier" : 'EMPLOYEE INSURANCE',
          "Supplier" : "Petty cash atheer practise",
          "PaymentMethodCode": "CHECK",
          "PaymentMethod": "Check",
          "PaymentTerms": "Immediate",
          # "SupplierSite": "EGYPT",
          "SupplierSite": "Riyadh",
          "InvoiceSource": "Manual invoice entry",
          "InvoiceType": "Standard",
          "Description": invoice_number_compaination(supplier,month,year),
           "attachments": [],
          "invoiceInstallments":[],
          "invoiceLines": invoiceLines,
     }
     print(invoice_data)
     url = 'https://fa-euuk-test-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/invoices'
     response = requests.post(url, auth=HTTPBasicAuth(user_name, password),
                              headers={'Content-Type': 'application/json'},
                            json=invoice_data)
     # print(response) 
     # print("content:", response.content)                         
     json_response =  json.loads(response.text)
     if response == 201:
          print("json_response:",json_response)
     else:
          print("json_response:",json_response,"erooooooooooor")     
     




def send_tax_invoice(request,month,year):
     supplier = 'SALARY TAX'
     lines = get_invoice_date_as_excel(month,year,supplier,request.user)
     InvoiceAmount = lines.pop()
     invoiceLines = []
     for count,line in enumerate(lines):
          invoiceLines.append(
               {
                    "LineNumber": count+1,
                    "LineAmount": line['amount'],  
                    "Description":'SALARY TAX',
                    "invoiceDistributions": [{
                         "DistributionLineNumber": 1,
                         "DistributionLineType": "Item",
                         "DistributionAmount": line['amount'],
                         # "DistributionCombination": distribution_combination(request.user.company.company_segment,line['cost_center'],'EMPLOYEE INSURANCE',request.user.company.company_segment)
                         "DistributionCombination": "01.00.00000.00.41632.0000.00.00.00"
               }] })     
     
     invoice_data = {
          "InvoiceNumber": invoice_number_compaination(supplier,month,year),
          # "InvoiceCurrency": "EG" for shoura,
          "InvoiceCurrency": "SAR",
          "InvoiceAmount": InvoiceAmount,
          "InvoiceDate": get_string_date(),
          # "BusinessUnit":  "Shoura",
          "BusinessUnit":  "Future Networks Telecom Company BU",
          # "Supplier" : 'EMPLOYEE INSURANCE',
          "Supplier" : "Petty cash atheer practise",
          "PaymentMethodCode": "CHECK",
          "PaymentMethod": "Check",
          "PaymentTerms": "Immediate",
          # "SupplierSite": "EGYPT",
          "SupplierSite": "Riyadh",
          "InvoiceSource": "Manual invoice entry",
          "InvoiceType": "Standard",
          "Description": invoice_number_compaination(supplier,month,year),
           "attachments": [],
          "invoiceInstallments":[],
          "invoiceLines": invoiceLines,
     }
     url = 'https://fa-euuk-test-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/invoices'
     response = requests.post(url, auth=HTTPBasicAuth(user_name, password),
                              headers={'Content-Type': 'application/json'},
                              json=invoice_data)
     print("****************************************")
     print(response) 
     print("****************************************")
     print("****************************************")  
     json_response =  json.loads(response.text)
     print("json_response:",response.content,"createddddd")
     if response == '201 Created':
          json_response =  json.loads(response.text)
          print("json_response:",json_response,"createddddd")
     else:
          print("json_response:","erooooooooooor")     
     
  






def send_salaries_invoice(request,month,year):
     supplier = 'Accrued salaries'
     lines = get_invoice_date_as_excel(month,year,supplier,request.user)
     InvoiceAmount = lines.pop()
     invoiceLines = []
     for count,line in enumerate(lines):
          invoiceLines.append(
               {
                    "LineNumber": count+1,
                    "LineAmount": line['amount'],  
                    "Description":'Accrued salaries',
                    "invoiceDistributions": [{
                         "DistributionLineNumber": 1,
                         "DistributionLineType": "Item",
                         "DistributionAmount": line['amount'],
                         # "DistributionCombination": distribution_combination(request.user.company.company_segment,line['cost_center'],'EMPLOYEE INSURANCE',request.user.company.company_segment)
                         "DistributionCombination": "01.00.00000.00.41632.0000.00.00.00"
               }] })     
     
     invoice_data = {
          "InvoiceNumber": invoice_number_compaination(supplier,month,year),
          # "InvoiceCurrency": "EG" for shoura,
          "InvoiceCurrency": "SAR",
          "InvoiceAmount": InvoiceAmount,
          "InvoiceDate": get_string_date(),
          # "BusinessUnit":  "Shoura",
          "BusinessUnit":  "Future Networks Telecom Company BU",
          # "Supplier" : 'EMPLOYEE INSURANCE',
          "Supplier" : "Petty cash atheer practise",
          "PaymentMethodCode": "CHECK",
          "PaymentMethod": "Check",
          "PaymentTerms": "Immediate",
          # "SupplierSite": "EGYPT",
          "SupplierSite": "Riyadh",
          "InvoiceSource": "Manual invoice entry",
          "InvoiceType": "Standard",
          "Description": invoice_number_compaination(supplier,month,year),
           "attachments": [],
          "invoiceInstallments":[],
          "invoiceLines": invoiceLines,
     }
     print(invoice_data)
     url = 'https://fa-euuk-test-saasfaprod1.fa.ocs.oraclecloud.com/fscmRestApi/resources/11.13.18.05/invoices'
     response = requests.post(url, auth=HTTPBasicAuth(user_name, password),
                              headers={'Content-Type': 'application/json'},
                            json=invoice_data)
     # print(response) 
     # print("content:", response.content)                         
     # json_response =  json.loads(response.text)
     # if response == 201:
     #      print("json_response:",json_response)
     # else:
     #      print("json_response:",json_response,"erooooooooooor")     
     
