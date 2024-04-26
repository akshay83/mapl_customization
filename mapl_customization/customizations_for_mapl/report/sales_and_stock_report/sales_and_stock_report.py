# Copyright (c) 2024, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
from frappe.utils import flt, getdate
from mapl_customization.customizations_for_mapl.report.sales_taxes_report.sales_taxes_report import extract_columns
from mapl_customization.customizations_for_mapl.utils import get_effective_stock_at_all_warehouse

def execute(filters=None):
	data = get_sale_data(filters)
	report = []
	for d in data:
		stk_details = d
		c,stk = get_effective_stock_at_all_warehouse(d['Item:Link/Item:150'], filters.get("to_date"))
		for s in stk:
			if s['warehouse'] == d['Warehouse:Data:150']:
				stk_details.update({"Balance Qty:Data:100":s['balance_qty'],"Effective Qty:Data:100":s['effective_qty']})
		if stk and len(stk)>0:
			report.append(stk_details)
	#columns, data = [], []
	columns = extract_columns(report)
	return columns, report

def get_sale_data(filters):
	query = """
			select
				sales.name as `ID:Link/Sales Invoice:200`,
				sales.letter_head as `Letter Head:Data:100`,   
				if(sales.docstatus=1,'Submitted', 'Draft') as `Document Status:Data:125`, 
				sales.posting_date as `Date:Date:100`,
				sales.customer as `Customer:Link/Customer:100`,
				sales.customer_name as `Customer Name:Data:150`,
				details.warehouse as `Warehouse:Data:150`, 
				details.brand as `Brand:Data:100`,
				details.item_code as `Item:Link/Item:150`,
				details.item_group as `Item Group:Link/Item Group:150`,
				details.qty as `Qty:Float:70`,
				details.rate as `Rate:Float:100`,
				details.amount as `Amount:Float:100`
			from
				`tabSales Invoice` sales,
				`tabSales Invoice Item` details
			where
				details.parent=sales.name
				and sales.posting_date>='{from_date}'
				and sales.posting_date<='{to_date}'
				and ifnull(sales.letter_head,'') like (if('{letter_head}'='All','%%','{letter_head}'))
				{brands_filter}
				and ifnull(details.item_group,'') like '{item_group}'
				and sales.docstatus >= if('{show_draft}'='Include Draft',0,1)
				and sales.docstatus <> 2
			order by
				sales.letter_head, sales.posting_date	
		""".format(**{
			"brands_filter": "and ifnull(details.brand,'') regexp ('{0}')".format(filters.get("brands_array")) if filters.get("brands_array") else "",
			"from_date": filters.get("from_date"),
			"to_date": filters.get("to_date"),
			"letter_head": filters.get("letter_head"),
			"item_group": filters.get("item_group", "%%"),
			"show_draft": filters.get("show_draft")
		})
	print (query)
	print ()
	return frappe.db.sql(query, as_dict=1)
