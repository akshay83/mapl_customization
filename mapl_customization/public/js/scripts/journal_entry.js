frappe.ui.form.on("Journal Entry", "onload_post_render", function (frm) {
	frm.set_query("party", "accounts", function (doc, cdt, cdn) {
		let pt = frappe.get_doc(cdt, cdn).party_type;
		return {
			query: "mapl_customization.customizations_for_mapl.queries.select_customer_supplier_query",
			filters: { 'party_type': pt }
		}
	});
	frm.set_query("party_type", "accounts", function (doc, cdt, cdn) {
		return {
			query: "erpnext.setup.doctype.party_type.party_type.get_party_type"
		}
	});
});

frappe.ui.form.on("Journal Entry Account", "party", function (frm, dt, dn) {
	let grid_row = frm.open_grid_row();
	let party = null;
	let pt = null;
	let p = null;

	if (!grid_row) {
		party = frappe.get_doc(dt, dn);
		pt = party.party_type;
		p = party.party;
	} else {
		pt = grid_row.grid_form.fields_dict.party_type.get_value();
		p = grid_row.grid_form.fields_dict.party.get_value();
	}

	if (pt && p) {
		custom._get_party_balance_formatted(pt, p, frm.doc.company, function (result) {
			show_alert(result, 8);
		});

		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_name",
			args: {
				party_type: pt,
				party: p
			},
			callback: function (r) {
				if (!r.exc && r.message) {
					if (grid_row) {
						grid_row.grid_form.fields_dict.party_name.set_value(r.message);
					} else {
						party.party_name = r.message;
					}
					frm.refresh_field('accounts');
				}
			}
		});
	}
});
