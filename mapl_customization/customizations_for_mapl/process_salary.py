import frappe
import erpnext
import json
import mapl_customization
from frappe.utils import cint
from mapl_customization.customizations_for_mapl.report.custom_salary_register.custom_salary_register import get_employee_details
from erpnext import get_default_cost_center

@frappe.whitelist()
def process_staff_salaries_jv(payable_account, date, filters, director):

	if isinstance(filters, str):
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

	for comp, amount in earnings_deductions.items():
		ac1 = jv.append("accounts")
		account = frappe.get_list("Salary Component Account", filters={"parent":comp}, fields=["account","company"])
		
		ac1.account = account[0].account #account[0].account
		if amount > 0:
			ac1.debit_in_account_currency = amount
		elif amount < 0:
			ac1.credit_in_account_currency = abs(amount)
		ac1.cost_center = get_default_cost_center(account[0].company)

	jv.save()

def process_staff_jv(jv, record, account, ed):
	ac1 = jv.append("accounts")
	ac1.party_type = 'Employee'
	ac1.party = record["employee_id"]
	ac1.party_name = record["employee_name"]
	ac1.account = account
	if mapl_customization.is_this_app_installed() and cint(frappe.db.get_single_value("Payroll Settings", "simplify_employee_loan_repayment")):
		ac1.credit_in_account_currency = record["net_pay"]
	else:
		ac1.credit_in_account_currency = record["net_pay"]+record.get("total_loan",0)

	process_earnings_deductions(jv, record, account, ed)

def process_earnings_deductions(jv, record, account, ed):
	sal_slip = frappe.get_doc("Salary Slip", record["salary_slip_id"])
	if mapl_customization.is_this_app_installed() and cint(frappe.db.get_single_value("Payroll Settings", "simplify_employee_loan_repayment")):
		for adv in sal_slip.loans:
			ac1 = jv.append("accounts")
			ac1.party_type = 'Employee'
			ac1.party_name = record["employee_name"]
			ac1.party = record["employee_id"]
			ac1.account = frappe.db.get_value("Loan", adv.loan , "loan_account")
			ac1.credit_in_account_currency = adv.principal_amount

	for earn in sal_slip.earnings:
		ed[earn.salary_component] = ed.get(earn.salary_component,0) + earn.amount

	for dedu in sal_slip.deductions:
		ed[dedu.salary_component] = ed.get(dedu.salary_component,0) + (-1 * dedu.amount)
