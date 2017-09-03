// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Custom Salary Register"] = {
	"filters": [
		{
			"fieldname":"date_range",
			"label": __("Date Range"),
			"fieldtype": "DateRange",
			"default": [frappe.datetime.add_months(frappe.datetime.get_today(),-1), frappe.datetime.get_today()],
			"reqd": 1
		}
	],
	onload: function(report) {
		report.page.add_inner_button(__("Process Staff Salaries Journal Entries"), function() {
			var filters = report.get_values();
			process_salary_jv(filters, 0);
		}, __('Process Entries'));
		/*report.page.add_inner_button(__("Process Director Salaries Journal Entries"), function() {
			var filters = report.get_values();
			process_salary_jv(filters, 1);
		}, __('Process Entries'));*/
	}
}

process_salary_jv = function(filters, is_director) {
			var dialog = new frappe.ui.Dialog({
				title: "Process Journal Entries",
				fields: [
					{"fieldtype": "Date", "label": __("Date"), "fieldname": "date","reqd": 1 },
					{"fieldtype": "Link",
					 "label": __("Salary Payable Account"),
					 "fieldname":"payable_account",
					 "options":"Account",
					 "reqd": 1}
				]
			});

			 dialog.set_primary_action(__("Save"), function() {
				args = dialog.get_values();
				if(!args) return;
				return frappe.call({
					method: "mapl_customization.customizations_for_mapl.process_salary.process_staff_salaries_jv",
					args: {
					 "payable_account":args.payable_account,
					 "date":args.date,
					 "filters": filters,
					 "director": is_director
					},
					callback: function(r) {
						if(r.exc) {
							msgprint(__("There were errors."));
							return;
						}
						dialog.hide();
					},
					btn: this
				});
			});
			dialog.show();
};
