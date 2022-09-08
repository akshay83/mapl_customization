# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import getdate, cstr, flt, fmt_money, formatdate

def execute(filters=None):
	columns, data = [], []
	columns = [
		{
			"fieldname":"posting_date",
			"label":"Date",
			"fieldtype":"Date",
			"width": 125
		},
		{
			"fieldname":"debit",
			"label":"Debit",
			"fieldtype:":"Data",
			"precision": 2,
			"width": 150
		},
		{
			"fieldname":"credit",
			"label":"Credit",
			"fieldtype:":"Data",
			"precision": 2,
			"width": 150
		},
		{
			"fieldname":"running_balance",
			"label":"Balance",
			"fieldtype:":"Data",
			"precision": 2,
			"width": 150
		}
	]

	if (filters.get("from_date") and filters.get("to_date")):
		data = get_details(filters)

	return columns, data


def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " posting_date >= %s" % frappe.db.escape(filters["from_date"])

	if filters.get("to_date"):
		conditions += " and posting_date <= %s" % frappe.db.escape(filters["to_date"])

	return conditions

def get_opening(filters):
	query = """
			select
			  ifnull(sum(debit-credit),0) as opening_balance
			from
			  `tabGL Entry`
			where
			  posting_date < {start_date}
			  and account like 'Cash%'
			""".format(**{
					"start_date":frappe.db.escape(filters["from_date"]),
				})
				
	build_row = {}
	for q in frappe.db.sql(query, as_dict=1):
		build_row["posting_date"] = "Opening Balance"
		if q.opening_balance <=0:
			build_row["credit"] = abs(q.opening_balance)
		else:
			build_row["debit"] = abs(q.opening_balance)
	return build_row

def get_details(filters):
	opening = get_opening(filters)
	total_credit = opening.get("credit",0.00)
	total_debit = opening.get("debit",0.00)
	opening["credit"] = fmt_money(total_credit)
	opening["debit"] = fmt_money(total_debit)
	rows = []
	rows.append(opening)

	query = """
				select
			  		posting_date,
			  		sum(debit) as debit,
			  		sum(credit) as credit
				from
			  		`tabGL Entry` gl
				where
			  		{date_range}
			  		and account like 'Cash%'
				group by posting_date
				order by posting_date
			""".format(**{
					"date_range": get_conditions(filters),
			})

	build_row = {}
	for d in frappe.db.sql(query, as_dict=1):
		build_row = {}
		build_row["posting_date"] = d.posting_date
		build_row["debit"] = fmt_money(d.debit or 0)
		build_row["credit"] = fmt_money(d.credit or 0)
		total_credit += d.credit
		total_debit += d.debit
		build_row["running_balance"] = str(fmt_money(abs(total_debit-total_credit),2)) + (" Cr" if (total_debit-total_credit) < 0 else " Dr")
		rows.append(build_row)

	rows.append({"posting_date": "Total", "debit":fmt_money(total_debit), "credit":fmt_money(total_credit)})

	rows.append({"posting_date":"Closing Balance",
			"debit": fmt_money((total_debit-total_credit) if (total_debit>total_credit) else 0),
			"credit": fmt_money((total_credit-total_debit) if (total_credit>total_debit) else 0)
		    })

	return rows
