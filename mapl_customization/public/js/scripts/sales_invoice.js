{% include "mapl_customization/customizations_for_mapl/einvoice/taxpro_einvoice.js" %}
erpnext.setup_einvoice_actions('Sales Invoice');

frappe.ui.form.on("Sales Invoice", "refresh", async function (frm) {
	let einvoice = await custom.einvoice_eligibility(frm.doc);
	let einvoice_made = !(frm.doc.irn === undefined || frm.doc.irn == null);
	//--DEBUG--console.log(einvoice);
	if (einvoice && !einvoice_made) {
		if (custom.is_workflow_active_on("Sales Invoice") && frm.doc.workflow_state != "Approved") return;
		frm.layout.show_message("Create an E-Invoice to Continue Printing","yellow");
	} 
	let negative_check = await custom.check_if_sales_invoice_will_result_in_negative_stock(frm.doc);
	if (negative_check.result) {
		frm.layout.show_message("On Submission, This Invoice will Result in Negative Stock. Check Item "+negative_check.item,"red");
		return;
	}
	let hsn_length_check = await custom.check_sales_invoice_hsn_length(frm.doc);
	if (hsn_length_check.result) {
		frm.layout.show_message("HSN Code Needs to be at least "+hsn_length_check.hsn_digits_failed+" Digits for Item "+hsn_length_check.item_code,"red");
		return;
	}
	if (frm.doc.docstatus == 0 && frm.doc.workflow_state === 'Pending' && frm.doc.delayed_payment === 1 
			&& ["other", "reference"].includes(frm.doc.delayed_payment_reason.toLowerCase())) {
				frm.layout.show_message("Reference Sale, Requires Approval","yellow");
	}
	if (frm.doc.__is_local==0 && frm.doc.docstatus <2 && frm.doc.address_display.includes("GSTIN") && frm.doc.gst_category.toUpperCase()=="UNREGISTERED") {
		frm.layout.show_message("GST Details Incorrect, please correct them to move Forward","red");
		return;
	}
	if (einvoice && !einvoice_made) return;
	if (frm.doc.docstatus == 0 && (frm.doc.ewaybill === undefined || frm.doc.ewaybill == null) && frm.doc.eway_bill_cancelled ==0) {
		frm.layout.show_message(`TIP: To Create EWAY Bill (<b>If Applicable</b>), First Check & Submit the Invoice. Then use E Invoice Button to Create an Eway Bill`,"blue");
	} 
});

frappe.ui.form.on("Sales Invoice", "before_cancel", function (frm) {
	if (frm.doc.irn && !frm.doc.irn_cancelled) {
		frappe.throw("IRN Created, Cannot Cancel");
	}
});

frappe.ui.form.on("Sales Invoice", "after_cancel", function (frm) {
	//--DEBUG--console.log("Check After Cancel");
	if (custom.is_workflow_active_on("Sales Invoice") && frm.doc.workflow_state !== 'Cancelled') {
		frappe.call({
			method: "unrestrict.unrestrict.update_workflow_on_cancel.update_workflow_state",
			args: {
				"doctype": "Sales Invoice",
				"docname": frm.doc.name,
				"value": "Cancelled"
			}
		});
	}
});

frappe.ui.form.on("Sales Invoice", "is_pos", function (frm) {
	console.log('is pos');
	if (frm.doc.is_pos == 1) {
		setTimeout(function () {
			frm.clear_table('payments');
			frm.refresh_field('payments');
		}, 2000);
	}
});

function custom_disable_save_button(frm) {
	//--DEBUG--console.log("Calling Disable Save");
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
	frm.enable_save();
	if (!frm.doc.__islocal && !frappe.user.has_role("System Manager") && frm.doc.docstatus != 0) {
		frm.disable_save();
	}
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
};

frappe.ui.form.on("Sales Invoice", "*", function (frm) {
	custom.hide_print_button("Sales Invoice", frm);
});

