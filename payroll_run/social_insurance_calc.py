

class SocialInsurance:

    def __init__(self, insurance_salary):
        self.insurance_salary = insurance_salary
    

    def calc_employee_insurance_amount(self):
        insurance_salary = self.insurance_salary
        employee_insurance_amount = 0.0
        employee_insurance_amount = insurance_salary * (11/100)
        return employee_insurance_amount

    def calc_company_insurance_amount(self):
        insurance_salary = self.insurance_salary
        company_insurance_amount = 0.0
        company_insurance_amount = insurance_salary * (18.75/100)
        return company_insurance_amount
    
    def calc_retirement_insurance_amount(self):
        insurance_salary = self.insurance_salary
        retirement_insurance_amount = 0.0
        retirement_insurance_amount = insurance_salary * (4.75/100)
        return retirement_insurance_amount
    