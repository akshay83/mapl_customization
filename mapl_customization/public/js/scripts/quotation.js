frappe.ui.form.on("Quotation", "refresh", function(frm) {
	if (frm.doc.__islocal) {
		cur_frm.set_value('tc_name','Quotation Terms & Conditions');
		cur_frm.set_value('valid_till', frappe.datetime.add_days(frappe.datetime.nowdate(), 15));
	}
});
