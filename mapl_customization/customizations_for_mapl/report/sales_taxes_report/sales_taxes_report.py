# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.utils import formatdate

def execute(filters=None):
	if not filters:
		filters = {}

	columns = get_columns(filters)
	data = get_data(filters=filters)
	return columns, data

def get_data(filters):
	result_rows = []
	rows = get_data_query(filters)
	for r in rows:
		build_row = {}
		build_row["sales_invoice"] = r.name
		build_row["posting_date"] = formatdate(r.posting_date,"dd-MM-YYYY")
		build_row["tin_no"] = r.tax_id
		build_row["customer"] = r.customer_name
		build_row["rate"] = r.rate
		build_row["charge_type"] = r.charge_type
		build_row[r.account_head+" "+str(r.rate)] = \
			r.tax_amount_after_discount_amount
		result_rows.append(build_row)
	return result_rows	

def get_columns(filters):
	distinct_rows = get_column_query(filters)

	columns = [
		{
			"fieldname":"sales_invoice",
			"label":"Sales Invoice No",
			"fieldtype":"Link",
			"options":"Sales Invoice"
		},
		{
			"fieldname":"posting_date",
			"label":"Posting Date",
			"fieldtype:":"Date"
		},
		{
			"fieldname":"customer",
			"label":"Customer Name",
			"fieldtype":"Data"
		},
		{
			"fieldname":"tin_no",
			"label":"Tin No",
			"fieldtype":"Data"
		},
		{
			"fieldname":"rate",
			"label":"Rate",
			"fieldtype":"Float"
		},
		{
			"fieldname":"charge_type",
			"label":"Charge Type",
			"fieldtype":"Data"
		}
	]
	for rows in distinct_rows:
		columns.append({
			"fieldname":rows.account_head+" "+str(rows.rate),
			"label":rows.account_head+" "+str(rows.rate),
			"fieldtype":"Float"
		})

	return columns

def get_condition(filters):
	condition = ""
	
	if filters:
		if filters.get("fromdate"):
			condition += " and inv.posting_date>=%(fromdate)s"

		if filters.get("todate"):
			condition += " and inv.posting_date<=%(todate)s"

	return condition

def get_column_query(filters):
	condition = get_condition(filters)

	query = """select distinct taxes.rate,taxes.account_head,taxes.charge_type
		from `tabSales Invoice` inv, `tabSales Taxes and Charges` taxes
		where taxes.parent = inv.name and inv.docstatus = 1 and inv.company=%(company)s {condition} 
		order by taxes.rate""".format(**{
			"condition":condition
			})

	return frappe.db.sql(query, { 
			'fromdate': str(filters.get("fromdate","")),
			'todate':str(filters.get("todate","")),
			'company':filters.get("company","")
			},as_dict=True)	

def get_data_query(filters):
	condition = get_condition(filters)

	query = """select inv.name,cust.customer_name,cust.tax_id,inv.posting_date,
		taxes.rate,taxes.charge_type,taxes.account_head,taxes.tax_amount_after_discount_amount
		 from `tabSales Invoice` inv, `tabSales Taxes and Charges` taxes,
		`tabCustomer` cust where taxes.parent = inv.name and cust.name=inv.customer and 
		inv.docstatus = 1 and inv.company=%(company)s {condition} order by taxes.rate""".format(**{
			"condition":condition
			})

	return frappe.db.sql(query, { 
			'fromdate': str(filters.get("fromdate","")),
			'todate':str(filters.get("todate","")),
			'company':filters.get("company","")
			},as_dict=True)	
		
