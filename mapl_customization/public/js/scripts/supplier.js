frappe.ui.form.on("Supplier","refresh", function(frm) {
	custom._get_party_balance_in_drcr('Supplier', frm.doc.name, frappe.defaults.get_user_default("company"), function(result) {
				frm.doc.current_balance=result;
				refresh_field("current_balance");
	});
});

frappe.ui.form.on("Supplier", "onload_post_render", function (frm) {
	frm.set_query("party_type", "connected_accounts_list", function (doc, cdt, cdn) {
		const row = locals[cdt][cdn];
		return {
			query: "erpnext.setup.doctype.party_type.party_type.get_party_type",
			filters: {
				'account': row.account
			}
		}
	});
});

frappe.ui.form.on("Connected Account", "party", function (frm, cdt, cdn) {
	custom.fetch_details_connected_accounts(frm, cdt, cdn);
});
