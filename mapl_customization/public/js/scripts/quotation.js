frappe.ui.form.on("Quotation", "refresh", function(frm) {
	if (frm.doc.__islocal) {
		frm.set_value('tc_name','Quotation Terms & Conditions');
		frm.set_value('valid_till', frappe.datetime.add_days(frappe.datetime.nowdate(), 15));
	}
});

frappe.ui.form.on("Quotation", "taxes_and_charges", function(frm) {
	setTimeout(function() { custom_set_tax_rate_type(frm) } , 2000);
});

frappe.ui.form.on("Quotation", "is_inclusive_of_taxes", function(frm) {
	custom_set_tax_rate_type(frm);
});

frappe.ui.form.on("Quotation", "validate", function(frm) {
	custom_set_tax_rate_type(frm);
});

function custom_set_tax_rate_type(frm) {
	$.each(frm.doc.taxes || [], function(i, v) {
		if (v.charge_type.toLowerCase()!="actual") {
			frappe.model.set_value(v.doctype, v.name, "included_in_print_rate", frm.doc.is_inclusive_of_taxes);
		}
	})
	frm.refresh();
};

function custom_toggle_bank(frm) {
	frm.set_df_property("bank", "reqd", frm.doc.show_bank_details == 1);
	frm.refresh_field("bank");
}

frappe.ui.form.on("Quotation", "onload_post_render", function (frm) {
	frm.set_query("party_name", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
		}
	});
	frm.set_query("customer_address", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
			filters: { 'customer': doc.party_name }
		}
	});
	frm.set_query("shipping_address_name", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
			filters: { 'customer': doc.party_name }
		}
	});
	custom_toggle_bank(frm);
});

frappe.ui.form.on("Quotation", "show_bank_details", function (frm) {
	custom_toggle_bank(frm);
});

frappe.ui.form.on("Quotation", "customer_address", function (frm) {
	if (frm.doc.customer_address && !frm.doc.shipping_address_name) {
		frm.set_value("shipping_address_name", frm.doc.customer_address);
		frm.refresh_field('shipping_address_name');
	}
});
frappe.ui.form.on("Quotation", "shipping_address_name", function (frm) {
	if (!frm.doc.shipping_address_name) {
		frm.set_value("shipping_address", null);
	}
});