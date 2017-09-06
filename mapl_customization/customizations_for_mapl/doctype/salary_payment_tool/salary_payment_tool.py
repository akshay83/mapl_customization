# -*- coding: utf-8 -*-
# Copyright (c) 2017, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import cint
from mapl_customization.customizations_for_mapl.report.custom_salary_register.custom_salary_register import get_employee_details

class SalaryPaymentTool(Document):
	pass


@frappe.whitelist()
def fetch_details(from_date, to_date):

	filters = {}

	filters.update({"from_date": from_date, "to_date":to_date})

	details = get_employee_details(filters)

	return details

@frappe.whitelist()
def make_jv(docname):
	salary_doc = frappe.get_doc("Salary Payment Tool", docname)
	if not salary_doc:
		return

	for i in salary_doc.payment_details:
		if i.transaction_reference and not cint(i.imported) \
			and not frappe.db.exists("Journal Entry", { "cheque_no": i.transaction_reference, "docstatus":1}):
			jv = frappe.new_doc("Journal Entry")
			jv.posting_date = salary_doc.pay_date
			jv.cheque_no = i.transaction_reference
			jv.cheque_date = salary_doc.pay_date
			jv.company = salary_doc.company

			ac1 = jv.append("accounts")
			ac1.party_type = 'Employee'
			ac1.party = i.employee
			ac1.party_name = i.employee_name
			ac1.debit_in_account_currency = i.amount_paid
			ac1.account = salary_doc.payable_account

			ac2 = jv.append("accounts")
			ac2.account = salary_doc.payment_account
			ac2.credit_in_account_currency = i.amount_paid

			jv.save()
			jv.submit()

			i.journal_reference = jv.name
			i.imported = 1
	salary_doc.save()
