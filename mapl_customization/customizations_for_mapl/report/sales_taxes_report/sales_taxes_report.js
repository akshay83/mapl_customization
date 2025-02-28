// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.query_reports["Sales Taxes Report"] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": "From Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "to_date",
			"label": "To Date",
			"fieldtype": "Date",
			"default": frappe.datetime.get_today()
		},
		{
			"fieldname": "company",
			"label": "Company",
			"options": "Company",
			"fieldtype": "Link",
			"default": frappe.defaults.get_user_default("Company")
		},
		{
			"fieldname": "document_type",
			"label": "Report Type",
			"options": "Sales Detailed\nPurchase Detailed\nPurchase Summary",
			"fieldtype": "Select",
			"default": "Purchase Summary",
			"on_change": function() {
				let document_type_value = frappe.query_report.get_filter_value('document_type');
				ztf = frappe.query_report.get_filter("include_zero_tax");
				if(document_type_value != "Purchase Detailed") {
					frappe.query_report.set_filter_value('include_zero_tax','0');
					ztf.toggle(false);
					return;
				} else {
					ztf.toggle(true);
				}
				ztf.refresh();
			}
		},
		{
			"fieldname": "include_zero_tax",
			"label": "Include Zero Tax Items",
			"fieldtype": "Check",
			"default": "0",
			"hidden": 1
		},
		{
			"fieldname": "include_stock_columns",
			"label": "Include Stock Columns",
			"fieldtype": "Check",
			"default": "0"
		}
	]
}
