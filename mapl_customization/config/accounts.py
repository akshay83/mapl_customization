from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label": _("Customized Reports"),
			"items": [
				{
					"type": "report",
					"doctype": "Sales Invoice",
					"is_query_report": True,
					"name": "Finance Outstanding",
					"description": "Shows Finance Outstanding"
				},
				{
					"type": "report",
					"doctype": "Sales Invoice",
					"is_query_report": True,
					"name": "Reference Outstanding",
					"description": "Shows Pending Payments for Referred Cases"
				},
				{
					"type":"report",
					"doctype": "Sales Invoice",
					"is_query_report":True,
					"name":"Sales Taxes Report",
					"description":"Generates a Report for Different Sales Taxes"
				},
				{
					"type":"report",
					"doctype": "Sales Invoice",
					"is_query_report":True,
					"name":"Simple Sales Report",
					"description":"Generates a Report for Sales"
				},
				{
					"type":"report",
					"doctype": "GL Entry",
					"is_query_report":True,
					"name":"Ledger Statement",
					"description":"Generates a Ledger Statement"
				},
				{
					"type":"report",
					"doctype": "Payment Entry",
					"is_query_report":True,
					"name":"Daily Collection Report",
					"description":"Generates a Daily Collection Report"
				},
				{
					"type": "report",
					"doctype": "GL Entry",
					"is_query_report": True,
					"name": "Cash Book",
					"description": "Display Daily Cash Register"
				}

			]
		},
		{
			"label": _("Banking and Payments"),
			"items": [
				{
					"type": "doctype",
					"name": "Finance Payment Tool",
				},
				{
					"type": "doctype",
					"name": "Adjustments Set Off Tool",
				},
				{
					"type": "doctype",
					"name": "Salary Payment Tool",
				}
			]
		}

	       ]

