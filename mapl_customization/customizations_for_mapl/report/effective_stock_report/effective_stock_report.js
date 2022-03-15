// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.query_reports["Effective Stock Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"width": "100",
			"default": frappe.sys_defaults.year_start_date
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"width": "100"
		},
		{
			"fieldname": "item_code",
			"label": __("Item Code"),
			"fieldtype": "Link",
			"options": "Item",
			"width": "200"
		},
		{
			"fieldname": "brand",
			"label": "Brand",
			"fieldtype": "Link",
			"options": "Brand",
			"width": "100"
		},
		{
			"fieldname": "warehouse",
			"label": __("Warehouse"),
			"fieldtype": "Link",
			"options": "Warehouse",
			"width": "150"
		}
	]
}
