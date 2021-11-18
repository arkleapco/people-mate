import calendar
from datetime import date
from django.db.models import Count, Q
from company.models import Working_Days_Policy, YearlyHoliday
from leave.models import Leave
from payroll_run.social_insurance_calc import SocialInsurance
from service.models import Bussiness_Travel
from employee.models import Employee, Employee_Element
from manage_payroll.models import Assignment_Batch, Payroll_Master
from payroll_run.new_tax_rules import Tax_Deduction_Amount
from django.utils.translation import ugettext_lazy as _
from .models import Taxes
from .payslip_functions import PayslipFunction
from django.shortcuts import render, get_object_or_404, get_list_or_404, redirect





class Salary_Calculator:

    def __init__(self, company, employee,elements):
        self.company = company
        self.employee = employee
        self.elements = elements

    def workdays_weekends_number(self, month, year):
        output = dict()
        workdays = 0
        weekends = 0
        holidays = 0
        holidays_list = []
        cal = calendar.Calendar()
        company_weekends = self.company_weekends()
        for week in cal.monthdayscalendar(year, month):
            for i, day in enumerate(week):
                # Check if is a weekday and the day is from this month
                if calendar.day_name[i] not in company_weekends and day != 0:
                    workdays += 1

                if calendar.day_name[i] in company_weekends and day != 0:
                    weekends += 1
        yearly_holidays = YearlyHoliday.objects.filter(
            enterprise=self.company, year__year=year).filter(Q(start_date__month=month) | Q(end_date__month=month))
        for x in yearly_holidays:
            if x.start_date.month != month or x.end_date.month != month:
                holidays += x.end_date.day
            else:
                holidays += x.number_of_days_off
            # holidays_list.append(x.start_date)
        output['workdays'] = workdays
        output['weekends'] = weekends
        output['holidays'] = holidays
        return output

    def company_weekends(self):
        company_policy = Working_Days_Policy.objects.get(
            enterprise=self.company)
        company_weekends = company_policy.week_end_days
        weekend_days = []
        for x in company_weekends:
            weekend_days.append(calendar.day_name[int(x)])
        return weekend_days

    def is_day_a_weekend(self, day):
        day_name = calendar.day_name[day.weekday()]
        if day_name in self.company_weekends():
            return True
        else:
            return False

    def holidays_of_the_month(self, year, month):
        holidays_list = []
        holidays = YearlyHoliday.objects.filter(
            enterprise=self.company, year__year=month).filter(Q(start_date__month=month) |
                                                              Q(end_date__month=month))
        for x in holidays:
            holidays_list.append(x.start_date)
        return holidays_list

    def is_day_a_holiday(self, year, month, day):
        if day in self.holidays_of_the_month(year, month):
            return True
        else:
            return False

    def is_day_a_leave(self, year, month, day):
        leave_list = Leave.objects.filter(
            Q(user__id=self.employee.user) & ((Q(startdate__month=month) & Q(startdate__year=month)) | (
                Q(enddate__month=month) & Q(enddate__year=month))))
        for leave in leave_list:
            if (leave.startdate <= date_v <= leave.enddate) and leave.is_approved:
                return True
        return False

    def is_day_a_service(self, year, month, day):
        services_list = Bussiness_Travel.objects.filter(
            Q(emp=self.employee) & (
                (Q(estimated_date_of_travel_from__month=month) & Q(estimated_date_of_travel_from__year=month)) | (
                    Q(estimated_date_of_travel_to__month=month) & Q(estimated_date_of_travel_from__year=month))))
        for service in services_list:
            if (
                    service.estimated_date_of_travel_from <= day <= service.estimated_date_of_travel_to__month) and service.is_approved:
                return True
        return False

    def calc_emp_income(self):
        #TODO filter employee element with start date
        emp_allowance = Employee_Element.objects.filter(element_id__in=self.elements,element_id__classification__code='earn',
                                                        emp_id=self.employee).filter(
            (Q(end_date__gt=date.today()) | Q(end_date__isnull=True)))
        total_earnnings = 0.0
        #earning | type_amount | mounthly
        for x in emp_allowance:
            payslip_func = PayslipFunction()
            if payslip_func.get_element_classification(x.element_id.id) == 'earn' or \
                    payslip_func.get_element_amount_type(x.element_id.id) == 'fixed amount' and \
                    payslip_func.get_element_scheduled_pay(x.element_id.id) == 'monthly':
                if x.element_value:
                    total_earnnings += x.element_value
                else:
                    total_earnnings += 0.0
        return round(total_earnnings, 3)

    # حساب اجر اليوم و سعر الساعة
    def calc_daily_rate(self):
        company_policy = Working_Days_Policy.objects.get(
            enterprise=self.company)
        # عدد ساعات العمل للشركة
        company_working_hrs = company_policy.number_of_daily_working_hrs
        emp_allowance = Employee_Element.objects.filter(element_id__in=self.elements,element_id__classification__code='earn',
                                                        emp_id=self.employee).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True))).get(element_id__basic_flag=True)
        emp_basic = emp_allowance.element_value  # المرتب الاساسي للعامل
        hour_rate = (emp_basic / 30) / company_working_hrs
        return hour_rate

    # calculate employee deductions without social insurance
    #3 + deduction
    def calc_emp_deductions_amount(self):
        # TODO : Need to filter with start date
        emp_deductions = Employee_Element.objects.filter(element_id__in=self.elements,
            element_id__classification__code='deduct', emp_id=self.employee).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        total_deductions = 0
        # payslip_func = PayslipFunction()
        for x in emp_deductions:
            if x.element_value:
                total_deductions += x.element_value
            else:
                total_deductions += 0.0
        return round(total_deductions, 3)

    def calc_emp_tax_deductions_amount(self):
        # TODO : Need to filter with start date
        emp_deductions = Employee_Element.objects.filter(element_id__in=self.elements,
            element_id__classification__code='deduct',element_id__tax_flag= True, emp_id=self.employee).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        total_deductions = 0
        # payslip_func = PayslipFunction()
        for x in emp_deductions:
            if x.element_value:
                total_deductions += x.element_value
            else:
                total_deductions += 0.0
        return round(total_deductions, 3)   


    def calc_emp_tax_deductions_amount(self):
        # TODO : Need to filter with start date
        emp_deductions = Employee_Element.objects.filter(element_id__in=self.elements,
            element_id__classification__code='deduct',element_id__tax_flag = True, emp_id=self.employee).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))
        total_deductions = 0
        # payslip_func = PayslipFunction()
        for x in emp_deductions:
            if x.element_value:
                total_deductions += x.element_value
            else:
                total_deductions += 0.0
        return round(total_deductions, 3)


    # calculate gross salary
    def calc_gross_salary(self):
        gross_salary = self.calc_emp_income()
        return round(gross_salary, 3)

    def chack_employee_has_allowences(self):
        emp_allowance = Employee_Element.objects.filter(element_id__in=self.elements,element_id__classification__code='earn',
                                                        emp_id=self.employee).filter(
            (Q(end_date__gt=date.today()) | Q(end_date__isnull=True))).exclude(element_id__is_basic = True)
        
        if  len(emp_allowance)<3:
            return False
        else:
            return True

    # calculate social insurance
    def calc_employee_insurance(self):
        if self.employee.insured:
            required_employee = Employee.objects.get(id=self.employee.id)
            insurance_deduction = 0


            if required_employee.insurance_salary and  required_employee.insurance_salary > 0.0:

                if required_employee.insurance_salary > 8100:
                    insurance_salary = 8100
                elif required_employee.insurance_salary < 1200:
                    insurance_salary = 1200
                else:
                    insurance_salary = required_employee.insurance_salary

                social_class = SocialInsurance(insurance_salary)
                insurance_deduction = social_class.calc_employee_insurance_amount()
            # elif required_employee.retirement_insurance_salary and  required_employee.retirement_insurance_salary > 0.0:
            #     # social_class = SocialInsurance(required_employee.retirement_insurance_salary)
            #     insurance_deduction = 0.0
            elif required_employee.retirement_insurance_salary and  required_employee.retirement_insurance_salary > 0.0:
                insurance_deduction = 0.0
            
            else:
                gross = self.calc_gross_salary()
                
                chack_employee_has_allowences = self.chack_employee_has_allowences()
                if chack_employee_has_allowences:
                    gross_to_be_insured = gross * 0.7692 #### exclude 30 % of gross
                else:
                    gross_to_be_insured = gross
                
                if gross_to_be_insured > 8100:
                    gross_salary = 8100
                elif gross_to_be_insured < 1200:
                    gross_salary = 1200
                else:
                    gross_salary = gross

                social_class = SocialInsurance(gross_salary)
                insurance_deduction=  social_class.calc_employee_insurance_amount()
        else:
            insurance_deduction =  0.000
        return  round(insurance_deduction, 3)

    # calculate social insurance
    def calc_company_insurance(self):
        if self.employee.insured:
            required_employee = Employee.objects.get(id=self.employee.id)
            insurance_deduction = 0
            if required_employee.insurance_salary and  required_employee.insurance_salary > 0.0:
                social_class = SocialInsurance(required_employee.insurance_salary)
                insurance_deduction = social_class.calc_company_insurance_amount()
            elif required_employee.retirement_insurance_salary and  required_employee.retirement_insurance_salary > 0.0:
                print("inside retirement >>>>")
                social_class = SocialInsurance(required_employee.retirement_insurance_salary)
                insurance_deduction = social_class.calc_retirement_insurance_amount()
            else:
                gross = self.calc_gross_salary()
                social_class = SocialInsurance(gross)
                insurance_deduction=  social_class.calc_company_insurance_amount()
        else:
            insurance_deduction =  0.000
        return  round(insurance_deduction, 3)
    

    def calc_retirement_insurance(self):
        if self.employee.insured:
            required_employee = Employee.objects.get(id=self.employee.id)
            insurance_deduction = 0
            if required_employee.retirement_insurance_salary > 0.0:
                print("inside retirement 2222 >>>>")
                social_class = SocialInsurance(required_employee.retirement_insurance_salary)
                insurance_deduction = social_class.calc_retirement_insurance_amount()
        else:
            insurance_deduction =  0.000
        return  round(insurance_deduction, 3)



    # calculate tax amount
    #
    def calc_taxes_deduction(self):
        required_employee = Employee.objects.get(id=self.employee.id)
        tax_rule_master = Payroll_Master.objects.get(enterprise=required_employee.enterprise , end_date__isnull = True)
        
        personal_exemption = tax_rule_master.tax_rule.personal_exemption
        round_to_10 = tax_rule_master.tax_rule.round_down_to_nearest_10
        # initiat the tax class here 
        tax_deduction_obj = Tax_Deduction_Amount(personal_exemption, round_to_10)
        taxable_salary = self.calc_gross_salary() - self.calc_emp_tax_deductions_amount()
        taxes = tax_deduction_obj.run_tax_calc(taxable_salary, self.calc_employee_insurance())
        self.tax_amount = taxes
        return round(taxes, 2)

    # calculate net salary
    def calc_net_salary(self):
        # taxes_and_insurance=  self.calc_taxes_deduction() + (self.calc_emp_deductions_amount() + self.calc_employee_insurance())
        # net_salary = self.calc_gross_salary() - taxes_and_insurance
        net_salary = self.calc_gross_salary() - ( self.calc_taxes_deduction() +  self.calc_employee_insurance() + self.calc_emp_deductions_amount())
        if net_salary < 0.0:
            return 0.0
        else:
            return net_salary

    def calc_attribute1(self):
        net_salary = self.calc_net_salary()
        attribute1 = net_salary * 0.01 ### net salary * 1%
        return attribute1

    def calc_final_net_salary(self):
        attribute1 = self.calc_attribute1()
        net_salary = self.calc_net_salary()
        final_net_salary = net_salary - attribute1
        return final_net_salary

