function custom_hide_sections(frm, hide) {
	if (hide) {
		frm.fields_dict.type_of_payment.wrapper.hide();
		frm.fields_dict.party_section.wrapper.hide();
		frm.fields_dict.payment_accounts_section.wrapper.hide();
		frm.fields_dict.accounting_dimensions_section.wrapper.hide();
		frm.fields_dict.finance.wrapper.hide();
	} else {
		frm.fields_dict.type_of_payment.wrapper.show();
		frm.fields_dict.party_section.wrapper.show();
		frm.fields_dict.payment_accounts_section.wrapper.show();
		frm.fields_dict.accounting_dimensions_section.wrapper.show();
		frm.fields_dict.finance.wrapper.show();
	}
};
function custom_hide_or_show_cashback_fields(frm, show) {
	let fields = ["base_amount", "cash_back_amount", "instant_cash_back_provider"];
	for (let f in fields) {
		frm.set_df_property(fields[f], "hidden", !show);
		frm.set_df_property(fields[f], "reqd", show);
		frm.refresh_field(fields[f]);
	}
};
frappe.ui.form.on("Payment Entry", "refresh", function (frm) {
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('width', '200px');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('width', '200px');
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('height', '50px');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('height', '50px');
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('font-weight', '800');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('font-weight', '800');
	$('.btn.btn-default.btn-xs:contains("Payments")').parent().css('text-align', 'center');
	$('.btn.btn-default.btn-xs:contains("Receipts")').parent().css('text-align', 'center');
	$('.input-with-feedback.form-control.bold[data-fieldname="paid_amount"]').css({ 'background': 'lightblue', 'border': 'none' })
	if (frm.doc.__islocal === undefined || !frm.doc.__islocal) {
		frm.fields_dict.payment_type_section.wrapper.hide();
	} else {
		frm.fields_dict.payment_type_section.wrapper.show();
		frm.set_df_property("special_payment", "reqd", 0);
		frm.set_df_property("special_payment", "hidden", 1);
		frm.refresh_field("special_payment");
		custom_hide_or_show_cashback_fields(frm, false);
	}
	custom.hide_print_button("Payment Entry", frm);
});
frappe.ui.form.on("Payment Entry", "mode_of_payment", function (frm) {
	if (frm.doc.mode_of_payment !== undefined && frm.doc.mode_of_payment != '') {
		frappe.db.get_value("Mode of Payment", frm.doc.mode_of_payment, "base_mode", function (val) {
			if (val.base_mode.toLowerCase() == "card") {
				frm.set_df_property("special_payment", "reqd", 1);
				frm.set_df_property("special_payment", "hidden", 0);
			} else {
				custom_hide_or_show_cashback_fields(frm, false);
				frm.set_df_property("special_payment", "reqd", 0);
				frm.set_df_property("special_payment", "hidden", 1);
				frm.set_value("special_payment", "");
				frm.fields_dict.party_section.wrapper.show();
			}
			frm.refresh_field("special_payment");
		});
	}
});
frappe.ui.form.on("Payment Entry", "special_payment", function (frm) {
	if (frm.doc.special_payment !== undefined && frm.doc.special_payment != '') {
		if (frm.doc.special_payment.toLowerCase().includes("cash back")) {
			custom_hide_or_show_cashback_fields(frm, true);
		} else {
			custom_hide_or_show_cashback_fields(frm, false);
			frm.fields_dict.party_section.wrapper.show();
		}
	}
});
frappe.ui.form.on("Payment Entry", "cash_back_amount", function (frm) {
	if (frm.doc.cash_back_amount !== undefined && frm.doc.cash_back_amount != '') {
		if (frm.doc.base_amount - frm.doc.cash_back_amount < 0) {
			frappe.msgprint("Check Base Amount");
		} else {
			frm.set_value("paid_amount", (frm.doc.base_amount - frm.doc.cash_back_amount));
			frm.set_value("received_amount", (frm.doc.base_amount - frm.doc.cash_back_amount));
			frm.refresh_field("paid_amount");
			frm.refresh_field("received_amount");
			frm.fields_dict.party_section.wrapper.show();	
		}	
	}
});
frappe.ui.form.on("Payment Entry", "onload_post_render", function (frm) {
	frm.fields_dict.gst_section.wrapper.hide();
	if (frm.doc.__islocal && !frm.doc.paid_amount) {
		custom_hide_sections(frm, true);
	} else {
		custom_hide_sections(frm, false);
	}

	if ($.find('.btn.btn-sm.btn-default:contains("Add Party")').length <= 0) {
		var add_btn = $('<button class="btn btn-sm btn-default">Add Party</button>').appendTo($("<div>")
			.css({
				"margin-bottom": "10px",
				"margin-top": "10px"
			}).appendTo(frm.fields_dict.party.$wrapper));

		add_btn.on("click", function () {
			if (frm.doc.party_type == "Customer") {
				custom.customer_quick_entry.set_called_from("party");
				custom.customer_quick_entry(frm);
			}
		});
	}
	frm.set_query("party_address", function (doc) {
		if (doc.party_type == "Customer") {
			return {
				query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: { 'customer': doc.party }
			}
		} else {
			return {
				query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: { 'supplier': doc.party }
			}
		}
	});
	frm.set_query("special_payment", function (doc) {
		return {
			filters: {
				'app_payment': 0
			}
		}
	});
});
frappe.ui.form.on("Payment Entry", "party_type", function (frm) {
	frm.set_query("party", function (doc) {
		if (frm.doc.party_type == 'Customer') {
			return {
				query: "mapl_customization.customizations_for_mapl.queries.select_customer_supplier_query",
				filters: { 'party_type': doc.party_type }
			}
		}
	});
});
frappe.ui.form.on("Payment Entry", "party", function (frm) {
	if (frm.doc.party_type && frm.doc.party) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_name",
			args: {
				party_type: frm.doc.party_type,
				party: frm.doc.party
			},
			callback: function (r) {
				if (!r.exc && r.message) {
					frm.set_value("party_name", r.message);
				}
			}
		});

		frm.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_primary_billing_address",
			args: {
				party_type: frm.doc.party_type,
				party: frm.doc.party
			},
			callback: function (r) {
				if (r.message)
					frm.set_value("party_address", r.message);
				else
					frm.set_value("party_address", null);
			}
		});
		custom._get_party_balance_formatted(frm.doc.party_type, frm.doc.party,
			frm.doc.company, function (result) {
				show_alert(result, 8);
			});
		frm.fields_dict.payment_accounts_section.wrapper.show();
		frm.fields_dict.accounting_dimensions_section.wrapper.show();
		frm.fields_dict.finance.wrapper.show();
	}
});

