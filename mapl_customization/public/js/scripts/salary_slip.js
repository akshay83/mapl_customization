cur_frm.add_fetch('employee', 'bank_branch', 'bank_branch');
cur_frm.add_fetch('employee', 'ifsc_code', 'ifsc_code');

frappe.ui.form.on("Salary Slip", "calculate_actual_salary", function(frm) {
	let calculation_dialog = new frappe.ui.Dialog({
			title: "Calculate Actual Salary",
			fields: [
				{
					label: "Actual Salary",
					fieldname: "actual_salary",
					fieldtype: "Currency"
				},
				{
					label: "Reporting Salary",
					fieldname: "reporting_salary",
					fieldtype: "Currency"
				},
				{
					label: "Actual Payment Days",
					fieldname: "actual_payment_days",
					fieldtype: "Int"
				},
				{
					label: "Reporting Payment Days",
					fieldname: "reporting_payment_days",
					fieldtype: "Int",
					read_only: 1
				},
				{
					label: "Calculate",
					fieldname: "calculate_button",
					fieldtype: "Button"
				}
			],
			primary_action_label: "Close",
			primary_action(values) {
				calculation_dialog.hide();
			}
	});

	console.log(calculation_dialog);
	calculation_dialog.fields_dict.calculate_button.$input.on("click", function (e) {
		calculation_dialog.set_value("reporting_payment_days",
			Math.round(calculation_dialog.get_value('actual_payment_days') * calculation_dialog.get_value('actual_salary') / calculation_dialog.get_value('reporting_salary')));
		calculation_dialog.refresh_fields(["reporting_payment_days"]);
	});

	calculation_dialog.set_value('actual_salary',frm.doc.actual_salary);
	calculation_dialog.set_value('reporting_salary',frm.doc.reporting_salary);
	calculation_dialog.show();
});

frappe.ui.form.on("Salary Slip","end_date", function(frm) {
	fetch_actual_reporting_salary(frm);
});

frappe.ui.form.on("Salary Slip","employee", function(frm) {
	fetch_actual_reporting_salary(frm);
});

frappe.ui.form.on("Salary Slip", "refresh", function (frm) {
	frappe.db.get_single_value("Payroll Settings", "gl_entry_on_salary_slip_submit").then((value) => {
		if (value === undefined || !value) return;
    	if (frm.doc.docstatus == 1) {
        		frm.add_custom_button(__('Accounting Ledger'), function () {
            		frappe.route_options = {
                		voucher_no: frm.doc.name,
                		from_date: frm.doc.posting_date,
                		to_date: moment(frm.doc.modified).format('YYYY-MM-DD'),
                		company: frm.doc.company,
                		group_by: "Group by Voucher (Consolidated)",
                		show_cancelled_entries: frm.doc.docstatus === 2
            		};
            		frappe.set_route("query-report", "General Ledger");
        		}, __("View"));		
    	}
	});
});

function fetch_actual_reporting_salary(frm) {
	if (frm.doc.salary_structure) {
		frappe.db.get_value("Salary Structure Assignment",
					{
						"salary_structure": frm.doc.salary_structure,
						"employee":frm.doc.employee,
						"docstatus":1
					},
					[	"reported_salary",
						"actual_salary",
						"no_pf_deduction"
					],function(val) {
						//--DEBUG--console.log(val);
						frm.doc.actual_salary = val.actual_salary;
						frm.doc.reporting_salary = val.reported_salary;
						if (val.no_pf_deduction != 0) {
				                        frm.set_df_property("reporting_salary", "hidden", 0);
							frm.set_df_property("actual_salary", "hidden", 0);
						} else {
							frm.set_df_property("reporting_salary", "hidden", 1);
							frm.set_df_property("actual_salary", "hidden", 1);
						}
						frm.refresh_field("actual_salary");
						frm.refresh_field("reporting_salary");
					}
		);
	}
}
