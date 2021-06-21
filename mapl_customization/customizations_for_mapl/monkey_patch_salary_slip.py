from __future__ import unicode_literals
import frappe
import erpnext
import math

from frappe.utils import add_days, cint, cstr, flt, getdate, rounded, date_diff, money_in_words
from erpnext.loan_management.doctype.loan_repayment.loan_repayment import calculate_amounts
from frappe import _

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


#Applying this patch as Employee Loan when Deducted from Salary is FLAWED. The default ERPNext System Creates a Loan Accrual Entry
#through Process Loan Interest Accrual running daily as a background process. This Process .. creates loan accrual entries for all
#those entries whose payment date in Repayment Schedule = current date of Process.

#Also when creating a Salary Slip .. it fetches all the Loan Interest Accrual And/Or Repayment Schedule having payment date less
#then the posting date of current Salary Slip irrespective of for which period the salary slip is being made.

#This patch fetches entries from repayment schedule where the loan is given as Repay From Salary and ignores the Loan Interest Accrual

def set_loan_repayment(self):
	self.total_loan_repayment = 0
	self.total_interest_amount = 0
	self.total_principal_amount = 0

	#monkey-here
	from mapl_customization.customizations_for_mapl.salary_slip_utils import get_repayment_schedule
	schedule = get_repayment_schedule(self)

	if schedule and len(schedule)>0:
		for l in schedule:
			self.total_interest_amount += l.interest_amount
			self.total_principal_amount += l.principal_amount
			self.total_loan_repayment += l.total_payment

		return
	#monkey-ends

	if not self.get('loans'):
		for loan in self.get_loan_details():

			amounts = calculate_amounts(loan.name, self.posting_date, "Regular Payment")

			if amounts['interest_amount'] or amounts['payable_principal_amount']:
				self.append('loans', {
					'loan': loan.name,
					'total_payment': amounts['interest_amount'] + amounts['payable_principal_amount'],
					'interest_amount': amounts['interest_amount'],
					'principal_amount': amounts['payable_principal_amount'],
					'loan_account': loan.loan_account,
					'interest_income_account': loan.interest_income_account
				})

	for payment in self.get('loans'):
		amounts = calculate_amounts(payment.loan, self.posting_date, "Regular Payment")
		total_amount = amounts['interest_amount'] + amounts['payable_principal_amount']
		if payment.total_payment > total_amount:
			frappe.throw(_("""Row {0}: Paid amount {1} is greater than pending accrued amount {2} against loan {3}""")
				.format(payment.idx, frappe.bold(payment.total_payment),
					frappe.bold(total_amount), frappe.bold(payment.loan)))

		self.total_interest_amount += payment.interest_amount
		self.total_principal_amount += payment.principal_amount

		self.total_loan_repayment += payment.total_payment

def term_loan_accrual_pending(date):
	repayment_list = frappe.db.sql("""select repay.name from `tabRepayment Schedule` repay,`tabLoan` loan where repay.payment_date <= %s
			and repay.is_accrued = 0 and loan.name = repay.parent and loan.repay_from_salary = 0""".format(date),as_dict=1)

	if (not repayment_list or len(repayment_list) <= 0):
		return None

	return repayment_list

def monkey_patch_salary_slip_for_rounding():
	from erpnext.payroll.doctype.salary_slip.salary_slip import SalarySlip
	SalarySlip.get_amount_based_on_payment_days = get_amount_based_on_payment_days
	SalarySlip.set_loan_repayment = set_loan_repayment

def monkey_patch_term_loan_processing():
	from erpnext.loan_management.doctype.process_loan_interest_accrual import process_loan_interest_accrual
	process_loan_interest_accrual.term_loan_accrual_pending = term_loan_accrual_pending

def monkey_patch_for_salary_slip():
	monkey_patch_salary_slip_for_rounding()
	monkey_patch_term_loan_processing()
