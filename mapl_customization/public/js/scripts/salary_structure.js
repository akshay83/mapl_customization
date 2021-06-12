//cur_frm.add_fetch('employee','no_pf_deduction','no_pf_deduction');

/*frappe.ui.form.on("Salary Structure Employee", "no_pf_deduction", function(frm, cdt, cdn) {
	console.log("No PF Deduction");
	console.log(frm);
	var grid_row = frm.open_grid_row();
	var item = null;
	if (!grid_row) {
		item = frappe.get_doc(cdt, cdn).no_pf_deduction;
	} else {
	    	item = grid_row.doc.no_pf_deduction;
	}
	frm.set_df_property("actual_salary", "reqd", item==1);
	frm.set_df_property("reporting_salary", "reqd", item==1);
	frm.refresh_field("actual_salary");
	frm.refresh_field("reporting_salary");
});*/
