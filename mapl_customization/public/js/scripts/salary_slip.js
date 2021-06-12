cur_frm.add_fetch('employee', 'bank_branch', 'bank_branch');
cur_frm.add_fetch('employee', 'ifsc_code', 'ifsc_code');

frappe.ui.form.on("Salary Slip", "calculate_actual_salary", function(frm) {
	cur_frm.doc.calculated_payment_days = Math.round(cur_frm.doc.payment_days * cur_frm.doc.actual_salary / cur_frm.doc.reporting_salary);
	cur_frm.refresh_field("calculated_payment_days");
});

frappe.ui.form.on("Salary Slip","end_date", function(frm) {
	if (frm.doc.start_date) {
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
						console.log(val);
						frm.doc.actual_salary = val.actual_salary;
						frm.doc.reporting_salary = value.reported_salary;
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
});
