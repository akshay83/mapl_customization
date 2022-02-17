# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate

def execute(filters=None):
	if not filters: filters = {}

	#validate(filters)
	columns = get_columns(filters)
	data = get_data(filters)
	return columns, data

def validate(filters):
	if (not filters.get("from_date")):
		frappe.throw("From Date Cannot Be Empty")

	if (not filters.get("to_date")):
		frappe.throw("To Date Cannot Be Empty")

	if (not filters.get("item_code")):
		frappe.throw("Item Code Cannot Be Empty")

def get_columns(filters):
	"""return columns based on filters"""

	columns = [
		{
			"fieldname":"item",
			"fieldtype":"Link",
			"label":"Item",
			"options":"Item",
			"width":250
		},
		{
			"fieldname":"item_group",
			"fieldtype":"Link",
			"label":"Item Group",
			"options": "Item Group",
			"width":150
		},
		{
			"fieldname":"brand",
			"fieldtype":"Data",
			"label":"Brand",
			"width":150
		},
		{
			"fieldname":"open_qty",
			"fieldtype":"Float",
			"label":"Opening Qty",
			"width":100
		},
		{
			"fieldname":"in_qty",
			"fieldtype":"Float",
			"label":"In Qty",
			"width":100
		},
		{
			"fieldname":"out_qty",
			"fieldtype":"Float",
			"label":"Out Qty",
			"width":100
		},
		{
			"fieldname":"balance_qty",
			"fieldtype":"Float",
			"label":"Balance Qty",
			"width":100
		},
		{
			"fieldname":"unconfirmed_qty",
			"fieldtype":"Float",
			"label":"Unconfirmed Sales Qty",
			"description": "Sales Invoice in Draft Status",
			"width":100
		},
		{
			"fieldname":"undelivered_qty",
			"fieldtype":"Float",
			"label":"Undelivered Qty",
			"description": "Sales Invoice Created Without Updating Stock",
			"width":100
		},
		{
			"fieldname":"challan_qty",
			"fieldtype":"Float",
			"label":"Challan Qty",
			"description": "Products on Challan",
			"width":100
		},
		{
			"fieldname":"purchase_qty",
			"fieldtype":"Float",
			"label":"Unconfirmed Purchase Qty",
			"description": "Products on Draft Purchase",
			"width":100
		},
		{
			"fieldname":"defective_qty",
			"fieldtype":"Float",
			"label":"Defective Qty",
			"description": "Products Booked under Problematic Document",
			"width":100
		},
		{
			"fieldname":"effective_qty",
			"fieldtype":"Float",
			"label":"Effective Qty",
			"width":100
		}
	]
	return columns

def get_open_conditions(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " and posting_date < '{0}'".format(filters.get("from_date"))
	return conditions

def get_conditions(filters):
	conditions = ""
	if filters.get("from_date"):
		conditions += " and posting_date > '{0}'".format(filters.get("from_date"))

	if filters.get("to_date"):
		conditions += " and posting_date <= '{0}'".format(filters.get("to_date"))

	if filters.get("remove_material_transfer"):
		conditions += """ and if(voucher_type='Stock Entry',
			(select purpose from `tabStock Entry` se where se.name=voucher_no) 
			not like '%%Transfer%%', True)"""

	return conditions

def get_conditions_for_invoice(filters):
	conditions = ""

	if filters.get("from_date"):
		conditions += " and INV.posting_date > '{0}'".format(filters.get("from_date"))

	if filters.get("to_date"):
		conditions += " and INV.posting_date <= '{0}'".format(filters.get("to_date"))

	return conditions

def get_global_condition(filters):
	global_condition = ""
	if filters.get("item_code"):
		global_condition += " and OUTSTK.NAME = '{0}'".format(filters.get('item_code'))

	if filters.get("brand"):
		global_condition += """ AND (select brand from `tabItem` where 
			item_code=OUTSTK.NAME) = '{0}' """.format(filters.get("brand"))

	return global_condition

def get_data(filters):

	query = """
		SELECT
		  NAME,
		  ITEM_GROUP,
		  BRAND,
		  `OPENING STOCK`,
		  `IN QTY`,
		  `OUT QTY`,
		  `OPENING STOCK`+`IN QTY`-`OUT QTY` AS `CLOSING STOCK`,
		  `UNCONFIRMED`,
		  `UNDELIVERED`,
		  `CHALLAN`,
		  `PURCHASE`,
		  `DEFECTIVE`,
		  (`OPENING STOCK`+`IN QTY`-`OUT QTY`)-`UNCONFIRMED`-`UNDELIVERED`-`DEFECTIVE`-`CHALLAN`+`PURCHASE` AS `EFFECTIVE STOCK`
		  FROM (
		    SELECT
		        OUTSTK.NAME,
			OUTSTK.ITEM_GROUP,
			OUTSTK.BRAND,
		        IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		          ITEM_CODE=OUTSTK.NAME {open_condition}),0) AS `OPENING STOCK`,
		        IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		          ITEM_CODE=OUTSTK.NAME AND ACTUAL_QTY > 0 {condition}),0) AS `IN QTY`,
		        IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
		          ITEM_CODE=OUTSTK.NAME AND ACTUAL_QTY < 0 {condition}),0) AS `OUT QTY`,
		        IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabSales Invoice` INV, `tabSales Invoice Item` INV_ITEM WHERE
		        INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=OUTSTK.NAME {inv_condition}),0) AS `UNCONFIRMED`,
		        IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Invoice` INV,
		          `tabSales Invoice Item` INV_ITEM WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND
		          INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV.UPDATE_STOCK=0 AND INV_ITEM.ITEM_CODE=OUTSTK.NAME {inv_condition}),0) AS `UNDELIVERED`,
            	IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabDelivery Note` INV, `tabDelivery Note Item` INV_ITEM WHERE
                  INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<2 AND INV_ITEM.ITEM_CODE=OUTSTK.NAME  {inv_condition}),0) AS `CHALLAN`,
            	IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabPurchase Invoice` INV, `tabPurchase Invoice Item` INV_ITEM WHERE
                  INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=OUTSTK.NAME  {inv_condition}),0) AS `PURCHASE`,				  
		        IFNULL((SELECT COUNT(*) FROM `tabStock Problem` PROB WHERE PROB.item=OUTSTK.NAME AND PROB.STATUS='Open'),0) AS `DEFECTIVE`
		    FROM
		      `tabItem` OUTSTK
		    WHERE
		      OUTSTK.IS_STOCK_ITEM=1 {global_condition}
		    ) DER GROUP BY NAME
		""".format(**{
			"condition":get_conditions(filters),
			"open_condition":get_open_conditions(filters),
			"global_condition":get_global_condition(filters),
			"inv_condition":get_conditions_for_invoice(filters)
		})
	return frappe.db.sql(query, as_list=1)
