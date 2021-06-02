from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.db import models
from django.db.models import Q
from django.db.models.signals import pre_save, post_save, post_init
from django.dispatch import receiver
from notifications.signals import notify
from .models import LeaveMaster, Leave, Employee_Leave_balance, EmployeeAbsence
from employee.models import Employee, JobRoll, Employee_Element, Employee_Element_History
from django.utils.translation import ugettext_lazy as _
from .manager import LeaveManager
from company.models import Enterprise
from datetime import date, datetime
from custom_user.models import User
import calendar

"""
Ziad
11/3/2021
Class to check employee balance and do all leaves calculations
"""


class CheckBalance:

    def __init__(self):
        pass

    # ___________ validate leave request __________________

    def eligible_user_leave(self, user):
        """
        check employee is already in vacation
        :return:
        """
        now_date = datetime.date(datetime.now())
        leaves = Leave.objects.filter(user=user, status='Approved')
        for leave in leaves:
            if leave.enddate >= now_date >= leave.startdate:
                return False
            else:
                continue
        return True

    def valid_leave(self, user, req_startdate, req_enddate):
        """
        check a vacation intersects with another
        :param req_startdate:
        :param req_enddate:
        :return:
        """
        leaves = Leave.objects.filter(user=user, status='Approved').order_by('-id')
        for leave in leaves[0:3]:
            if leave.enddate >= req_startdate >= leave.startdate or \
                    req_enddate >= leave.startdate >= req_startdate:
                return False
        return True

    # __________ end validate leave ______________________

    # def update_leave_balance(self, employee_balance, casual=None, usual=None, carried_forward=None):
    #     """
    #     update Employee balance
    #     :param employee_balance:
    #     :param casual:
    #     :param usual:
    #     :param carried_forward:
    #     :return:
    #     """

    def have_balance(self, employee_leave_balance, balance_deductions, employee_balance):
        """
        employee has balance to deduce from
        :param employee_leave_balance:
        :param balance_deductions:
        :param employee_balance:
        :return:
        by: amira
        date: 6/5/2021
        """
        if employee_leave_balance.casual > 0:

            # casual covers the needed leave
            if employee_leave_balance.casual > balance_deductions:

                new_balance = employee_leave_balance.casual - balance_deductions
                employee_balance.update(casual=new_balance)

                print("casual", employee_leave_balance.casual,
                      "usual", employee_leave_balance.usual)

            # casual doesn't cover needed leave deduce from casual and usual
            else:
                new_balance = 0
                # calcuate the new balance
                new_balance += balance_deductions - employee_leave_balance.casual
                # set cascual=0
                employee_balance.update(casual=0)
                # calcuate the usual balance
                new_usual_balance = employee_leave_balance.usual - new_balance
                # update
                employee_balance.update(usual=new_usual_balance)
                print("casual", employee_leave_balance.casual,
                      "usual", employee_leave_balance.usual)

        elif employee_leave_balance.usual > 0:

            # usual covers the needed leave
            if employee_leave_balance.usual > balance_deductions:

                new_balance = employee_leave_balance.usual - balance_deductions
                employee_balance.update(usual=new_balance)
                print("casual", employee_leave_balance.casual,
                      "usual", employee_leave_balance.usual)

            # usual doesn't cover needed leave deduce from usual and carried forward
            else:
                new_balance = 0
                # calcuate the new balance
                new_balance += balance_deductions - employee_leave_balance.usual

                # set cascual=0
                employee_balance.update(usual=0)
                # calcuate the usual balance
                new_forward_balance = employee_leave_balance.carried_forward - new_balance
                # update
                employee_balance.update(carried_forward=new_forward_balance)

        # employee doesnt have casual or usual but carried_forward covers his/her leaves
        else:
            new_balance = employee_leave_balance.carried_forward - balance_deductions
            employee_balance.update(carried_forward=new_balance)

    def create_employee_absence(self, data_obj_1, data_obj_2=None):
        """
        create new record in absent employee table
        :param data_obj_1: will be provided in all cases to be created
        :param data_obj_2: will only be provided in case the leave starts in a month and ends in another month
        :return:
        by: amira
        date: 6/5/2021
        """
        created_obj = EmployeeAbsence(
            **data_obj_1
        )
        created_obj.save()

        if data_obj_2 is not None:
            created_obj = EmployeeAbsence(
                **data_obj_2
            )
            created_obj.save()

    def update_employee_balance_to_zeros(self, employee_balance):
        """
        update usual, casual, carried_forward to zeros
        :param employee_balance:
        :return:
        by: amira
        date: 6/5/2021
        """
        employee_balance.update(usual=0)
        employee_balance.update(casual=0)
        employee_balance.update(carried_forward=0)

    def update_absence(self, employee_balance, total_absence_obj):
        """
        update absence value
        :param employee_balance:
        :param total_absence_obj:
        :return:
        """
        total_absence = 0
        for i in total_absence_obj:
            total_absence += i.num_of_days
        employee_balance.update(absence=total_absence)

    def have_no_balance(self, emp_id, employee_balance, end_date, start_date, employee, balance_deductions,
                        total_balance, leave_valuee):
        """
        employee doesnt have balance and absence will be added
        :param emp_id:
        :param employee_balance:
        :param end_date:
        :param start_date:
        :param employee:
        :param balance_deductions:
        :param total_balance:
        :param leave_valuee:
        :return:
        by: amira
        date: 6/5/2021
        """
        # emp_allowance = Employee_Element.objects.filter(element_id__classification__code='earn',
        #                                             emp_id=emp_id).filter(
        # (Q(end_date__gte=date.today()) | Q(end_date__isnull=True))).get(element_id__is_basic=True)
        # emp_basic = emp_allowance.element_value
        day_rate = 1  # todo to be calculated later # emp_basic / 30
        self.update_employee_balance_to_zeros(employee_balance=employee_balance)

        last_day = calendar.monthrange(end_date.year, end_date.month)[1]
        end_date_range_str = end_date.replace(day=last_day)

        print(end_date_range_str)

        current_year = date.today().year

        if end_date.month == start_date.month:
            print("yes  #")
            absence = balance_deductions - total_balance
            total_absence_value = absence * day_rate

            absence_dict = {
                'employee': employee,
                'start_date': start_date,
                'end_date': end_date,
                'num_of_days': absence,
                'value': total_absence_value,
            }
            self.create_employee_absence(data_obj_1=absence_dict)
            total_absence_obj = EmployeeAbsence.objects.filter(employee=employee, start_date__year=current_year)

        elif end_date.month > start_date.month:
            print("no")
            last_day = calendar.monthrange(start_date.year, start_date.month)[1]
            first_record_start = start_date
            first_record_end = start_date.replace(day=last_day)
            first_record_absence_days = int((first_record_end.day - first_record_start.day)) + 1
            balance_deductions1 = first_record_absence_days * leave_valuee
            first_record_absence = balance_deductions1 - total_balance
            first_record_value = first_record_absence * day_rate
            second_record_start = end_date.replace(day=1)
            second_record_end = end_date
            second_record_absence_days = int((second_record_end.day - second_record_start.day)) + 1
            balance_deductions2 = first_record_absence_days * leave_valuee
            second_record_absence = second_record_absence_days - total_balance
            second_record_value = second_record_absence * day_rate

            absence_dict_month_1 = {
                'employee': employee,
                'start_date': first_record_start,
                'end_date': first_record_end,
                'num_of_days': first_record_absence,
                'value': first_record_value,
            }

            absence_dict_month_2 = {
                'employee': employee,
                'start_date': second_record_start,
                'end_date': second_record_end,
                'num_of_days': second_record_absence,
                'value': second_record_value,
            }
            self.create_employee_absence(data_obj_1=absence_dict_month_1, data_obj_2=absence_dict_month_2)
            total_absence_obj = EmployeeAbsence.objects.filter(employee=employee, start_date__year=current_year)

        self.update_absence(employee_balance=employee_balance, total_absence_obj=total_absence_obj)

    # _____________________________________________________________________
    def check_balance(self, emp_id, start_date, end_date, leave):
        month_absence = 0
        leave_type_id = Leave.objects.filter(id=leave).values()[0].get("leavetype_id")

        leave_valuee = LeaveMaster.objects.get(id=leave_type_id).leave_value

        employee_leave_balance = Employee_Leave_balance.objects.get(employee=emp_id)

        total_balance = employee_leave_balance.total_balance

        employee = Employee.objects.get(id=emp_id.id, emp_end_date__isnull=True)

        needed_days = abs((end_date - start_date).days) + 1

        balance_deductions = needed_days * leave_valuee

        employee_balance = Employee_Leave_balance.objects.filter(employee=emp_id)

        print("casual", employee_leave_balance.casual,
              "usual", employee_leave_balance.usual, "total", total_balance, "needed", needed_days)

        # 1) have balance
        if total_balance >= balance_deductions:
            self.have_balance(employee_leave_balance=employee_leave_balance,
                              balance_deductions=balance_deductions,
                              employee_balance=employee_balance)

        # 2) doesnt have balance
        else:

            self.have_no_balance(emp_id=emp_id,
                                 employee_balance=employee_balance,
                                 end_date=end_date,
                                 start_date=start_date,
                                 employee=employee,
                                 balance_deductions=balance_deductions,
                                 total_balance=total_balance,
                                 leave_valuee=leave_valuee)
