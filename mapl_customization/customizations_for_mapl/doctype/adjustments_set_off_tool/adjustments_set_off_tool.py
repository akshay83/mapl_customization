# -*- coding: utf-8 -*-
# Copyright (c) 2017, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import cint, flt, getdate
from erpnext.accounts.doctype.journal_entry.journal_entry import get_party_account_and_balance
from erpnext.accounts.utils import get_fiscal_year

class AdjustmentsSetOffTool(Document):
	pass

@frappe.whitelist()
def make_jv(doc_name):
	payment_doc = frappe.get_doc("Adjustments Set Off Tool", doc_name)
	if not payment_doc:
		return
	if payment_doc.journal_reference:
		return

	jv = frappe.new_doc("Journal Entry")

	from frappe.model.naming import make_autoname
	abbr = frappe.db.get_value("Company", payment_doc.company, "abbr")
	fiscal_year = get_fiscal_year(date=payment_doc.adjustment_date)[0]
	short_fiscal_year = fiscal_year[2:4] + "-" + fiscal_year[7:9]
	if getdate(payment_doc.adjustment_date) <= getdate('2018-03-31'):
		jv.naming_series = 'MAPL/FIN-JV/.YYYY./.######'
	else:
		jv.naming_series = abbr+"/FIN-JV/"+short_fiscal_year+"/"+".######"

	jv.posting_date = payment_doc.adjustment_date
	jv.company = payment_doc.company

	adj_acc_credit_total = 0
	adj_acc_debit_total = 0

	for i in payment_doc.adjustment_detail:
		if i.customer and not cint(i.imported):
			ac1 = jv.append("accounts")
			ac1.party_type = 'Customer'
			ac1.party = i.customer
			if i.difference_amount > 0:
				ac1.credit_in_account_currency = abs(i.difference_amount)
			elif i.difference_amount < 0:
				ac1.debit_in_account_currency = abs(i.difference_amount)

			ac1.account = get_party_account_and_balance(payment_doc.company, \
				'Customer', i.customer)['account']

			if i.difference_amount > 0:
				adj_acc_debit_total += abs(i.difference_amount)
			elif i.difference_amount < 0:
				adj_acc_credit_total += abs(i.difference_amount)


			i.imported = 1

	ac2 = jv.append("accounts")
	ac2.account = payment_doc.adjustment_account
	ac2.debit_in_account_currency = adj_acc_debit_total

	ac3 = jv.append("accounts")
	ac3.account = payment_doc.adjustment_account
	ac3.credit_in_account_currency = adj_acc_credit_total

	jv.save()
	jv.submit()
	payment_doc.journal_reference = jv.name
	payment_doc.save()

def get_period_condition(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += """ and gl_entry.posting_date >= '%s'""" % filters["from_date"]
	if filters.get("to_date"):
		conditions += """ and gl_entry.posting_date <= '%s'""" % filters["to_date"]
	return conditions

def get_finance_condition(filters):
	conditions = ""
	if filters.get("is_financed"):
		if cint(filters["is_financed"]) == 0:
			conditions += """where data.`Hypothecation` <= 0"""
		if cint(filters["is_financed"]) == 1:
			conditions += """where data.`Hypothecation` > 0"""
	return conditions

def get_cut_off_date(filters):
	return """'%s'""" % filters["check_balance_till"]


def get_condition(filters):
	conditions = " and "
	tp = filters.get("threshold_percentage", 0)
	ta = filters.get("threshold_amount", 0)
	if flt(tp) != 0:
		conditions += """ abs(`Percentage`) < %s""" % tp
	elif flt(ta) != 0:
		conditions += """ abs(`Difference`) < %s""" % ta
	return conditions

@frappe.whitelist()
def fetch_details(filters):
	if isinstance(filters, str):
		filters = json.loads(filters)

	if not filters.get("from_date") and not filters.get("to_date") and not filters.get("check_balance_till"):
		return

	update_query =	"""select * from (
				select 
				  *,
				  cast(`Total Debit`-`Total Credit` as Decimal(17,2)) as `Difference`,
				  cast((((`Total Debit`-`Total Credit`)/`Total Debit`)*100) as Decimal(8,2)) as `Percentage`
				from
				  (select 
				    dump.party,
				    customer.customer_name,
				    cast(sum(dump.debit) as Decimal(17,2)) as `Total Debit`,
				    cast(sum(dump.credit) as Decimal(17,2)) as `Total Credit`,
				    count(dump.hypothecation) as `Hypothecation`,
				    dump.`Current Balance` as `Current Balance`
				  from
				  (select 
				      gl_entry.voucher_type,
				      gl_entry.voucher_no,
				      gl_entry.posting_date,
				      gl_entry.debit,
				      gl_entry.credit,
				      gl_entry.party,
				      sales_invoice.hypothecation,
				      sales_invoice.reference,
				      (select sum(debit-credit) from `tabGL Entry` 
					where party=gl_entry.party 
					and posting_date <= {cut_off_balance}) as `Current Balance`
				    from   
				      `tabGL Entry` gl_entry
				      left join
				      `tabSales Invoice` sales_invoice
				      on
				      gl_entry.voucher_no = sales_invoice.name
				    where   
				      gl_entry.party_type = 'Customer'
				      {period_condition}
				    order by 
				      gl_entry.posting_date) as dump,
				    `tabCustomer` customer
				  where
				    customer.name = dump.party
				  group by 
				    dump.party) as data
				  {finance_condition}
				) as final_data
				where 
				    abs(`Current Balance`) <> 0
				    and abs(`Difference`) <> 0
			            {threshold_condition}
			""".format(**{
				"period_condition": get_period_condition(filters),
				"threshold_condition": get_condition(filters),
				"finance_condition": get_finance_condition(filters),
				"cut_off_balance": get_cut_off_date(filters)
			   })

	details = frappe.db.sql(update_query, as_dict=1)
	return details
