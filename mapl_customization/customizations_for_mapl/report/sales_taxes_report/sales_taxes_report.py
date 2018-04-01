# Copyright (c) 2013, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
import json

def execute(filters=None):
	columns, data = [], []
	columns = [
		{
			"fieldname":"invoice_name",
			"label":"Invoice Name",
			"fieldtype":"Link",
			"options":"Sales Invoice" if (filters.get("document_type") and filters["document_type"]=="Sales") else "Purchase Invoice",
			"width": 150
		},
		{
			"fieldname":"reporting_name",
			"label":"Reporting Name",
			"fieldtype":"Data",
			"width": 150
		},
		{
			"fieldname":"invoice_no",
			"label":"Invoice No",
			"fieldtype":"Data",
			"width": 150
		},
		{
			"fieldname":"posting_date",
			"label":"Posting Date",
			"fieldtype:":"Date",
			"width": 100
		},
		{
			"fieldname":"invoice_date",
			"label":"Invoice Date",
			"fieldtype:":"Date",
			"width": 100
		},
		{
			"fieldname":"party_name",
			"label":"Party Name",
			"fieldtype:":"Data",
			"width": 125
		},
		{
			"fieldname":"supplier_type",
			"label":"Supplier Type",
			"fieldtype:":"Data",
			"width": 100
		},
		{
			"fieldname":"supply_type",
			"label":"Supply Type",
			"fieldtype:":"Data",
			"width": 100
		},
		{
			"fieldname":"party_gstin",
			"label":"Party GSTIN",
			"fieldtype:":"Data",
			"width": 100
		},
		{
			"fieldname":"taxable_amt",
			"label":"Taxable Amount",
			"fieldtype:":"Float",
			"width": 100
		},
		{
			"fieldname":"charge_type",
			"label":"Charged As",
			"fieldtype:":"Data",
			"width": 75
		},
		{
			"fieldname":"total_tax",
			"label":"Total Tax",
			"fieldtype:":"Float",
			"width": 100
		}

	]
	columns.extend(get_columns(filter))
	data = get_query(filters)
	return columns, data


def get_columns(filters):
	columns = []
	query = """select distinct tax_type,tax_rate from `tabItem Tax` order by tax_rate desc"""
	for d in frappe.db.sql(query, as_dict=1):
		build_column = {}
		build_column["fieldname"] = d.tax_type+"-"+str(float(d.tax_rate))+"%"
		build_column["label"] = d.tax_type+"-"+str(d.tax_rate)+"%"
		build_column["fieldtype"] = "Float"
		build_column["width"] = 125
		columns.append(build_column)
	return columns



def get_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " and sales.posting_date >= '%s'" % frappe.db.escape(filters["from_date"])


	if filters.get("to_date"):
		conditions += " and sales.posting_date <= '%s'" % frappe.db.escape(filters["to_date"])


	return conditions


def get_document_specific_columns(filters):
	if filters.get("document_type"):
		if filters["document_type"] == "Sales":
			return """,sales.customer_gstin as gstin, sales.customer_name as party_name, sales.name as inv_no, sales.posting_date as inv_date,
				(select concat(ifnull(concat(addr.state,','),''),addr.gst_state) from `tabAddress` addr where addr.name=sales.customer_address) as state"""
	return """,sales.supplier_gstin as gstin,sales.supplier_name as party_name,sales.bill_no as inv_no,sales.bill_date as inv_date,
		  (select supplier_type from `tabSupplier` where name=sales.supplier) as supplier_type, supply_type"""



