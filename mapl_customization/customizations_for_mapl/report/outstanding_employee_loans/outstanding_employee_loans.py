# Copyright (c) 2022, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
from erpnext.loan_management.doctype.loan_repayment.loan_repayment import calculate_amounts
from frappe.utils import getdate

def execute(filters=None):
	columns, data = get_columns(filters), get_data(filters)
	return columns, data

def get_columns(filters):
	columns = [{
				"fieldname":"employee",
				"label": "Employee",
				"fieldtype":"Link",
				"options":"Employee",
				"width": 120
			},
			{
				"fieldname":"employee_name",
				"label": "Employee Name",
				"fieldtype":"Data",
				"width": 150
			},
			{
			"fieldname":"total_balance_loan",
			"label": "Total Balance",
			"fieldtype":"Currency",
			"width": 120
			}]
	return columns

def get_data(filters):
	query = """
				select 
  					loans.name,
					loans.applicant,
					loans.applicant_name
				from
  					`tabLoan` loans	
				where
					loans.status in ('Partially Disbursed','Disbursed')
				{0}
				order by
					loans.applicant
	"""
	if filters.get("employee"):
		query = query.format(" and loans.applicant = '{0}'".format(filters.get("employee")))
	else:
		query = query.format("")

	applicant = None
	applicant_name = None
	rows = []
	build_row = {}
	total_loan = 0
	for loan in frappe.db.sql(query, as_dict=1):
		if not applicant:
			applicant = loan.applicant
			applicant_name = loan.applicant_name
		if applicant != loan.applicant:
			build_row["employee"] = applicant
			build_row["employee_name"] = applicant_name
			build_row["total_balance_loan"] = total_loan
			rows.append(build_row)
			build_row = {}
			total_loan = 0
			applicant_name = loan.applicant_name
			applicant = loan.applicant
		amounts = calculate_amounts(loan.name, getdate(), payment_type='Loan Closure')
		total_loan += amounts['payable_amount']
	build_row["employee"] = applicant
	build_row["employee_name"] = applicant_name
	build_row["total_balance_loan"] = total_loan
	rows.append(build_row)
	return rows
