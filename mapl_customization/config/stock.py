from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Serial No and Batch"),
			"items" : [
				{
					"type" : "doctype",
					"name" : "Stock Problem",
					"description" : _("Tool to Keep a Track of Problems in Stock") 
				}
			]
		},
		{
			"label": _("Setup"),
			"items" : [
				{
					"type": "doctype",
					"name": "Item Taxes Template",
					"description": "Tax Template for Items"
				}
			]
		},
		{
			"label": _("Stock Reports"),
			"items" : [
				{
					"type": "report",
					"doctype": "Item",
					"name": "Monthly Stock Movement",
					"is_query_report": True,
					"description": "Shows a Month Wise Movement of a Particular Item"
				},
				{
					"type": "report",
					"doctype": "Stock Ledger Entry",
					"name": "Simple Stock Report",
					"is_query_report": True
				},
				{
					"type": "report",
					"doctype": "Item",
					"name": "Effective Stock Report",
					"is_query_report": True
				}
			]
		}
	       ]