#########################################################################

    def calc_basic_net(self):
        basic_net =Employee_Element.objects.filter(element_id__is_basic=True, emp_id=self.employee).filter(
            (Q(end_date__gte=date.today()) | Q(end_date__isnull=True)))[0].element_value
        basic_net = basic_net if basic_net is not None else 0
        allowence = self.calc_emp_income() - basic_net
        deductions = self.calc_emp_deductions_amount()
        insurence = self.calc_employee_insurance()
        final_net = (basic_net+ allowence - (deductions + insurence) )
        return final_net

    # @Edited by Faten:2021-06-04
    def net_to_tax(self):
        taxes=0
        percent=0
        diffrence=0
        final_net = self.calc_basic_net()
        year_net = (final_net * 12) - 9000
        tax_sections = Taxes.objects.all()

        # Loop over tax_sections table that maps each gross start, end range to it's corresponding start, end net
        # If the year_net exceeds the current section range add the full maximum tax amount to taxes
        # When reaching the section which year_net is located get the section tax percent
        for section in tax_sections:
            if float(year_net)>section.start_range and float(year_net)<=section.end_range:
                percent = section.percent / 100
                break
            else:
                taxes+=section.tax
                diffrence+=section.diffrence

        # This indecates the gross for the net salary without the part in the last tax section
        full_sections_gross = float(year_net)+taxes
        # Last tax section net salary can be calculated by full_sections_gross (doesn't include last tax) - diffrence (represnt the boundary gross for the previous section)
        last_section_net = full_sections_gross - diffrence

        # To convert net amount to tax amount as (net / (1-percent)) = gross, gross * percent = tax
        last_section_tax_value = last_section_net / (1-percent) * percent
        taxes += last_section_tax_value
        return taxes / 12

    def net_to_gross(self):
        final_net = self.calc_basic_net()
        tax = self.net_to_tax()
        gross_salary = round(tax +float(final_net),3)
        return gross_salary
