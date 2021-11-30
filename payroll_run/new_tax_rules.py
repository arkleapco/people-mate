from defenition.models import TaxRule, Tax_Sections


class Tax_Deduction_Amount:
    def __init__(self, exemption, round_down_to_nearest_10):
        self.exemption = exemption
        self.round_down_to_nearest_10 = round_down_to_nearest_10

    def _tax_calculation_under_600000(self, salary, section_seq_start):
        tax_sections = Tax_Sections.objects.filter(section_execution_sequence__gte=section_seq_start)
        employee_sections = {}
        tax_value = 0.0
        for section in tax_sections:
            if salary >= section.salary_from:
                if salary <= section.salary_to and section.section_execution_sequence !=7 :
                        employee_sections[section.tax_percentage] = salary - section.salary_from + 1
                elif salary <= section.salary_to and section.section_execution_sequence ==7:
                        employee_sections[section.tax_percentage] = salary - 400000
                else:   # salary grater than the نهاية الشريحة
                        employee_sections[section.tax_percentage] = section.tax_difference
        for key, value in employee_sections.items():
            tax_amount_for_section = value * (key / 100)
            tax_value += tax_amount_for_section
        
        return round(tax_value, 2)
    
    def _tax_calculation_above_600000(self, salary, section_seq_start):
        tax_sections = Tax_Sections.objects.filter(section_execution_sequence__gte=section_seq_start)
        employee_sections = {}
        tax_value = 0.0
        for section in tax_sections:
            if section.section_execution_sequence == section_seq_start:
                employee_sections[section.tax_percentage] = section.salary_to
            elif section.section_execution_sequence ==7:
                employee_sections[section.tax_percentage] = salary - 400000
            else:
                employee_sections[section.tax_percentage] = section.tax_difference
        for key, value in employee_sections.items():
            tax_amount_for_section = value * (key / 100)
            tax_value += tax_amount_for_section
        return round(tax_value, 2)
    
    def _tax_calaulation(self, annual_tax_salary):
        # هل المرتب اكثر من 600 الف ؟
        if annual_tax_salary < 600000:
            # return self._tax_special_sextion(annual_tax_salary, 0)
            return self._tax_calculation_under_600000(annual_tax_salary, 0)
        else:
            # salary from 600,000 to 700,000
            if annual_tax_salary >= 600000 and annual_tax_salary <= 700000:
                return self._tax_calculation_above_600000(annual_tax_salary, 2)
            # salary from 700,000 to 800,000
            elif annual_tax_salary >= 700000 and annual_tax_salary <= 800000:
                return self._tax_calculation_above_600000(annual_tax_salary, 3)
            # salary from 800,000 to 900,000
            elif annual_tax_salary >= 600000 and annual_tax_salary <= 900000:
                return self._tax_calculation_above_600000(annual_tax_salary, 4)
            # salary from 900,000 to 1,000,000
            elif annual_tax_salary >= 600000 and annual_tax_salary <= 1000000:
                return self._tax_calculation_above_600000(annual_tax_salary, 5)
            # salary from 1,000,000 and more
            else:
                return self._tax_calculation_above_600000(annual_tax_salary, 6)


    def _calc_annual_tax_salary(self, monthly_taxable_salary, monthly_insurance_salary):
        salary = monthly_taxable_salary * 12
        yearly_insurance = monthly_insurance_salary * 12
        tax_salary = salary - (self.exemption + yearly_insurance)
        return self._tax_calaulation(tax_salary)

    def _calculate_monthly_tax(self, yearly_tax_amount):
        if self.round_down_to_nearest_10:
            return round(yearly_tax_amount / 12, 2)
        else:
            return yearly_tax_amount / 12

    def run_tax_calc(self, monthly_taxable_salary, monthly_insurance_salary):
        return self._calculate_monthly_tax(self._calc_annual_tax_salary(monthly_taxable_salary, monthly_insurance_salary))