# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe

def execute(filters=None):
	columns, data = [], []
	columns = [
		{
			"fieldname":"posting_date",
			"label":"Date",
			"fieldtype":"Date",
			"width": 100
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
			"width": 150
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
			"fieldname":"debit",
			"label":"Debit",
			"fieldtype:":"Currency",
			"width": 125
		},
		{
			"fieldname":"credit",
			"label":"Credit",
			"fieldtype:":"Currency",
			"width": 125
		},
		{
			"fieldname":"chq_no",
			"label":"Reference No",
			"fieldtype:":"Data",
			"width": 125
		},
		{
			"fieldname":"remarks",
			"label":"Remarks",
			"fieldtype:":"Text",
			"width": 250
		}

	]

	if ((filters.get("party") and filters.get("party_type")) or filters.get("account") \
		and filters.get("from_date") and filters.get("to_date")):
		data = get_details(filters)

	return columns, data


def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " posting_date >= '%s'" % frappe.db.escape(filters["from_date"])


	if filters.get("to_date"):
		conditions += " and posting_date <= '%s'" % frappe.db.escape(filters["to_date"])

	return conditions


def get_account_filters(filters):
	conditions = ""

	if filters.get("account"):
		conditions += " and account = '%s'" % filters["account"]

	if filters.get("party_type"):
		conditions += " and party_type = '%s'" % filters["party_type"]

	if filters.get("party"):
		conditions += " and party = '%s'" % filters["party"]


	return conditions


def get_opening(filters):
	query = """select 
			  ifnull(sum(debit-credit),0) as opening_balance
			from 
			  `tabGL Entry` 
			where
			  posting_date < '{start_date}'
			  {condition}"""
	build_row = {}

	query = query.format(**{
				"start_date":frappe.db.escape(filters["from_date"]),
				"condition": get_account_filters(filters)
				})

	for q in frappe.db.sql(query, as_dict=1):
		build_row["voucher_type"] = "Opening Balance"
		if q.opening_balance <=0:
			build_row["credit"] = abs(q.opening_balance)
		else:
			build_row["debit"] = abs(q.opening_balance)

	return build_row



def get_details(filters):
	opening = get_opening(filters)
	total_credit = opening.get("credit",0)
	total_debit = opening.get("debit",0)
	rows = []
	rows.append(opening)

	query = """select 
			  posting_date,
			  voucher_type,
			  voucher_no,
			  remarks,
			  if((voucher_type like 'Journal %'),
			    (select cheque_no from `tabJournal Entry` where name=voucher_no),
			    if((voucher_type like 'Payment %'), 
			      (select reference_no from `tabPayment Entry` where name=voucher_no),
			      null
			    )
			  ) as chq_no,
			  against,
			  sum(debit) as debit,
			  sum(credit) as credit,
			   if(against is not null and length(against)<=10,
				        if(against like 'Cust-%',
				          (select customer_name from `tabCustomer` where name = gl.against),
				          if (against like 'Supp-%',
				            (select supplier_name from `tabSupplier` where name = gl.against),
				            if (against like 'EMP/%',
						(select employee_name from `tabEmployee` where name = gl.against),
						null
					    )
				          )
				        ),
				        null
			  ) as `against_name`
			from 
			  `tabGL Entry` gl
			where
			  {date_range}
			  {condition}
			group by voucher_no
			order by posting_date"""

	build_row = {}

	query = query.format(**{
				"date_range": get_conditions(filters),
				"condition":get_account_filters(filters)
				})

	for d in frappe.db.sql(query, as_dict=1):
		build_row = {}
		build_row["posting_date"] = d.posting_date
		build_row["voucher_type"] = d.voucher_type
		build_row["voucher_no"] = d.voucher_no
		build_row["remarks"] = d.remarks
		build_row["debit"] = d.debit
		build_row["credit"] = d.credit
		build_row["against"] = d.against
		build_row["against_name"] = d.against_name
		build_row["chq_no"] = d.chq_no
		total_credit += d.credit
		total_debit += d.debit
		rows.append(build_row)

	rows.append({"voucher_type": "Total", "debit":total_debit, "credit":total_credit})

	rows.append({"voucher_type":"Closing Balance",
			"debit": (total_debit-total_credit) if (total_debit>total_credit) else 0,
			"credit": (total_credit-total_debit) if (total_credit>total_debit) else 0
		    })

	return rows
