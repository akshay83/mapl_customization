frappe.ui.form.on("Sales Invoice", "is_pos", function(frm) {
	console.log('is pos');
	if (frm.doc.is_pos==1) {
		setTimeout(function() {
			cur_frm.clear_table('payments');
			cur_frm.refresh_field('payments');
		}, 2000 );
	}
});

function custom_hide_print_button(frm) {
	//TO HIDE PRINT ICON & PRINT MENU FROM A DOCUMENT IN VERSION 6 USE

	//--DEBUG--console.log("Calling Hide Print Button");
	//--DEBUG--console.log(cur_frm.doc.workflow_state);
	//--DEBUG--console.log(cur_frm.doc.__unsaved);
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
	if (typeof frm.doc.workflow_state !== "undefined") {
		if (frm.doc.workflow_state!="Pending" && frm.doc.workflow_state!="Rejected" && frm.doc.workflow_state!="Cancelled" && !frm.is_dirty()) {
			$('ul[class="dropdown-menu"] a:contains("Print")').show(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
			$(".page-icon-group.hidden-xs.hidden-sm").show(); //HIDE PRINT ICON - FIND BASED ON ID //
		} else {
			$('ul[class="dropdown-menu"] a:contains("Print")').hide(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
			$(".page-icon-group.hidden-xs.hidden-sm").hide(); //HIDE PRINT ICON - FIND BASED ON ID //
		}
	} else {
		if (!frm.is_dirty()) {
			$('ul[class="dropdown-menu"] a:contains("Print")').show(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
			$(".page-icon-group.hidden-xs.hidden-sm").show(); //HIDE PRINT ICON - FIND BASED ON ID //
		} else {
			$('ul[class="dropdown-menu"] a:contains("Print")').hide(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
			$(".page-icon-group.hidden-xs.hidden-sm").hide(); //HIDE PRINT ICON - FIND BASED ON ID //
		}
	}
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
};

function custom_disable_save_button(frm) {
	//--DEBUG--console.log("Calling Disable Save");
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
	frm.enable_save();
	if (!frm.doc.__islocal && !frappe.user.has_role("System Manager") && frm.doc.docstatus!=0) {
		frm.disable_save();
	}
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
};

frappe.ui.form.on("Sales Invoice", "*", function(frm) {
	custom_hide_print_button(frm);
});

frappe.ui.form.on("Sales Invoice", "onload", function(frm) {
	//--DEBUG--console.log("Called Onload Event");
	custom_hide_print_button(frm);
	custom_disable_save_button(frm);
});

//ADD MENU ITEM IN MENU DROPDOWN BUTTON
frappe.ui.form.on("Sales Invoice", "refresh", function(frm) {
	//TO FILL VOLATILE TYPE FIELD
	//if (frm.doc.customer!=null) {
	//    frappe.model.get_value("Customer",frm.doc.customer,"tax_id", function(value) {;
	//         frm.set_value("test_vat",value.tax_id);
	//    });
	//}

	//--DEBUG--console.log("Called Referesh Event");
	custom_hide_print_button(frm);
	custom_disable_save_button(frm);
	$('.frappe-control.input-max-width[data-fieldname="grand_total"]').find('.control-value.like-disabled-input.bold').css('background','lightblue')
});

cur_frm.add_fetch('item_code','is_vehicle','is_vehicle');
cur_frm.add_fetch('item_code','is_electric_vehicle','is_electric_vehicle');
cur_frm.add_fetch('customer','tax_id','test_vat');
cur_frm.add_fetch('customer','vehicle_no','customer_vehicle_no');

frappe.ui.form.on("Sales Invoice","onload_post_render", function(frm) {
	frm.set_query("customer", function(doc) {
	   	return{
			query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
		}
	});
	frm.set_query("special_payment", function(doc) {
		return{
			filters: {
				'app_payment': 1
			}
		}
	});
	frm.set_query("shipping_address_name", function(doc) {
		return{
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: {'customer':doc.customer}
		}
	});
	cur_frm.set_query("customer_address", function(doc) {
		return{
			query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
				filters: {'customer':doc.customer}
	}
	});
	$('.frappe-control.input-max-width[data-fieldname="grand_total"]').find('.control-value.like-disabled-input.bold').css('background','lightblue')
});

frappe.ui.form.on("Sales Invoice", "shipping_address_name", function(frm) {
	if (!frm.doc.shipping_address_name) {
		frm.set_value("shipping_address",null);
	}
});
frappe.ui.form.on("Sales Invoice", "is_finance", function (frm) {
	cur_frm.set_df_property("hypothecation", "reqd", frm.doc.is_finance==1);
	cur_frm.refresh_field("hypothecation");
});
frappe.ui.form.on("Sales Invoice", "service_invoice", function (frm) {
	frm.set_df_property("model", "reqd", frm.doc.service_invoice==1);
	frm.refresh_field("model");
	frm.set_df_property("brand", "reqd", frm.doc.service_invoice==1);
	frm.refresh_field("brand");
	frm.set_df_property("chassis_no", "reqd", frm.doc.service_invoice==1);
	frm.refresh_field("chassis_no");
	frm.set_df_property("engine_no", "reqd", frm.doc.service_invoice==1);
	frm.refresh_field("engine_no");
});

frappe.ui.form.on("Sales Invoice", "delayed_payment", function (frm) {
	frm.set_df_property("referred_by", "reqd", frm.doc.delayed_payment==1);
	frm.refresh_field("referred_by");
});
frappe.ui.form.on("Sales Invoice", "customer", function (frm) {
	frm.set_df_property("customer_name", "hidden", false);
	if (frm.doc.customer) {
		custom._get_party_balance_formatted('Customer', frm.doc.customer,
					frm.doc.company, function(result) {
						show_alert(result,8);
		});
	}
});

frappe.ui.form.on("Sales Invoice", "items_on_form_rendered", function(frm) {
	// Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
	// The button in child form
	var grid_row = cur_frm.open_grid_row();

	//Set target_warehouse as Null, overcome problem of Default Warehouse
	grid_row.grid_form.fields_dict.target_warehouse.set_model_value(null);

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
					"date": cur_frm.doc.posting_date
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

frappe.ui.form.on("Sales Invoice", "validate", function(frm) {
	if (frm.doc.default_warehouse != null) {
		frm.doc.items.forEach(function(i) {
			if (i.warehouse == null) {
				i.warehouse = frm.doc.default_warehouse;
			}
		});
	}
	/*frm.doc.items.forEach(function(i) {
            if (i.gst_hsn_code == null || i.gst_hsn_code == "") {
            	frappe.msgprint("HSN Code Not found for "+i.item_code+", Please verify");
            }
	});*/
	if (frm.doc.update_stock == 0) {
		frappe.msgprint("Update Stock not Ticked. Please Verify Before Continuing");
	}
});

frappe.ui.form.on("Sales Invoice Item", "item_code", function(frm, cdt, cdn) {
	var grid_row = frm.open_grid_row();
	var item = null;
	if (!grid_row) {
		item = frappe.get_doc(cdt, cdn).item_code;
	} else {
		item = grid_row.doc.item_code;
	}
	if (item) {
		frappe.db.get_value('Item', item, 'item_group', function(ig) {
			//--DEBUG--console.log(ig.item_group);
			if (ig.item_group != 'Spare Parts') return;
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.utils.get_average_purchase_rate_for_item",
				args: {
					"item": item
				},
				callback: function(r) {
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
									height: 50px;">'+item+
							'</br><span style="font-weight:800;text-align:right;color:black;"><b>'+
							parseFloat(r.message[0]).toFixed(2)+'</b></span></div>',8);
					}
				}
			});
		});
	}
});