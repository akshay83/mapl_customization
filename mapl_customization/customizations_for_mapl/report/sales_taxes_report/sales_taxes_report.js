// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Taxes Report"] = {
	"filters": [
		{
		"fieldname":"from_date",
		"label": "From Date",
		"fieldtype": "Date",
		"default": frappe.datetime.get_today()
		},
		{
		"fieldname":"to_date",
		"label": "To Date",
		"fieldtype": "Date",
		"default": frappe.datetime.get_today()
		},
		{
		"fieldname":"company",
		"label": "Company",
		"options": "Company",
		"fieldtype": "Link",
		"default": frappe.defaults.get_user_default("Company")
		},
		{
		"fieldname":"document_type",
		"label": "Report Type",
		"options": "Sales\nPurchase",
		"fieldtype": "Select"
		},
	]
}
