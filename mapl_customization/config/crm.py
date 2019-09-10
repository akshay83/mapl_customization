from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Custom Reports"),
			"items" : [
				{
					"doctype": "Lead",
					"type" : "report",
					"name" : "Lead Report",
					"is_query_report" : True
				}
			]
		}
	       ]

