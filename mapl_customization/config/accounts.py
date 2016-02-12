from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Documents"),
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
		}
	       ]

