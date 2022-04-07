from element_definition.models import Element
from .models import *
from django.core.exceptions import ValidationError
from django.core.exceptions import ObjectDoesNotExist
import re


class FastFormula:

    def __init__(self, emp_id, element, class_name):
        self.emp_id = emp_id
        self.class_name = class_name
        self.element = element

    def _convert_formula(self, formula_string):
        output = ''
        for letter in formula_string:
            if letter == "+" or letter == "-" or letter == "*" or letter == "/":
                letter = " {} ".format(letter)
            if letter == "%":
                letter = "/" + " " + "100" 
            output += letter
        return output

    def get_emp_elements(self):
        # get all elements for one employee and put them in a dic
        emp_elements = self.class_name.objects.filter(emp_id=self.emp_id)
        return emp_elements



    def get_fast_formula(self):
        # return a dic contains all the formula elements from the master element table.
        formula_elements = self.class_name.objects.filter(emp_id=self.emp_id, element_id=self.element)
        formulas = {}
        for x in formula_elements:
            formulas.update({self._convert_formula(
                x.element_id.element_formula): x.element_id.id})
        return formulas

    def get_formula_amount(self):
        # will check first if the employee have the formula element,
        # then we do calculations based on his elements.
        amount = 0
        custom_rule = "amount = "
        for key in self.get_fast_formula():  # looping in fast formula dic to check if the user have this FF
                custom_rule += key
        for e_element in self.get_emp_elements():
            ldict = {}
            for element_code in custom_rule.split():
                signs = ['-','+','*','/','=', ')' , '(']
                if element_code != 'amount' and element_code not in  signs:
                    try:
                        float(element_code)
                        is_int = True
                    except:
                        is_int = False
                    if is_int is False :    
                        try:
                            element = Element.objects.get(code=element_code)
                        except ObjectDoesNotExist:
                            return False    
                        try:
                            employee_element = self.class_name.objects.get(element_id__code = element_code, emp_id=self.emp_id)
                            if element_code == e_element.element_id.code :
                                element_value = employee_element.element_value
                                custom_rule = re.sub(r"\b{}\b".format(element_code),str(element_value),custom_rule)


                        except ObjectDoesNotExist:
                            # return False
                            custom_rule = custom_rule.replace(element_code, str(0))
        ldict = locals()
        try:
            exec(custom_rule, globals(), ldict)
            amount = ldict['amount']
            round_amout = (round(amount, 2))
            return round_amout
        except :
            return -1
