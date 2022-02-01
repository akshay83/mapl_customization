frappe.provide("frappe");
frappe.provide("custom");

custom._get_party_balance = function (party, customer_name, company, _callback) {
	var result = 0.0;
	if (customer_name != null && company != null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party == "Customer" ? "Customer" : "Supplier"
			},
			callback: function (r) {
				if (!r.exc && r.message) {
					_callback(parseFloat(r.message));
				}
			}
		});
	}
};

custom._get_party_balance_in_drcr = function (party, customer_name, company, _callback) {
	var result = 0.0;
	if (customer_name != null && company != null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party == "Customer" ? "Customer" : "Supplier"
			},
			callback: function (r) {
				alert_msg = "";
				if (!r.exc && r.message) {
					balance_value = parseFloat(r.message);
					if (balance_value > 0) {
						alert_msg = "<b><span style=\"color:red;font-weight:initial;\">" + Math.abs(balance_value) + " Dr.</span></b>";
					} else if (balance_value < 0) {
						alert_msg = "<b><span style=\"color:blue;font-weight:initial;\">" + Math.abs(balance_value) + " Cr.</span></b>";
					} else {
						alert_msg = "<b><span style=\"color:black;font-weight:initial;\"> 0.00</span></b>";
					}
				}
				else {
					alert_msg = "<b><span style=\"color:black;\"> 0.00</span></b>";
				}
				_callback(alert_msg);
			}
		});
	}
};


custom._get_party_balance_formatted = function (party, customer_name, company, _callback) {
	var result = 0.0;
	if (customer_name != null && company != null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party == "Customer" ? "Customer" : "Supplier"
			},
			callback: function (r) {
				var alert_msg = customer_name + " Current Balance:";
				if (!r.exc && r.message) {
					balance_value = parseFloat(r.message);
					if (balance_value > 0) {
						alert_msg = alert_msg + "<b><span style=\"color:red;font-weight:initial;\">" + Math.abs(balance_value) + " Dr.</span></b>";
					} else if (balance_value < 0) {
						alert_msg = alert_msg + "<b><span style=\"color:blue;font-weight:initial;\">" + Math.abs(balance_value) + " Cr.</span></b>";
					} else {
						alert_msg = alert_msg + "<b><span style=\"color:black;font-weight:initial;\"> 0.00</span></b>";
					}
				} else {
					alert_msg = customer_name + " Current Balance:<b><span style=\"color:black;font-weight:initial;\"> 0.00</span></b>";
				}
				_callback(alert_msg);
			}
		});
	}
};

custom.show_stock_dialog = function (stk) {
	d = new frappe.ui.Dialog({ title: __('Current Stock at Warehouses') });
	html_string = "<div><div style=\"width:40%;float:left;color:red;\"><b>Warehouse</b></div>\
                                <div style=\"float:left;width:12%;\">Cur Stock</div>\
                                <div style=\"float:left;width:12%;\">Open Order</div>\
                                <div style=\"float:left;width:12%;\">Unconfirmed</div>\
                                <div style=\"float:left;width:12%;\">Undelivered</div>\
                                <div style=\"float:left;width:12%;\">Defective</div>\
                                <div style=\"clear:both;\"></div>\
						</div></div>";
	html_string = html_string + "<div><span style=\"font-size:10px;\"><div style=\"width:40%;float:left;color:red;\">&nbsp</div>\
                                <div style=\"float:left;width:12%;\">&nbsp</div>\
                                <div style=\"float:left;width:12%;\">Confirmed Sales Order</div>\
                                <div style=\"float:left;width:12%;\">Sales Invoice Not Submitted</div>\
                                <div style=\"float:left;width:12%;\">Billed But Not Delivered</div>\
                                <div style=\"float:left;width:12%;\">&nbsp</div>\
                                <div style=\"clear:both;\">&nbsp</div>\
						</div></span></div>";

	$.each(Object.keys(stk).sort(), function (i, key) {
		var v = stk[key];
		html_string = html_string + $.format('<div style=\"padding-top:10px;\">\
                				<div style=\"width:40%;float:left;\"><b>{0}</b></div>\
                                <div style=\"color:blue;float:left;width:12%;\">{1}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{2}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{3}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{4}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{5}</div>\
                                <div style=\"clear:both;\"></div>\
                            </div>', [v['NAME'], v['CLOSING STOCK'], v['OPEN ORDER'], v['UNCONFIRMED'], v['UNDELIVERED'], v['DEFECTIVE']]);
	});
	html_string = html_string + "<div style=\"clear:both;\"></div><hr>";
	$(d.body).html(html_string);
	d.$wrapper.find('.modal-dialog').css("width", "900px");
	d.show();
};

