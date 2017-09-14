# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe import _
from frappe.utils import flt, getdate, cint

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
            "fieldname":"warehouse",
            "fieldtype":"Link",
            "label":"Warehouse",
	    "options":"Warehouse",
	    "width":150
        },
        {
            "fieldname":"item_group",
            "fieldtype":"Link",
            "label":"Item Group",
	    "options":"Item Group",
	    "width":150
        },
	{
	    "fieldname":"open_qty",
	    "fieldtype":"Float",
	    "label":"Opening Qty",
	    "width":150
	},
        {
            "fieldname":"in_qty",
            "fieldtype":"Float",
            "label":"In Qty",
	    "width":150
        },
        {
            "fieldname":"out_qty",
            "fieldtype":"Float",
            "label":"Out Qty",
	    "width":150
        },
        {
            "fieldname":"balance_qty",
            "fieldtype":"Float",
            "label":"Balance Qty",
	    "width":150
        }
	]

	return columns

def get_open_conditions(filters):
	conditions = ""

	if filters.get("warehouse"):
		conditions += " and warehouse = '%s'" % frappe.db.escape(filters.get("warehouse"), percent=False)

	if filters.get("from_date"):
		conditions += " and posting_date < '%s'" % frappe.db.escape(filters["from_date"])


	return conditions


def get_conditions(filters):
	conditions = ""


	if filters.get("from_date"):
		conditions += " and posting_date > '%s'" % frappe.db.escape(filters["from_date"])


	if filters.get("to_date"):
		conditions += " and posting_date <= '%s'" % frappe.db.escape(filters["to_date"])

	if filters.get("item_code"):
		conditions += " and item_code = '%s'" % frappe.db.escape(filters.get("item_code"), percent=False)


	if filters.get("warehouse"):
		conditions += " and warehouse = '%s'" % frappe.db.escape(filters.get("warehouse"), percent=False)

	if filters.get("remove_material_transfer"):
		conditions += """ and if(voucher_type='Stock Entry',
			(select purpose from `tabStock Entry` se where se.name=voucher_no) 
			not like '%%Transfer%%', True)"""


	return conditions

#unsused for now
def build_for_material_transfer(filters,conditions):
	if filters.get("remove_material_transfer"):
		conditions += """ and if (voucher_type='Stock Entry',
			(select purpose from `tabStock Entry` where name=Stk.voucher_no)
			not like '%%Transfer%%', True)"""

	return conditions

def get_global_condition(filters):
	global_condition = ""
	if filters.get("brand"):
		global_condition += """ and item.brand = '{brand}' """.format(**{
			"brand":filters.get("brand")
			})

	if filters.get("item_code"):
		global_condition += " and OUTSTK.item_code = '%s'" % frappe.db.escape(filters.get("item_code"), percent=False)


	return global_condition


def get_data(filters):

	query = ""
	if filters.get("group_by_warehouse") and cint(filters.get("group_by_warehouse")):
		query = """SELECT *,`OPENING STOCK`+`IN QTY`-`OUT QTY` AS `CLOSING STOCK` FROM (
			SELECT OUTSTK.ITEM_CODE,OUTSTK.WAREHOUSE, item.ITEM_GROUP, IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE AND WAREHOUSE=OUTSTK.WAREHOUSE {open_condition}),0) AS `OPENING STOCK`,
			IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE AND WAREHOUSE=OUTSTK.WAREHOUSE AND ACTUAL_QTY > 0 {condition}),0) AS `IN QTY`,
			IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE AND WAREHOUSE=OUTSTK.WAREHOUSE AND ACTUAL_QTY < 0 {condition}),0) AS `OUT QTY`
			FROM `tabStock Ledger Entry` OUTSTK,`tabItem` item where item.item_code=OUTSTK.item_code {global_condition}
			group by OUTSTK.item_code, OUTSTK.WAREHOUSE order by OUTSTK.item_code,OUTSTK.WAREHOUSE) DER """.format(**{
				"condition":get_conditions(filters),
				"open_condition":get_open_conditions(filters),
				"global_condition":get_global_condition(filters)
			})
	else:
		query = """SELECT *,`OPENING STOCK`+`IN QTY`-`OUT QTY` AS `CLOSING STOCK` FROM (
			SELECT OUTSTK.ITEM_CODE,null as `warehouse`, item.ITEM_GROUP, IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE {open_condition}),0) AS `OPENING STOCK`,
			IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE AND ACTUAL_QTY > 0 {condition}),0) AS `IN QTY`,
			IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
			ITEM_CODE=OUTSTK.ITEM_CODE AND ACTUAL_QTY < 0 {condition}),0) AS `OUT QTY`
			FROM `tabStock Ledger Entry` OUTSTK,`tabItem` item where item.item_code=OUTSTK.item_code {global_condition}
			group by OUTSTK.item_code order by OUTSTK.item_code) DER """.format(**{
				"condition":get_conditions(filters),
				"open_condition":get_open_conditions(filters),
				"global_condition":get_global_condition(filters)
			})


	return frappe.db.sql(query, as_list=1)
