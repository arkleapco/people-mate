from element_definition.models import Element_Master , Element
from .models import *


class FastFormula:

    def __init__(self, emp_id, element, class_name):
        self.emp_id = emp_id
        self.class_name = class_name
        self.element = element

    def _convert_formula(self, str):
        output = ''
        for x in str:
            if x == "+" or x == "-" or x == "*" or x == "/":
                x = " {} ".format(x)
            if x == "%":
                x = "/100 *"
            output += x
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
        for x in self.get_emp_elements():
            ldict = {}
            for i in custom_rule.split():
                try:
                    element = Element.objects.get(code=i)
                    try:
                        employee_element = self.class_name.objects.get(element_id__code = i, emp_id=self.emp_id)
                        if i == x.element_id.code and x.element_id.is_basic == False:
                            element_value = x.element_value
                            custom_rule = custom_rule.replace(i, str(element_value))
                    except:
                        print("this employee not have this element to make the formula")
                except:
                    print("There no element in element master table")

        ldict = locals()
        exec(custom_rule, globals(), ldict)
        amount = ldict['amount']
        round_amout = (round(amount, 2))
        return round_amout