frappe.ui.form.on("Sales Invoice", "onload", function (frm) {
	//--DEBUG--console.log("Called Onload Event");
	custom.hide_print_button("Sales Invoice", frm);
	//DISABLED-VER13--custom_disable_save_button(frm);
	frappe.db.get_single_value("Global Defaults", "disable_rounded_total").then(val => {
		frm.doc.disable_rounded_total = val;
		frm.refresh_field('disable_rounded_total');
	});
});

//ADD MENU ITEM IN MENU DROPDOWN BUTTON
frappe.ui.form.on("Sales Invoice", "refresh", function (frm) {
	//TO FILL VOLATILE TYPE FIELD
	//if (frm.doc.customer!=null) {
	//    frappe.model.get_value("Customer",frm.doc.customer,"tax_id", function(value) {;
	//         frm.set_value("test_vat",value.tax_id);
	//    });
	//}

	//--DEBUG--console.log("Called Referesh Event");
	custom.hide_print_button("Sales Invoice", frm);
	//DISABLED-VER13--custom_disable_save_button(frm);
	$('.frappe-control.input-max-width[data-fieldname="grand_total"]').find('.control-value.like-disabled-input.bold').css('background', 'lightblue')
	$('div').find("[data-label='Fetch%20Timesheet']").hide();
	$('div').find("[data-label='Get%20Items%20From']").hide();

	if (frm.doc.tc_name === undefined || frm.doc.tc_name == null || frm.doc.tc_name == '') {
		frappe.db.get_value('Company', frappe.defaults.get_user_default("Company"), "default_selling_terms", function (val) {
			frm.set_value("tc_name", val.default_selling_terms);
			frm.refresh_field("tc_name");
			frappe.db.get_value("Terms and Conditions", val.default_selling_terms, "terms", function (terms_value) {
				frm.set_value("terms", terms_value.terms);
				frm.refresh_field("terms");
			});
		});
	}
});

frappe.ui.form.on("Sales Invoice", "before_save", function (frm) {
	if (frm.doc.docstatus == 0 && frm.is_dirty()) {
		frm.doc.workflow_state = "Pending";
	}
});

cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
cur_frm.add_fetch('item_code', 'is_electric_vehicle', 'is_electric_vehicle');
cur_frm.add_fetch('customer', 'tax_id', 'test_vat');
cur_frm.add_fetch('customer', 'vehicle_no', 'customer_vehicle_no');

frappe.ui.form.on("Sales Invoice", "onload_post_render", async function (frm) {
	$('div').find("[data-label='Fetch%20Timesheet']").hide();
	$('div').find("[data-label='Get%20Items%20From']").hide();

	frm.set_query("customer", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
		}
	});
	frm.set_query("special_payment", function (doc) {
		return {
			filters: {
				'app_payment': 1
			}
		}
	});
	frm.set_query("shipping_address_name", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
			filters: { 'customer': doc.customer }
		}
	});
	frm.set_query("customer_address", function (doc) {
		return {
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
			filters: { 'customer': doc.customer }
		}
	});
	$('.frappe-control.input-max-width[data-fieldname="grand_total"]').find('.control-value.like-disabled-input.bold').css('background', 'lightblue')

	//Set Default Warehouse
	if (frm.is_new() !== undefined && frm.is_new()) {
		frm.set_value("set_warehouse", await custom.get_default_warehouse());
		frm.refresh_field("set_warehouse");
	}
});

frappe.ui.form.on("Sales Invoice", "customer_address", function (frm) {
	if (frm.doc.customer_address && !frm.doc.shipping_address_name) {
		frm.set_value("shipping_address_name", frm.doc.customer_address);
		frm.refresh_field('shipping_address_name');
	}
});
frappe.ui.form.on("Sales Invoice", "shipping_address_name", function (frm) {
	if (!frm.doc.shipping_address_name) {
		frm.set_value("shipping_address", null);
	}
});
frappe.ui.form.on("Sales Invoice", "is_finance", function (frm) {
	frm.set_df_property("hypothecation", "reqd", frm.doc.is_finance == 1);
	frm.refresh_field("hypothecation");
});
frappe.ui.form.on("Sales Invoice", "service_invoice", function (frm) {
	frm.set_df_property("model", "reqd", frm.doc.service_invoice == 1);
	frm.refresh_field("model");
	frm.set_df_property("brand", "reqd", frm.doc.service_invoice == 1);
	frm.refresh_field("brand");
	frm.set_df_property("chassis_no", "reqd", frm.doc.service_invoice == 1);
	frm.refresh_field("chassis_no");
	frm.set_df_property("engine_no", "reqd", frm.doc.service_invoice == 1);
	frm.refresh_field("engine_no");
});

