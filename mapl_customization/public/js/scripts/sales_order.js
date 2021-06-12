cur_frm.add_fetch('item_code','is_vehicle','is_vehicle');
frappe.ui.form.on("Sales Order", "is_finance", function (frm) {
	frm.set_df_property("hypothecation", "reqd", frm.doc.is_finance==1);
	frm.refresh_field("hypothecation");
});
frappe.ui.form.on("Sales Order", "customer", function (frm) {
	frm.set_df_property("customer_name", "hidden", false);
	if (frm.doc.customer) {
		custom._get_party_balance_formatted('Customer', frm.doc.customer, frm.doc.company, function(result) {
			show_alert(result,8);
		});
	}
});
frappe.ui.form.on("Sales Order","onload_post_render", function(frm) {
	frm.set_query("customer", function(doc) {
		return{
			query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
		}
	});
	frm.set_query("shipping_address_name", function(doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
			filters: {'customer':doc.customer}
		}
	});
});
frappe.ui.form.on("Sales Order", "items_on_form_rendered", function(frm) {
	// Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
	// The button in child form
	var grid_row = cur_frm.open_grid_row();

	// Add Button to Child Form ... Wrap it around the "dialog_result" field
	var $btn = $('<button class="btn btn-sm btn-default">' + __("Current Stock") + '</button>')
		.appendTo($("<div>").css({
			"margin-bottom": "10px",
			"margin-top": "10px"
		 }).appendTo(grid_row.grid_form.fields_dict.item_code.$wrapper));

	// Bind a Event to Added Button
	$btn.on("click", function() {
		if (grid_row.grid_form.fields_dict.item_code.value) {
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.utils.get_effective_stock_at_all_warehouse",
				args: {
					"item_code": grid_row.grid_form.fields_dict.item_code.value,
					"date": cur_frm.doc.transaction_date
				},
				callback: function(r) {
					if (r.message) {
						custom.show_stock_dialog(r.message);
					}
				}
			});
		}
	});
});

frappe.ui.form.on('Sales Order', 'customer' , function(frm) {
	if(frm.doc.customer) {
		frm.set_party_account_based_on_party = true;
		return frappe.call({
			method: "erpnext.accounts.doctype.payment_entry.payment_entry.get_party_details",
			args: {
				company: frm.doc.company,
				party_type: 'Customer',
				party: frm.doc.customer,
				date: frm.doc.transaction_date
			},
			callback: function(r, rt) {
				if(r.message) {
					frm.set_value("customer_account", r.message.party_account);
				}
			}
		});
	}
});

frappe.ui.form.on('Sales Order Payment', 'mode_of_payment', function(frm, cdt, cdn) {
	var d = locals[cdt][cdn];
	if (!d.mode_of_payment) {
		return;
	}
	frappe.call({
		method: "erpnext.accounts.doctype.sales_invoice.sales_invoice.get_bank_cash_account",
		args: {
			"mode_of_payment": d.mode_of_payment,
			"company": frm.doc.company
		},
		callback: function(r, rt) {
			if(r.message) {
				frappe.model.set_value(cdt, cdn, 'account', r.message.account);
			}
		}
	});
});
