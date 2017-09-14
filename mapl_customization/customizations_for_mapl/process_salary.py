import frappe
import erpnext
import json
from frappe.utils import cint
from mapl_customization.customizations_for_mapl.report.custom_salary_register.custom_salary_register import get_employee_details

@frappe.whitelist()
def process_staff_salaries_jv(payable_account, date, filters, director):

	if isinstance(filters, basestring):
		filters = json.loads(filters)

	if filters.get("date_range"):
		filters.update({"from_date": filters.get("date_range")[0], "to_date":filters.get("date_range")[1]})
	else:
		return

	details = get_employee_details(filters)

	jv = frappe.new_doc("Journal Entry")
	jv.posting_date = date
	jv.accounts = []

	earnings_deductions = {}
	for d in details:
		if not d["designation"] or (d["designation"] and d["designation"].lower() != 'director'):
			process_staff_jv(jv, d, payable_account, earnings_deductions)

	for comp, amount in earnings_deductions.iteritems():
		account = frappe.get_doc("Salary Component", comp).accounts

		account = account[0].default_account
		ac1 = jv.append("accounts")
		ac1.account = account
		if amount > 0:
			ac1.debit_in_account_currency = amount
		elif amount < 0:
			ac1.credit_in_account_currency = abs(amount)
		ac1.cost_center = 'Main - MAPL' #erpnext.get_default_cost_center(account[0].company)

	jv.save()

def process_staff_jv(jv, record, account, ed):
	ac1 = jv.append("accounts")
	ac1.party_type = 'Employee'
	ac1.party = record["employee_id"]
	ac1.party_name = record["employee_name"]
	ac1.account = account
	ac1.credit_in_account_currency = record["net_pay"]

	process_earnings_deductions(jv, record, account, ed)

def process_earnings_deductions(jv, record, account, ed):
	sal_slip = frappe.get_doc("Salary Slip", record["salary_slip_id"])
	for adv in sal_slip.loan_deduction_detail:
		loan_account = frappe.db.get_value("Employee Loan", adv.loan_reference , "employee_loan_account")
		ac1 = jv.append("accounts")
		ac1.party_type = 'Employee'
		ac1.party_name = record["employee_name"]
		ac1.party = record["employee_id"]
		ac1.account = loan_account
		ac1.credit_in_account_currency = adv.principal_amount

	for earn in sal_slip.earnings:
		ed[earn.salary_component] = ed.get(earn.salary_component,0) + earn.amount

	for dedu in sal_slip.deductions:
		ed[dedu.salary_component] = ed.get(dedu.salary_component,0) + (-1 * dedu.amount)


