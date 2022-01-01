frappe.ui.form.on("Address","refresh", function(frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Update Address'), function() {
			custom.update_address(frm);
		}, 'Actions');
	}
});
