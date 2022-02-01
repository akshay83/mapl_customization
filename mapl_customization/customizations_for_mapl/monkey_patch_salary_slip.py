from __future__ import unicode_literals
import frappe
import erpnext
import math

from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words
from frappe import _

#Apply Custom Rounding
#As if 1st Feb 2022 this Method is Same in both Version-13 Branches and Develop Branch
def get_amount_based_on_payment_days(self, row, joining_date, relieving_date):
	amount, additional_amount = row.amount, row.additional_amount
	if (self.salary_structure and
		cint(row.depends_on_payment_days) and cint(self.total_working_days) and
		(not self.salary_slip_based_on_timesheet or
			getdate(self.start_date) < joining_date or
			(relieving_date and getdate(self.end_date) > relieving_date)
		)):
		additional_amount = flt((flt(row.additional_amount) * flt(self.payment_days)
			/ cint(self.total_working_days)), row.precision("additional_amount"))
		amount = flt((flt(row.default_amount) * flt(self.payment_days)
			/ cint(self.total_working_days)), row.precision("amount")) + additional_amount

	elif not self.payment_days and not self.salary_slip_based_on_timesheet and cint(row.depends_on_payment_days):
		amount, additional_amount = 0, 0
	elif not row.amount:
		amount = flt(row.default_amount) + flt(row.additional_amount)

	# apply rounding
	if frappe.get_cached_value("Salary Component", row.salary_component, "round_to_the_nearest_integer"):
		#Monkey Here
		rounding_type = frappe.get_cached_value("Salary Component", row.salary_component, "rounding")
		if not rounding_type or rounding_type == '':
			amount, additional_amount = rounded(amount), rounded(additional_amount)
		else:
			amount, additional_amount = custom_round(rounding_type, amount), custom_round(rounding_type, additional_amount)

	return amount, additional_amount

def custom_round(d, amt):
	if d and d != '':
		if d.lower() == 'downwards':
			return int(amt)
		elif d.lower() == 'upwards':
			return math.ceil(amt)
		else:
			return round(amt, 0)
	return amt

def monkey_patch_salary_slip_for_rounding():
	print ('Patching Salary Slip Monkey - MAPL')
	from erpnext.payroll.doctype.salary_slip.salary_slip import SalarySlip
	SalarySlip.get_amount_based_on_payment_days = get_amount_based_on_payment_days

def monkey_patch_for_salary_slip():
	monkey_patch_salary_slip_for_rounding()