custom.update_address = function (frm) {
	if (!(typeof frm === 'string' || frm instanceof String) && frm.is_dirty()) {
		frappe.msgprint(__("Please Save Changes Before Updating"));
		return;
	}
	frappe.confirm("Please Be Aware That This Event Would Affect <B>All the Documents</B> in the System.\
			Advice You to Kindly Make a New Address for New Documents. Do You Want to Continue?", function () {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.update_address.update_address",
			args: {
				"address_name": (typeof frm === 'string') ? frm : frm.doc.name,
			},
			callback: function (r) {
				if (!r.exc) {
					frappe.msgprint(__("Address Updated Across All Relevant Documents"));
				}
			}
		});
	});
};

custom.hide_show_print_buttons = function (show) {
	if (show) {
		$('.dropdown-item:contains("Print")').show(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
		$('.text-muted.btn.btn-default.icon-btn[data-original-title="Print"]').show();
	} else {
		$('.dropdown-item:contains("Print")').hide(); //HIDE MENU ENTRY - FIND BASED ON TEXT AND <A> //
		$('.text-muted.btn.btn-default.icon-btn[data-original-title="Print"]').hide();
	}
};

custom.hide_print_button = function (doctype, frm) {
	//TO HIDE PRINT ICON & PRINT MENU FROM A DOCUMENT IN VERSION 6 USE

	//--DEBUG--console.log("Calling Hide Print Button");
	//--DEBUG--console.log(cur_frm.doc.workflow_state);
	//--DEBUG--console.log(cur_frm.doc.__unsaved);
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
	if (typeof frm.doc.workflow_state !== "undefined") {
		frappe.db.get_value('Workflow', { "document_type": doctype, "is_active": 1 }, "name", function (val) {
			if (Object.keys(val).length > 0) {
				if (frm.doc.workflow_state != "Pending" && frm.doc.workflow_state != "Rejected" && frm.doc.workflow_state != "Cancelled" && !frm.is_dirty()) {
					custom.hide_show_print_buttons(true);
				} else {
					custom.hide_show_print_buttons(false);
				}
			} else {
				custom.handle_default_print_action(doctype, frm);
			}
		});
	} else {
		custom.handle_default_print_action(doctype, frm);
	}
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
};

custom.handle_default_print_action = function (doctype, frm) {
	if (!frm.is_dirty() && !(doctype == "Payment Entry" && frm.doc.docstatus != 1)) {
		custom.hide_show_print_buttons(true);
	} else {
		custom.hide_show_print_buttons(false);
	}
};

custom.fetch_details_connected_accounts = function (frm, cdt, cdn) {
	var grid_row = frm.open_grid_row();
	var party = null;
	var pt = null;
	var p = null;
	var comp = null;

	if (!grid_row) {
		party = frappe.get_doc(cdt, cdn);
		pt = party.party_type;
		p = party.party;
		comp = party.company;
	} else {
		pt = grid_row.grid_form.fields_dict.party_type.get_value();
		p = grid_row.grid_form.fields_dict.party.get_value();
		comp = grid_row.grid_form.fields_dict.company.get_value();;
	}
	if (pt && p) {
		if (!comp) frappe.throw(__("Please select Company"));
		frappe.call({
			method: "erpnext.accounts.doctype.journal_entry.journal_entry.get_party_account_and_balance",
			args: {
				company: comp,
				party_type: pt,
				party: p
			},
			callback: function (r) {
				if (!r.exc && r.message) {
					if (grid_row) {
						grid_row.grid_form.fields_dict.account.set_value(r.message.account);
					} else {
						party.account = r.message.account;
					}
					frm.refresh_field('connected_accounts_list');
				}
			}
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
					frm.refresh_field('connected_accounts_list');
				}
			}
		});
	}
};
