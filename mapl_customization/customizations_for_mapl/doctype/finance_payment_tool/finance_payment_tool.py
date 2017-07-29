# -*- coding: utf-8 -*-
# Copyright (c) 2017, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document
from frappe.utils import cint

class FinancePaymentTool(Document):
	pass


@frappe.whitelist()
def make_jv(doc_name):
	payment_doc = frappe.get_doc("Finance Payment Tool", doc_name)
	if not payment_doc:
		return

	for i in payment_doc.payment_details:
		if i.internal_customer and not cint(i.imported) \
			and not frappe.db.exists("Journal Entry", { "cheque_no": i.transaction_id, "docstatus":1}):
			jv = frappe.new_doc("Journal Entry")
			jv.naming_series = 'MAPL/FIN-JV/.YYYY./.######'
			jv.posting_date = i.transaction_date
			jv.cheque_no = i.transaction_id

			ac1 = jv.append("accounts")
			ac1.party_type = 'Customer'
			ac1.party = i.internal_customer
			ac1.credit_in_account_currency = i.amount_paid

			ac2 = jv.append("accounts")
			ac2.account = payment_doc.account_paid_to
			ac2.debit_in_account_currency = i.amount_paid

			jv.hypothecation_company = payment_doc.finance_company
			jv.save()
			jv.submit()

			i.journal_reference = jv.name
			i.imported = 1
	payment_doc.save()


@frappe.whitelist()
def fetch_customers(doc_name):
	complete_query=	"""
		   select 
			  name, 
			  customer_name 
		   from 
			  `tabSales Invoice` 
		   where 
			  reference regexp (select group_concat(substr(finance_reference,4) separator '|') 
			        from `tabFinance Payment Details` 
			        where parent='Test BFL' 
			        group by 'all')"""
	update_query = """
		update 
		  `tabFinance Payment Details` fpd 
		set fpd.internal_customer = (select customer 
			         from `tabSales Invoice`
			         where reference regexp substr(fpd.finance_reference,4) order by posting_date desc limit 1),
		    fpd.internal_customer_name = (select customer_name
			         from `tabSales Invoice`
			         where reference regexp substr(fpd.finance_reference,4) order by posting_date desc limit 1)
		where
		    fpd.parent = %s"""

	frappe.db.sql(update_query,doc_name)
	frappe.db.commit()
