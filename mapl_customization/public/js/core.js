frappe.provide("frappe");
frappe.provide("custom");

custom._get_party_balance = function(party,customer_name,company, _callback) {
	var result = 0.0;
	if (customer_name!=null && company!=null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party=="Customer"?"Customer":"Supplier"
			},
			callback: function(r) {
				if(!r.exc && r.message) {
					_callback(parseFloat(r.message));
				}
			}
		});
	}
};

custom._get_party_balance_in_drcr = function(party,customer_name,company, _callback) {
	var result = 0.0;
	if (customer_name!=null && company!=null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party=="Customer"?"Customer":"Supplier"
			},
			callback: function(r) {
				alert_msg = "";
				if(!r.exc && r.message) {
					balance_value = parseFloat(r.message);
					if (balance_value > 0) {
						alert_msg = "<b><span style=\"color:red;font-weight:initial;\">"+Math.abs(balance_value)+" Dr.</span></b>";
					} else if (balance_value < 0) {
						alert_msg = "<b><span style=\"color:blue;font-weight:initial;\">"+Math.abs(balance_value)+" Cr.</span></b>";
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


custom._get_party_balance_formatted = function(party, customer_name,company, _callback) {
	var result = 0.0;
	if (customer_name!=null && company!=null) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_balance",
			args: {
				party: customer_name,
				company: company,
				party_type: party=="Customer"?"Customer":"Supplier"
			},
			callback: function(r) {
				var alert_msg = customer_name+" Current Balance:";
				 if(!r.exc && r.message) {
					balance_value = parseFloat(r.message);
					if (balance_value > 0) {
						alert_msg = alert_msg+"<b><span style=\"color:red;font-weight:initial;\">"+Math.abs(balance_value)+" Dr.</span></b>";
					} else if (balance_value < 0) {
						alert_msg = alert_msg+"<b><span style=\"color:blue;font-weight:initial;\">"+Math.abs(balance_value)+" Cr.</span></b>";
					} else {
						alert_msg = alert_msg+"<b><span style=\"color:black;font-weight:initial;\"> 0.00</span></b>";
					}
				} else {
					alert_msg = customer_name+" Current Balance:<b><span style=\"color:black;font-weight:initial;\"> 0.00</span></b>";
				}
				_callback(alert_msg);
			}
		});
	}
};

custom.show_stock_dialog = function(stk) {
		d = new frappe.ui.Dialog({title: __('Current Stock at Warehouses')});
		html_string = "<div><div style=\"width:40%;float:left;color:red;\"><b>Warehouse</b></div>\
                                <div style=\"float:left;width:12%;\">Cur Stock</div>\
                                <div style=\"float:left;width:12%;\">Open Order</div>\
                                <div style=\"float:left;width:12%;\">Unconfirmed</div>\
                                <div style=\"float:left;width:12%;\">Undelivered</div>\
                                <div style=\"float:left;width:12%;\">Defective</div>\
                                <div style=\"clear:both;\"></div>\
						</div></div>";
		html_string = html_string+"<div><span style=\"font-size:10px;\"><div style=\"width:40%;float:left;color:red;\">&nbsp</div>\
                                <div style=\"float:left;width:12%;\">&nbsp</div>\
                                <div style=\"float:left;width:12%;\">Confirmed Sales Order</div>\
                                <div style=\"float:left;width:12%;\">Sales Invoice Not Submitted</div>\
                                <div style=\"float:left;width:12%;\">Billed But Not Delivered</div>\
                                <div style=\"float:left;width:12%;\">&nbsp</div>\
                                <div style=\"clear:both;\">&nbsp</div>\
						</div></span></div>";

		$.each(Object.keys(stk).sort(), function(i, key) {
				var v = stk[key];
				html_string = html_string + $.format('<div style=\"padding-top:10px;\">\
                				<div style=\"width:40%;float:left;\"><b>{0}</b></div>\
                                <div style=\"color:blue;float:left;width:12%;\">{1}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{2}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{3}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{4}</div>\
                                <div style=\"color:blue;float:left;width:12%;\">{5}</div>\
                                <div style=\"clear:both;\"></div>\
                            </div>',[v['NAME'], v['CLOSING STOCK'], v['OPEN ORDER'], v['UNCONFIRMED'], v['UNDELIVERED'], v['DEFECTIVE']]);
		});
	html_string = html_string + "<div style=\"clear:both;\"></div><hr>";
	$(d.body).html(html_string);
	d.$wrapper.find('.modal-dialog').css("width", "900px");
	d.show();
};

custom.update_address = function(frm) {
	if (!(typeof frm === 'string' || frm instanceof String) && frm.is_dirty()) {
		frappe.msgprint(__("Please Save Changes Before Updating"));
		return;
	}
	frappe.confirm("Please Be Aware That This Event Would Affect <B>All the Documents</B> in the System.\
			Advice You to Kindly Make a New Address for New Documents. Do You Want to Continue?", function() {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.update_address.update_address",
			args: {
				"address_name": (typeof frm === 'string')?frm:frm.doc.name,
			},
			callback: function(r) {
				if(!r.exc) {
					frappe.msgprint(__("Address Updated Across All Relevant Documents"));
				}
			}
		});
	});
};