def get_query(filters):
	rows = []
	query = """select 
			    sales.name, 
			    sales.posting_date, 
			    sales.reporting_name,
			    taxes.item_wise_tax_detail, 
			    taxes.account_head, 
			    sales.net_total,
			    taxes.charge_type,
			    taxes.tax_amount
			    {doc_columns}
			  from 
			    `tab{doctype} Taxes and Charges`  taxes,
			    `tab{doctype} Invoice` sales 
			  where 
			    taxes.parent=sales.name 
			    and (taxes.charge_type != 'Actual' 
				or taxes.account_head in (select distinct tax_type from `tabItem Tax`))
			    and sales.docstatus = 1
			    {condition}
			  order by sales.name"""

	temp_name = None
	temp_account_head = None
	build_row = {}

	query = query.format(**{
				"doctype":"Sales" if (filters.get("document_type") and filters["document_type"]=="Sales") else "Purchase",
				"doc_columns": get_document_specific_columns(filters),
				"condition":get_conditions(filters)
				})

	#if filters.get("document_type") and filters["document_type"] == "Sales":
	#	query = get_sales_query().format(**{
	#				"condition":get_conditions(filters)
	#				})

	for d in frappe.db.sql(query, as_dict=1):
		if d.item_wise_tax_detail:

			if not temp_name or temp_name != d.name:
				if temp_name:
					rows.append(build_row)

				build_row = {}
				build_row["invoice_name"] = d.name
				build_row["reporting_name"] = d.reporting_name
				build_row["invoice_no"] = d.inv_no
				build_row["invoice_date"] = d.inv_date
				build_row["posting_date"] = d.posting_date
				build_row["party_gstin"] = d.gstin
				build_row["taxable_amt"] = d.net_total
				build_row["party_name"] = d.party_name
				build_row["charge_type"] = d.charge_type
				build_row["supplier_type"] = d.supplier_type if d.supplier_type else d.state
				build_row["supply_type"] = d.supply_type if d.supply_type else None
				temp_name = d.name
				temp_account_head = d.item_tax_rate

			build_row["total_tax"] = build_row.get("total_tax",0) + d.tax_amount

			tax_json = d.item_wise_tax_detail
			if isinstance(tax_json, basestring):
				tax_json = json.loads(tax_json)


			if d.charge_type != 'Actual':
				for key, val in tax_json.items():
					build_key = d.account_head+"-"+str(float(val[0]))+"%"
					build_row[build_key] = build_row.get(build_key,0) + val[1]
			else:
				doc = frappe.get_doc("{doctype} Invoice".format(**{
						"doctype":"Sales" if (filters.get("document_type") and filters["document_type"]=="Sales") else "Purchase",
						}), d.name)

				for i in doc.items:

					txs = frappe.get_doc("Item", i.item_code).taxes

					for t in txs:
						build_key = d.account_head+"-"+str(float(t.tax_rate))+"%"
						if t.tax_type==d.account_head:
							build_row[build_key] = build_row.get(build_key, 0) + round((i.net_amount * float(t.tax_rate) / 100),2)

	rows.append(build_row)
	return rows


def get_sales_query():
	return """
			select
                            sales.name,
			    sales.reporting_name,
                            cust.customer_name,
                            concat(ifnull(addr.city,''),',',ifnull(addr.state,'')) as place,
                            concat(ifnull(addr.gst_state,''),',',ifnull(addr.gst_state_number,'')) as gst_state,
                            item.item_tax_rate,
                            sales.posting_date,
                            taxes.item_wise_tax_detail,
                            taxes.account_head,
                            (item.net_amount) as taxable_amt,
                            taxes.charge_type,
                            (item.amount-item.net_amount) as tax_amount,
                            sales.customer_gstin as gstin,
                            sales.customer_name as party_name,
                            taxes.included_in_print_rate
                          from
                            `tabSales Taxes and Charges`  taxes,
                            `tabSales Invoice` sales,
                            `tabSales Invoice Item` item,
                            `tabCustomer` cust,
                            `tabAddress` addr
                          where
                            taxes.parent=sales.name
                            and item.parent=sales.name
                            and sales.customer=cust.name 
                            and addr.address_title = cust.name 
                            and sales.customer_address=addr.name  
                            and (taxes.charge_type != 'Actual'
                                or taxes.account_head in (select distinct tax_type from `tabItem Tax`))
                            and sales.docstatus = 1
			    {condition}
                          order by sales.name, item.item_tax_rate, account_head
	"""
