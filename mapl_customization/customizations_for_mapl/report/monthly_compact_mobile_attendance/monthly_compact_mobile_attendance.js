// Copyright (c) 2026, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Monthly Compact Mobile Attendance"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"branch",
			"label": __("Branch"),
			"fieldtype": "Link",
			"options": "Branch"
		},		
		{
			"fieldname":"employee",
			"label": __("Employee"),
			"fieldtype": "Link",
			"options": "Employee",
			"on_change": function() {
				let employee = frappe.query_report.get_filter_value('employee');
				if(!employee) {
					frappe.query_report.set_filter_value('employee_name','');
					return;
				}
				frappe.db.get_value("Employee", employee, "employee_name", function(value) {
					frappe.query_report.set_filter_value('employee_name',value["employee_name"]);
				});
			},
		},
		{
			"fieldname":"employee_name",
			"label": __("Employee Name"),
			"fieldtype": "Data",
			"read_only": 1
		}		
	]
};

