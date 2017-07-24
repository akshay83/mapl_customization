from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Banking and Payments"),
			"items" : [
				{
					"type" : "doctype",
					"name" : "Receipts",
					"description" : _("Formal Receipts for Payments Received") 
				},
				{
					"type" : "doctype",
					"name" : "Payments",
					"description" : _("Tool to Make Payments.")
				}
			]
		},
		{
			"label": _("Standard Reports"),
			"items": [
				{
					"type": "report",
					"doctype": "Sales Invoice",
					"is_query_report": True,
					"name": "Finance Outstanding",
					"description": "Shows Finance Outstanding"
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
				}

			]
		}
	       ]

