from __future__ import unicode_literals
from frappe import _

def get_data():
	return [
		{
			"label" : _("Documents"),
			"items" : [
				{
					"type" : "doctype",
					"name" : "Stock Problem",
					"description" : _("Tool to Keep a Track of Problems in Stock") 
				}
			]
		}
	       ]

