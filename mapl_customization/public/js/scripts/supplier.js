frappe.ui.form.on("Supplier","refresh", function(frm) {
	custom._get_party_balance_in_drcr('Supplier', frm.doc.name, frappe.defaults.get_user_default("company"), function(result) {
				frm.doc.current_balance=result;
				refresh_field("current_balance");
	});
});
