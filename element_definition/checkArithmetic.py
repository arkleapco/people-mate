from django.core.exceptions import ValidationError


class ArithmeticOperations:

    def __init__(self, arithc_sign, percent, arithc_sign_2):
        self.arithc_sign = arithc_sign
        self.percent = percent
        self.arithc_sign_2 = arithc_sign_2
    
    def check_arithc_if_empty(self, arithc_sign):
        if arithc_sign is None:
            return  -1
        else:
            return arithc_sign
    
    def check_arithc_if_empty(self, percent):
        if percent is None:
            return  -2
        else:
            return percent
    
    def check_arithc_if_empty(self, arithc_sign_2):
        if arithc_sign_2 is None:
            return  -3
        else:
            return arithc_sign_2