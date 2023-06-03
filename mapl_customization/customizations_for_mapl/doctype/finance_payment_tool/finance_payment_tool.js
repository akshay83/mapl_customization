// Copyright (c) 2017, Akshay Mehta and contributors
// For license information, please see license.txt

cur_frm.set_query("internal_customer", "payment_details", function (doc, cdt, cdn) {
	return {
		query: "mapl_customization.customizations_for_mapl.queries.select_customer_supplier_query",
		filters: { 'party_type': 'Customer' }
	}
});
frappe.ui.form.on("Finance Payment Tool", "refresh", function (frm) {
	if (!frm.doc.__islocal && !frm.is_dirty()) {
		frm.add_custom_button(__('Fetch Customers'), function () {
			if (cur_frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.doctype.finance_payment_tool.finance_payment_tool.fetch_customers",
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
		frm.add_custom_button(__('Make Journal Entries'), function () {
			if (frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.doctype.finance_payment_tool.finance_payment_tool.make_jv",
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
frappe.ui.form.on("Finance Payment Details", "internal_customer", function (frm, dt, dn) {
	var grid_row = frm.open_grid_row();
	var p = grid_row.grid_form.fields_dict.internal_customer.get_value();

	if (p) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_name",
			args: {
				party_type: 'Customer',
				party: p
			},
			callback: function (r) {
				if (!r.exc && r.message) {
					grid_row.grid_form.fields_dict.internal_customer_name.set_value(r.message);
				}
			}
		});
		custom._get_party_balance_formatted('Customer', p,	frm.doc.company, function (result) {
				show_alert(result, 8);
		});
	}
});
