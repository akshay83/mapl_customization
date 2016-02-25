// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.query_reports["Monthly Stock Movement"] = {
	"filters": [
		{
		"fieldname":"company",
		"label":"Company",
		"options":"Company",
		"fieldtype":"Link",
		"default":frappe.defaults.get_user_default("Company")
		},
		{
		"fieldname":"fromdate",
		"fieldtype":"Date",
		"Label":"From Date",
		"width":"80",
		"default":sys_defaults.year_start_date
		},
		{
		"fieldname":"todate",
		"fieldtype":"Date",
		"width":"80",
		"label":"To Date",
		"default":frappe.datetime.get_today()
		},
		{
		"fieldname":"item_code",
		"label":"Item Code",
		"fieldtype":"Link",
		"width":"80",
		"options":"Item"
		},
		{
		"fieldname":"remove_material_transfer",
		"fieldtype":"Check",
		"label":"Remove Material Transfer",
		"default":"1"
		}
	]
}
