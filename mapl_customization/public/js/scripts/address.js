frappe.ui.form.on("Address","refresh", function(frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Update Address'), function() {
			if (cur_frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
			frappe.confirm("Please Be Aware That This Event Would Affect <B>All the Documents</B> in the System.\
					Advice You to Kindly Make a New Address for New Documents. Do You Want to Continue?", function() {
				frappe.call({
					method: "mapl_customization.customizations_for_mapl.update_address.update_address",
					args: {
						"address_name": frm.doc.name,
					},
					callback: function(r) {
						if(!r.exc) {
							frappe.msgprint(__("Address Updated Across All Relevant Documents"));
						}
					}
				});
			});
		}, 'Actions');
	}
});
