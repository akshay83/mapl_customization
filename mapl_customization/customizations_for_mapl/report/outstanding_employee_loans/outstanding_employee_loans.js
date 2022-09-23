// Copyright (c) 2022, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Outstanding Employee Loans"] = {
	"filters": [
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