frappe.ui.form.on("Payment Entry", "party_address", function (frm) {
	if (frm.doc.party_address) {
		frm.call({
			method: "mapl_customization.customizations_for_mapl.utils.fetch_address_details_payments_receipts",
			args: {
				party_address: frm.doc.party_address
			},
			callback: function (r) {
				if (r.message)
					frm.set_value("address", r.message);
			}
		});
	} else {
		frm.set_value("address", null);
	}
});

frappe.ui.form.on("Payment Entry", "*", function (frm) {
	custom.hide_print_button("Payment Entry", frm);
});

frappe.ui.form.on("Payment Entry", "onload", function (frm) {
	//--DEBUG--console.log("Called Onload Event");
	custom.hide_print_button("Payment Entry", frm);
});

frappe.ui.form.on("Payment Entry", "payments", function (frm) {
	frm.set_value('payment_type', 'Pay');
	frm.fields_dict.type_of_payment.wrapper.show();
});

frappe.ui.form.on("Payment Entry", "receipts", function (frm) {
	frm.set_value('payment_type', 'Receive');
	frm.fields_dict.type_of_payment.wrapper.show();
});

frappe.ui.form.on("Payment Entry", "validate", function (frm) {
	frm.doc.references.forEach(function (val, i) {
		if (val.allocated_amount < 0) {
			frappe.msgprint("Check Allocated Amount in Row No " + (i + 1));
			frappe.validated = false;
		}
	});
});
