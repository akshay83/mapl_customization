# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import flt, fmt_money

def execute(filters=None):
	columns, data = [], []
	#if (not filters.get("customer_group") and not filters.get("party_type")):
	#	return columns, data

	columns = [
			{
				"fieldname":"posting_date",
				"label":"Date",
				"fieldtype":"Date",
				"width": 125
			},
			{
				"fieldname":"voucher_type",
				"label":"Type",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"voucher_no",
				"label":"Voucher Ref",
				"fieldtype":"Dynamic Link",
				"options":"voucher_type",
				"width": 250
			},
			{
				"fieldname":"debit",
				"label":"Debit",
				"fieldtype":"Currency",
				"width": 125
			},
			{
				"fieldname":"credit",
				"label":"Credit",
				"fieldtype":"Currency",
				"width": 125
			},
			{
				"fieldname":"running",
				"label":"Running Balance",
				"fieldtype":"Data",
				"width": 125
			},
			{
				"fieldname":"chq_no",
				"label":"Reference No",
				"fieldtype":"Data",
				"width": 125
			},
			{
				"fieldname":"against",
				"label":"Against A/c",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"against_name",
				"label":"Against Name",
				"fieldtype":"Data",
				"width": 150
			},
			{
				"fieldname":"remarks",
				"label":"Remarks",
				"fieldtype":"Text",
				"width": 250
			}
	]

	data = get_groupwise_statement(filters)

	#if ((filters.get("party") and filters.get("party_type")) or filters.get("account") \
	#	and filters.get("from_date") and filters.get("to_date")):
	#	data = get_individual_statement(filters)

	return columns, data


def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " posting_date >= '%s'" % frappe.db.escape(filters["from_date"])


	if filters.get("to_date"):
		conditions += " and posting_date <= '%s'" % frappe.db.escape(filters["to_date"])

	if filters.get("party"):
		conditions += " and party = '%s'" % filters["party"]

	return conditions


def get_opening(filters, party_name):
	query = """select 
			  ifnull(sum(debit-credit),0) as opening_balance
			from 
			  `tabGL Entry` 
			where
			  posting_date < '{start_date}'
			  and party_type = '{party_type}' and party = '{party_name}'"""
	build_row = {}

	query = query.format(**{
				"start_date":frappe.db.escape(filters["from_date"]),
				"party_name": party_name,
				"party_type": filters.get("party_type")
				})

	for q in frappe.db.sql(query, as_dict=1):
		build_row["voucher_type"] = "Opening Balance"
		if q.opening_balance <=0:
			build_row["credit"] = abs(q.opening_balance)
		else:
			build_row["debit"] = abs(q.opening_balance)

	return build_row

def get_closing_balance(total_debit, total_credit):
	closing = {}
	closing["voucher_type"] = "Closing Totals"
	closing["debit"] = total_debit
	closing["credit"] = total_credit

	balance = {}
	if (total_debit < total_credit):
		balance["debit"] = total_credit-total_debit
	elif (total_debit > total_credit):
		balance["credit"] = total_debit-total_credit
	balance["voucher_type"] = "Balance"

	return closing, balance

def get_customer_group(filters):

	query = """
                   and customer.customer_group in (
                    select
                       ig1.name
                    from
                       `tabCustomer Group` ig1,
                        (select name, parent_customer_group,lft, rgt from `tabCustomer Group` where name = '{group}') ig2
                    where
                       ig2.lft <= ig1.lft
                       and ig2.rgt >= ig1.rgt
                    )
		"""

	query = query.format(**{
				"group":filters["customer_group"]
				})

	return query


def get_groupwise_statement(filters):
	query = """
                        select
                          customer.name,
                          customer.{docname}_name,
                          gl_entry.posting_date,
                          gl_entry.voucher_type,
                          gl_entry.voucher_no,
                          ifnull(sum(gl_entry.debit),0) as debit,
                          ifnull(sum(gl_entry.credit),0) as credit,
                          if((gl_entry.voucher_type like 'Journal %'),
                               (select cheque_no from `tabJournal Entry` where name=gl_entry.voucher_no),
                               if((gl_entry.voucher_type like 'Payment %'),
                                    (select reference_no from `tabPayment Entry` where name=gl_entry.voucher_no),
                                    null
                               )
                          ) as chq_no,
                          gl_entry.against
                        from
                          `tabGL Entry` gl_entry,
                          `tab{Document}` customer
                        where
                          customer.name = gl_entry.party
                          and {date_range}
			  {group_query}
                        group by
                          gl_entry.voucher_no,
                          gl_entry.party
                        order by
                          customer.{docname}_name,
                          gl_entry.posting_date
		"""

	query = query.format(**{
				"date_range":get_conditions(filters),
				"group_query": get_customer_group(filters) if filters.get("customer_group") else "",
				"Document": filters.get("party_type"),
				"docname": filters.get("party_type").lower()
				})

	rows = []
	total_credit = 0
	total_debit = 0
	current_customer_name = None
	current_customer = None

	for d in frappe.db.sql(query, as_dict=1):
		if not current_customer or current_customer != d.name:
			if current_customer:
				closing, balance = get_closing_balance(total_debit, total_credit)
				rows.append(closing)
				rows.append(balance)
				rows.append([])

			opening = {}
			#opening["voucher_type"] = d.name
			if filters.get("party_type") == "Customer":
				opening["voucher_no"] = d.customer_name + " (" + d.name + ")"
			elif filters.get("party_type") == "Employee":
				opening["voucher_no"] = d.employee_name + " (" + d.name + ")"
			elif filters.get("party_type") == "Supplier":
				opening["voucher_no"] = d.supplier_name + " (" + d.name + ")"

			rows.append(opening)
			opening = get_opening(filters, d.name)
			rows.append(opening)
			current_customer = d.name
			total_credit = opening.get("credit",0)
			total_debit = opening.get("debit",0)

		total_credit += d.credit
		total_debit += d.debit

		build_row = {}
		build_row["debit"] = d.debit
		build_row["posting_date"] = d.posting_date
		build_row["credit"] = d.credit
		running_balance = total_debit-total_credit
		build_row["running"] = (str(fmt_money(abs(running_balance))) + " Cr.") if running_balance < 0 else (str(fmt_money(abs(running_balance))) + " Dr.")
		build_row["voucher_type"] = d.voucher_type
		build_row["voucher_no"] = d.voucher_no
		build_row["against"] = d.against
		build_row["against_name"] = d.against_name
		build_row["chq_no"] = d.chq_no
		rows.append(build_row)

	closing, balance = get_closing_balance(total_debit, total_credit)
	rows.append(closing)
	rows.append(balance)

	return rows
