

from employee.models import Employee


class SocialInsurance:

    def __init__(self, gross_sal, has_allowences, employee, month, year):
        self.gross_sal = gross_sal
        self.has_allowences = has_allowences
        self.employee = employee
        self.month = month
        self.year = year


    
    def check_if_employee_new_hire(self):
        is_new_hire = 30 
        if self.employee.hiredate.month == self.month and self.employee.hiredate.year == self.year:
            working_days_newhire = self.employee.employee_working_days_from_hiredate(self.year, self.month)
            if working_days_newhire < 30:
                is_new_hire = working_days_newhire
            # if working_days_newhire :
            #     is_new_hire = working_days_newhire
            # else:
            #     is_new_hire = 30 
        return is_new_hire

    def insurance_salary_amount(self):
        amount_dic = {'employee':0, 'retirement':0}
        insurance_salary_amont = 0.0
        if self.employee.insurance_salary and  self.employee.insurance_salary > 0.0:
            if self.year < 2022:
                max_insurance_year =8100
                min_insurance_year = 1200
            else:
                max_insurance_year =9400
                min_insurance_year = 1400
            if self.employee.insurance_salary > max_insurance_year: ## max insurance_salary change every yer need to put in set up screen 
                insurance_salary_amont = max_insurance_year
                amount_dic['employee']=insurance_salary_amont
            elif self.employee.insurance_salary < min_insurance_year:
                insurance_salary_amont = min_insurance_year
                amount_dic['employee']=insurance_salary_amont
            else:
                insurance_salary_amont = self.employee.insurance_salary
                amount_dic['employee']=insurance_salary_amont
        elif self.employee.retirement_insurance_salary and self.employee.retirement_insurance_salary > 0:
            insurance_salary_amont = self.employee.retirement_insurance_salary
            amount_dic['retirement']=insurance_salary_amont
        return amount_dic

    def calc_insurance_from_gross_salary(self):
        insurance_from_gross= 0.0
        gross = self.gross_sal
        if self.has_allowences:
            gross_to_be_insured = gross * 0.7692 #### exclude 30 % of gross
        else:
            gross_to_be_insured = gross
        
        if gross_to_be_insured > 8100:
            insurance_from_gross = 8100
        elif gross_to_be_insured < 1200:
            insurance_from_gross = 1200
        else:
            insurance_from_gross = gross
        return insurance_from_gross

    def calc_employee_insurance_amount(self):
        employee_insurance_amount = 0.0
        if self.check_if_employee_new_hire() >=30 and self.insurance_salary_amount()['employee']: 
            if self.insurance_salary_amount()['employee'] > 0:
                employee_insurance_amount = self.insurance_salary_amount()['employee'] * (0.11)
            else:
                employee_insurance_amount = self.calc_insurance_from_gross_salary() * (0.11) 
        return employee_insurance_amount

    def calc_company_insurance_amount(self):
        company_insurance_amount = 0.0
        if self.check_if_employee_new_hire() >=30 :
            if self.insurance_salary_amount()['employee'] > 0:
                company_insurance_amount = self.insurance_salary_amount()['employee'] * (0.1875)
            elif self.insurance_salary_amount()['retirement'] > 0:
                company_insurance_amount = self.insurance_salary_amount()['retirement'] * (0.0475)
            else:
                company_insurance_amount = self.calc_insurance_from_gross_salary() * (0.1875)
        return company_insurance_amount
    
    def calc_retirement_insurance_amount(self):
        retirement_insurance_amount = 0.0
        if self.insurance_salary_amount()['retirement']:
            insurance_salary = self.insurance_salary_amount()['retirement']
            retirement_insurance_amount = insurance_salary * (0.0475)
        return retirement_insurance_amount
    