# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
import calendar
from frappe import _
from frappe.utils import flt, getdate
from datetime import datetime
from dateutil import relativedelta

def execute(filters=None):
	if not filters: filters = {}

	if not validate(filters):
		return [],[]

	columns = get_columns(filters)

	data = get_data(filters)

	return columns, data

def validate(filters):
	if (not filters.get("fromdate")):
		frappe.throw("From Date Cannot Be Empty")

	if (not filters.get("todate")):
		frappe.throw("To Date Cannot Be Empty")

	if (not filters.get("item_code")):
		return False

	if (not filters.get("company")):
		return False

	return True

def get_columns(filters):
	"""return columns based on filters"""

	columns = [
        {
            "fieldname":"item",
            "fieldtype":"Data",
            "label":"Month",
	    "width":200
        },
        {
            "fieldname":"in_qty",
            "fieldtype":"Float",
            "label":"In Qty",
	    "width":80
        },
	{
	    "fieldname":"in_value",
	    "fieldtype":"Currency",
	    "label":"In Value",
	    "width":150
	},
        {
            "fieldname":"out_qty",
            "fieldtype":"Float",
            "label":"Out Qty",
	    "width":80
        },
	{
	    "fieldname":"out_value",
	    "fieldtype":"Currency",
	    "label":"Out Value",
	    "width":150
	},
        {
            "fieldname":"balance_qty",
            "fieldtype":"Float",
            "label":"Balance Qty",
	    "width":80
        },
	{
	    "fieldname":"balance_value",
	    "fieldtype":"Currency",
	    "label":"Balance Value",
	    "width":150
	}
	]

	return columns

def get_conditions(filters,with_to_date=False):
	conditions = ""

	if filters.get("to_date") and with_to_date:
		conditions += " and posting_date <= '%s'" % frappe.db.escape(filters["to_date"])

	if filters.get("item_code"):
		conditions += " and item_code = '%s'" % frappe.db.escape(filters.get("item_code"), percent=False)

	if filters.get("remove_material_transfer"):
		conditions += """ and if(entry.voucher_type='Stock Entry',
			(select purpose from `tabStock Entry` where name=entry.voucher_no) 
			not like '%%Transfer%%', True)"""

	return conditions


def get_opening_balance(filters):
	query = """select item_code, warehouse, sum(actual_qty) as opening_balance, sum(stock_value_difference) as opening_value
		from `tabStock Ledger Entry` as entry force index (posting_sort_index)
		where docstatus < 2 and posting_date < %(fromdate)s and company=%(company)s
        {condition} order by posting_date, posting_time, name""".format(**{
            "condition":get_conditions(filters)
        })

	return frappe.db.sql(query, {
		'company':filters.get("company",""),
		'fromdate':str(filters.get("fromdate",""))
		},as_dict=True)

def get_current_items(filters):
	query = """select item_code, warehouse, posting_date, actual_qty, valuation_rate,
			company, voucher_type, qty_after_transaction, stock_value_difference
		from `tabStock Ledger Entry` as entry force index (posting_sort_index)
		where docstatus < 2 and company = %(company)s and posting_date>= %(fromdate)s
        {condition} order by posting_date, posting_time, name""".format(**{
            "condition":get_conditions(filters,with_to_date=True)
        })

	return frappe.db.sql(query, {
		'company':filters.get("company",""),
		'fromdate':str(filters.get("fromdate",""))
		}, as_dict=True)

def get_data(filters):
	data = []
	opening = get_opening_balance(filters)
	opening_balance = 0
	opening_value = 0
	for o in opening:
		if o.opening_balance:
			build_row = {}
			build_row["item"] = "Opening Balance"
			build_row["balance_qty"] = o.opening_balance
			build_row["balance_value"] = o.opening_value
			opening_balance = o.opening_balance
			opening_value = o.opening_value
			data.append(build_row)

	items = get_current_items(filters)

	previous_balance_qty = 0
	previous_balance_value = 0

	month_from_date = datetime.strptime(filters.get("fromdate"),"%Y-%m-%d").date()
	month_to_date = datetime.strptime(filters.get("todate"),"%Y-%m-%d").date()
	month_diff = relativedelta.relativedelta(month_to_date,month_from_date).months
	year_diff = relativedelta.relativedelta(month_to_date,month_from_date).years
	month_diff = month_diff + (year_diff*12)

	month_list = build_months(month_from_date.month,month_from_date.year,month_diff+1)
	index = 0

	for r in month_list:
		build_row = {
			"in_qty":0,
			"out_qty":0,
			"in_value":0,
			"out_value":0
			}
		build_row["item"] = r
		for i in items:
			if i.posting_date.strftime("%B").lower()+" "+str(i.posting_date.year)== \
					month_list[index].lower():
				build_row["in_qty"] += i.actual_qty if i.actual_qty > 0 else 0
				build_row["out_qty"] += abs(i.actual_qty) if i.actual_qty < 0 else 0
				build_row["in_value"] += i.stock_value_difference if i.stock_value_difference > 0 else 0
				build_row["out_value"] += abs(i.stock_value_difference) if i.stock_value_difference < 0 else 0

		if index==0:
			build_row["balance_qty"] = opening_balance+build_row["in_qty"]-build_row["out_qty"]
			build_row["balance_value"] = opening_value+build_row["in_value"]-build_row["out_value"]
		else:
			build_row["balance_qty"] = previous_balance_qty+build_row["in_qty"]-build_row["out_qty"]
			build_row["balance_value"] = previous_balance_value+build_row["in_value"]-build_row["out_value"]

		previous_balance_qty = build_row["balance_qty"]
		previous_balance_value = build_row["balance_value"]

		data.append(build_row)
		index = index + 1

	return data

def build_months(start_month, start_year, difference):
	month_dict = []
	for m in range(0, difference):
		month_dict.append(calendar.month_name[start_month]+" "+str(start_year))

		start_month = start_month + 1
		if start_month > 12:
			start_month = 1
			start_year = start_year + 1

	return month_dict
