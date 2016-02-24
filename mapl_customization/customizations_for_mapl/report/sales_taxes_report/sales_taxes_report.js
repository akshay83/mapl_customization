// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Taxes Report"] = {
	"filters": [
		{
		"fieldname":"fromdate",
		"label": "From Date",
		"fieldtype": "Date"
		},
		{
		"fieldname":"todate",
		"label": "To Date",
		"fieldtype": "Date"
		},
		{
		"fieldname":"company",
		"label": "Company",
		"options": "Company",
		"fieldtype": "Link",
		"default": frappe.defaults.get_user_default("Company")
		}
	]
}
