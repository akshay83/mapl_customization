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

custom.show_effective_stock_for = function (item_code, on_date) {
	frappe.call({
		method: "mapl_customization.customizations_for_mapl.utils.get_effective_stock_at_all_warehouse",
		args: {
			"item_code": item_code,
			"date": on_date
		},
		callback: function (r) {
			if (r.message) {
				custom.show_stock_dialog(item_code, r.message[0], r.message[1]);
			}
		}
	});
};

custom.show_stock_dialog = function (item_code, columns, values) {
	let table_fields = [];
	let data = {};
	for (let i = 0; i < columns.length; i++) {
		let fn = columns[i]["fieldname"];
		let val = values[0][i];
		table_fields.push({
			fieldtype: "Data",
			label: columns[i]["label"],
			fieldname: fn,
			in_list_view: 1,
			read_only: 1,
			hidden: (columns[i]["fieldtype"] == "Float" || columns[i]["fieldname"] == "warehouse") ? 0 : 1,
			columns: columns[i]["fieldname"] == "warehouse" ? 2 : 1
		});
		data[fn] = val;
	}
	let fields = [{
		fieldname: "stock_details",
		fieldtype: "Table",
		fields: table_fields,
		data: [data],
		readonly: 1
	}];
	let dialog = new frappe.ui.Dialog({ title: 'Current Stock for :' + item_code, fields });
	dialog.$wrapper.find('.modal-content').css("width", "1200px");
	dialog.$wrapper.find('.modal-dialog').css("position", "absolute");
	dialog.$wrapper.find('.modal-dialog').css("left", "10%");
	dialog.show();
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

custom.hide_print_button = async function (doctype, frm) {
	//TO HIDE PRINT ICON & PRINT MENU FROM A DOCUMENT IN VERSION 6 USE

	//--DEBUG--console.log("Calling Hide Print Button");
	//--DEBUG--console.log(cur_frm.doc.workflow_state);
	//--DEBUG--console.log(cur_frm.doc.__unsaved);
	//--DEBUG--console.log("Cancel Button:"+$('.grey-link:contains(Cancel)').length);
	if (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Administrator")) return;
	if (await custom.is_workflow_active_on(doctype)) {
		if (frm.doc.workflow_state != "Pending" && frm.doc.workflow_state != "Rejected" && frm.doc.workflow_state != "Cancelled" && !frm.is_dirty()) {
			let einvoice = false;
			let print_doc = false;
			if (doctype == 'Sales Invoice') einvoice = await custom.einvoice_eligibility(frm.doc);
			if (einvoice) {
				if (frm.doc.irn !== undefined && frm.doc.irn != null && frm.doc.irn_cancelled === 0) {
					print_doc = true;
				}
			} else {
				print_doc = true;
			}
			let negative_stock_check = await custom.check_if_sales_invoice_will_result_in_negative_stock(frm.doc);
			let hsn_check = await custom.check_sales_invoice_hsn_length(frm.doc);
			if (doctype == 'Sales Invoice' && (negative_stock_check.result	|| hsn_check.result)) {
					print_doc = false; 
			}
			custom.hide_show_print_buttons(print_doc);
		} else {
			custom.hide_show_print_buttons(false);
		}
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

custom.get_default_warehouse = async function (user_name) {
	let uname = frappe.user.name;
	if (user_name !== undefined && user_name != null) {
		uname = user_name;
	}
	let return_value = null;
	let promise = new Promise((resolve, reject) => {
		frappe.db.get_value("User", uname, "default_user_warehouse").then(val => {
			if (val.message.default_user_warehouse !== undefined && val.message.default_user_warehouse != null) {
				return_value = val.message.default_user_warehouse;
			} else {
				return_value = frappe.defaults.get_default("default_warehouse");
			}
			resolve(return_value);
		});
	});
	await promise.catch(() => frappe.throw());
	return return_value;
};

custom.einvoice_eligibility = async function (doc) {
	const res = await frappe.call({
		method: 'erpnext.regional.india.e_invoice.utils.validate_eligibility',
		args: { doc: doc, taxpro: 1 }
	});
	return res.message;
};

custom.check_if_sales_invoice_will_result_in_negative_stock = async function (doc) {
	const delay = ms => new Promise(res => setTimeout(res, ms)); //Utility Method
	let negative_stock = { "result": false };	
	if (doc.docstatus >= 1 || doc.update_stock == 0 || doc.__islocal == 1) return negative_stock;
	let promise = new Promise((resolve, reject) => {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.check_if_invoice_will_end_up_in_negative_stock",
			args: {
				doc: doc
			},
			callback: async function (r) {
				//--DEBUG--console.log(r);
				if (!r.exc) {
					// await delay(5000); // - way to use delay ----- async function
					negative_stock = r.message;
				}
				resolve(negative_stock);
				return;
			}
		});
	});
	await promise.catch(() => frappe.throw());
	//--DEBUG--console.log("Out:" + negative_stock);
	return negative_stock;
};

custom.check_sales_invoice_hsn_length = async function (doc) {
	let length_check_failed = {"result": false};
	if (doc.docstatus >= 1 || doc.__islocal == 1) return length_check_failed;
	let promise = new Promise((resolve, reject) => {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.sales_invoice_validation.validate_hsn_code",
			args: {
				doc: doc,
				method: null,
				show_message: 0
			},
			callback: async function (r) {
				//--DEBUG--console.log(r);
				if (!r.exc) {
					length_check_failed = r.message;
				}
				resolve(length_check_failed);
				return;
			}
		});
	});
	await promise.catch(() => frappe.throw());
	//--DEBUG--console.log("Length Check Failed:" + length_check_failed);
	return length_check_failed;
};