frappe.ui.form.on("Sales Invoice", "delayed_payment", function (frm) {
	frm.set_df_property("delayed_payment_reason", "reqd", frm.doc.delayed_payment == 1);
	frm.refresh_field("delayed_payment_reason");
});

frappe.ui.form.on("Sales Invoice", "delayed_payment_reason", function (frm) {
	let reason = frm.doc.delayed_payment_reason.toLowerCase();
	frm.set_df_property("referred_by", "reqd", (reason == "reference" || reason == "distribution channel"));
	frm.set_df_property("delayed_payment_remarks", "reqd", reason == "other");
	frm.refresh_field("delayed_payment_remarks");
	frm.refresh_field("referred_by");
});
frappe.ui.form.on("Sales Invoice", "customer", function (frm) {
	frm.set_df_property("customer_name", "hidden", false);
	if (frm.doc.customer) {
		custom._get_party_balance_formatted('Customer', frm.doc.customer,
			frm.doc.company, function (result) {
				show_alert(result, 8);
			});
	}
});

frappe.ui.form.on("Sales Invoice", "items_on_form_rendered", function (frm) {
	// Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
	// The button in child form
	var grid_row = frm.open_grid_row();

	// Add Button to Child Form ... Wrap it around the "dialog_result" field
	var $btn = $('<button class="btn btn-sm btn-default" style="background:var(--bg-blue);">' + __("Current Stock") + '</button>')
		.appendTo($("<div>").css({
			"margin-bottom": "10px",
			"margin-top": "10px"
		}).appendTo(grid_row.grid_form.fields_dict.item_code.$wrapper));

	// Bind a Event to Added Button
	$btn.on("click", function () {
		if (grid_row.grid_form.fields_dict.item_code.value) {
			custom.show_effective_stock_for(grid_row.grid_form.fields_dict.item_code.value, frm.doc.posting_date);
		}
	});
});

frappe.ui.form.on("Sales Invoice", "validate", function (frm) {
	if (frm.doc.update_stock == 0) {
		frappe.msgprint("Update Stock not Ticked. Please Verify Before Continuing");
	}
	if (!frm.doc.shipping_address_name) {
		if (frm.doc.customer_address) {
			frm.set_value("shipping_address_name", frm.doc.customer_address);
			frm.refresh_field('shipping_address_name');
		}
	}
});

frappe.ui.form.on("Sales Invoice Item", "item_code", function (frm, cdt, cdn) {
	var grid_row = frm.open_grid_row();
	var item = null;
	if (!grid_row) {
		item = frappe.get_doc(cdt, cdn).item_code;
	} else {
		item = grid_row.doc.item_code;
	}
	if (item) {
		frappe.db.get_value('Item', item, 'item_group', function (ig) {
			//--DEBUG--console.log(ig.item_group);
			if (ig.item_group != 'Spare Parts') return;
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.utils.get_average_purchase_rate_for_item",
				args: {
					"item": item
				},
				callback: function (r) {
					if (r.message) {
						//--DEBUG--console.log(r.message[0]);
						show_alert('<style> \
							.alert.desk-alert { \
							max-width:600px !important; \
							max-height:200px !important; \
							} </style> \
							<div style="display: inline-block; \
									/*min-width: 400px;*/ \
									/*width: 400px;*/ \
									height: 50px;">'+ item +
							'</br><span style="font-weight:800;text-align:right;color:black;"><b>' +
							parseFloat(r.message[0]).toFixed(2) + '</b></span></div>', 8);
					}
				}
			});
		});
	}
});
