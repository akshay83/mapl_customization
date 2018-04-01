# -*- coding: utf-8 -*-
# Copyright (c) 2017, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json
from frappe.model.document import Document
from frappe.utils import cint, flt
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
	short_fiscal_year = fiscal_year[2,4] + "-" + fiscal_year[7:9]
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
		conditions += """ and sales.posting_date >= '%s'""" % filters["from_date"]

	if filters.get("to_date"):
		conditions += """ and sales.posting_date <= '%s'""" % filters["to_date"]

	if filters.get("is_financed"):
		if cint(filters["is_financed"]) == 0:
			conditions += """ and sales.hypothecation is null """

		if cint(filters["is_financed"]) == 1:
			conditions += """ and sales.hypothecation is not null """

	return conditions


def get_condition(filters):
	conditions = " and "
	tp = filters.get("threshold_percentage", 0)
	ta = filters.get("threshold_amount", 0)

	if flt(tp) != 0:
		conditions += """ abs(b.out_perc) < %s""" % tp

	elif flt(ta) != 0:
		conditions += """ abs(b.current_balance) < %s""" % ta

	return conditions

@frappe.whitelist()
def fetch_details(filters):
	if isinstance(filters, basestring):
		filters = json.loads(filters)

	if not filters.get("from_date") and not filters.get("to_date"):
		return

	update_query =	"""
			select * from 
			  (select *, 
			      (((current_balance+total_dbd)/total_billing)*100) as out_perc 
			    from 
			    (select sales.customer_name,
			      sales.customer,
			      (select sum(grd.grand_total) 
			         from `tabSales Invoice` grd
			         where 
			            grd.customer = sales.customer
			              and grd.docstatus = 1) as `total_billing`,
			      (select ifnull(sum(debit),0)-ifnull(sum(credit),0) 
			          from `tabGL Entry` 
			          where 
			            party=sales.customer 
			            and party_type='Customer') as `current_balance`,
                              (select ifnull(sum(credit),0)-ifnull(sum(debit),0)
                                  from `tabGL Entry`
                                  where
                                    against like '%Dealer Bu%'
                                    and party=sales.customer
                                    and party_type='Customer') as `total_dbd`
			    from `tabSales Invoice` sales
			    where sales.docstatus=1
			       {period_condition}
			    group by customer
			    order by customer_name) a
			  ) b
			  where b.current_balance <> 0
			  {threshold_condition} order by out_perc desc""".format(**{
				"period_condition": get_period_condition(filters),
				"threshold_condition": get_condition(filters)
			   })

	details = frappe.db.sql(update_query, as_dict=1)

	return details
