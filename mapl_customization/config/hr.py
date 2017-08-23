from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Customized Reports"),
			"items" : [
				{
					"type" : "report",
					"name" : "Custom Salary Register",
					"doctype" : "Salary Slip",
					"is_query_report" : True
				}
			]
		}
	       ]

