// Copyright (c) 2017, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.ui.form.on("Adjustments Set Off Tool", "fetch_details", function (frm) {
	frm.clear_table("adjustment_detail");
	frappe.call({
		method: "mapl_customization.customizations_for_mapl.doctype.adjustments_set_off_tool.adjustments_set_off_tool.fetch_details",
		args: {
			"filters": frm.doc
		},
		callback: function (r) {
			if (r.message) {
				$.each(r.message, function (i, d) {
					var c = frm.add_child("adjustment_detail");
					c.customer_name = d.customer_name;
					c.customer = d.party;
					c.total_debit = d["Total Debit"];
					c.total_credit = d["Total Credit"];
					c.difference_amount = d.Difference;
					c.difference_percent = d.Percentage;
				});
				frm.refresh_field("adjustment_detail");
				frappe.msgprint(__("Success"));
			}
		}
	});
});
frappe.ui.form.on("Adjustments Set Off Tool", "refresh", function (frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Make Journal Entries'), function () {
			if (cur_frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.doctype.adjustments_set_off_tool.adjustments_set_off_tool.make_jv",
				args: {
					"doc_name": frm.doc.name
				},
				callback: function (r) {
					if (!r.exc) {
						frappe.msgprint(__("Success"));
						frm.reload_doc();
					}
				}
			});
		});
	}
});