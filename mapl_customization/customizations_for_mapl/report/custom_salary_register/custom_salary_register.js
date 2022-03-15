// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Custom Salary Register"] = {
	"filters": [
		{
			"fieldname": "date_range",
			"label": __("Date Range"),
			"fieldtype": "DateRange",
			"default": [frappe.datetime.add_months(frappe.datetime.get_today(), -1), frappe.datetime.get_today()],
			"reqd": 1
		},
		{
			"fieldname": "print_attendance",
			"label": __("Print Biometric Attendance"),
			"fieldtype": "Check",
			"default": 0
		}
	],
	onload: function (report) {
		report.page.add_inner_button(__("Process Staff Salaries Journal Entries"), function () {
			custom_process_salary_jv(report.get_values());
		}, __('Process Entries'));
	}
}

custom_process_salary_jv = function (filters) {
	let dialog = new frappe.ui.Dialog({
		title: "Process Journal Entries",
		fields: [
			{ "fieldtype": "Date", "label": __("Date"), "fieldname": "date", "reqd": 1 },
		]
	});

	dialog.set_primary_action(__("Save"), function () {
		args = dialog.get_values();
		if (!args) return;
		return frappe.call({
			method: "mapl_customization.customizations_for_mapl.process_salary.process_staff_salaries",
			args: {
				"date": args.date,
				"filters": filters
			},
			callback: function (r) {
				if (r.exc) {
					msgprint(__("There were errors."));
					return;
				}
				msgprint(__("Success"));
				dialog.hide();
			},
			btn: this
		});
	});
	dialog.show();
};
