frappe.ui.form.on("Payment Entry", "refresh", function(frm) {
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('width','200px');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('width','200px');
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('height','50px');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('height','50px');
	$('.btn.btn-default.btn-xs:contains("Receipts")').css('font-weight','800');
	$('.btn.btn-default.btn-xs:contains("Payments")').css('font-weight','800');
	$('.btn.btn-default.btn-xs:contains("Payments")').parent().css('text-align','center');
	$('.btn.btn-default.btn-xs:contains("Receipts")').parent().css('text-align','center');
	$('.input-with-feedback.form-control.bold[data-fieldname="paid_amount"]').css({'background':'lightblue','border':'none'})
});
frappe.ui.form.on("Payment Entry", "onload_post_render", function(frm) {
	if (frm.doc.__islocal && !frm.doc.paid_amount) {
		cur_frm.fields_dict.type_of_payment.wrapper.hide();
	}

	if ($.find('.btn.btn-sm.btn-default:contains("Add Party")').length <= 0) {
		var add_btn = $('<button class="btn btn-sm btn-default">Add Party</button>').appendTo($("<div>")
				.css({
					"margin-bottom": "10px",
					"margin-top": "10px"
				}).appendTo(cur_frm.fields_dict.party.$wrapper));

		add_btn.on("click", function() {
			if (frm.doc.party_type == "Customer") {
				custom.customer_quick_entry.set_called_from("party");
				custom.customer_quick_entry(cur_frm);
			}
		});
	}

	frm.set_query("party", function(doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.select_customer_supplier_query",
			filters: {'party_type':doc.party_type }
		}
	});
	frm.set_query("party_address", function(doc) {
		if (doc.party_type=="Customer") {
			return {
				query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: {'customer':doc.party}
			}
		} else {
			return {
				query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: {'supplier':doc.party}
			}
		}
	});
	frm.set_query("special_payment", function(doc) {
		return {
			filters: {
				'app_payment': 0
			}
		}
	});
});

frappe.ui.form.on("Payment Entry", "party", function(frm) {
	if(frm.doc.party_type && frm.doc.party) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_name",
			args: {
				party_type: frm.doc.party_type,
				party: frm.doc.party
			},
			callback: function(r) {
				if(!r.exc && r.message) {
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
			callback: function(r) {
				if(r.message)
					frm.set_value("party_address", r.message);
				else
					frm.set_value("party_address", null);
			}
        	});
		custom._get_party_balance_formatted(frm.doc.party_type, frm.doc.party,
				frm.doc.company, function(result) {
					show_alert(result,8);
		});
	}
});

frappe.ui.form.on("Payment Entry", "party_address", function(frm) {
	if (frm.doc.party_address) {
		frm.call({
			method: "mapl_customization.customizations_for_mapl.utils.fetch_address_details_payments_receipts",
			args: {
				party_address: frm.doc.party_address
			},
			callback: function(r) {
				if(r.message)
					frm.set_value("address", r.message);
			}
		});
	} else {
		frm.set_value("address", null);
	}
});
//cur_frm.fields_dict['party_address'].get_query = function(doc, cdt, cdn) {
//	if (doc.party_type=="Customer") {
//		return {
//			filters:{'customer': doc.party}
//		}
//	} else {
//		return {
//			filters:{'supplier': doc.party}
//		}
//	}
//};

frappe.ui.form.on("Payment Entry", "payments", function(frm) {
	frm.set_value('payment_type','Pay');
	frm.fields_dict.type_of_payment.wrapper.show();
});

frappe.ui.form.on("Payment Entry", "receipts", function(frm) {
	frm.set_value('payment_type','Receive');
	frm.fields_dict.type_of_payment.wrapper.show();
});

frappe.ui.form.on("Payment Entry", "validate", function(frm) {
	frm.doc.references.forEach(function(val, i) {
		if (val.allocated_amount < 0) {
			frappe.msgprint("Check Allocated Amount in Row No " + (i+1));
			frappe.validated = false;
		}
	});
});