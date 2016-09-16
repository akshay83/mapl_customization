frappe.provide("frappe");
frappe.provide("custom");

var orig_mk_control = frappe.ui.form.make_control;

frappe.ui.form.make_control = function(opts) {
    var control_name = "Control"+opts.df.fieldtype.replace(/ /g,"");
    //console.log(control_name);
    if (control_name == "ControlVolatile") {
        return new frappe.ui.form["ControlReadOnly"](opts);
    }    
    return orig_mk_control(opts);
};

custom._get_party_balance = function (party,customer_name,company, callback) {
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
                              callback(parseFloat(r.message));
    	    			} 
        			}
        		});          
            }
};

custom._get_party_balance_in_drcr = function (party,customer_name,company, callback) {
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
                                        alert_msg = "<b><span style=\"color:red;\">"+Math.abs(balance_value)+" Dr.</span></b>";
                                } else if (balance_value < 0) {
                                        alert_msg = "<b><span style=\"color:blue;\">"+Math.abs(balance_value)+" Cr.</span></b>";
                                } else {
                                        alert_msg = "<b><span style=\"color:black;\"> 0.00</span></b>";
                                }
    	    			} 
                        else {
                             alert_msg = "<b><span style=\"color:black;\"> 0.00</span></b>";
                        }
                        callback(alert_msg);
        			}
        		});          
            }
};


custom._get_party_balance_formatted = function (party, customer_name,company, callback) {
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
                                        alert_msg = alert_msg+"<b><span style=\"color:red;\">"+Math.abs(balance_value)+" Dr.</span></b>";
                                } else if (balance_value < 0) {
                                        alert_msg = alert_msg+"<b><span style=\"color:blue;\">"+Math.abs(balance_value)+" Cr.</span></b>";
                                } else {
                                        alert_msg = alert_msg+"<b><span style=\"color:black;\"> 0.00</span></b>";
                                }
              				 } else {
                                alert_msg = customer_name+" Current Balance:<b><span style=\"color:black;\"> 0.00</span></b>";
                             }
                             callback(alert_msg);
    	    			} 
        			});
        		}         
            
};

custom.show_stock_dialog = function(stk) {
		d = new frappe.ui.Dialog({title: __('Current Stock at Warehouses')});
		html_string = "<div style=\"width:40%;float:left;color:red;\"><b>Warehouse</b></div>\
                                <div style=\"float:left;width:15%;\">Cur Stock</div>\
                                <div style=\"float:left;width:15%;\">Unconfirmed</div>\
                                <div style=\"float:left;width:15%;\">Undelivered</div>\
                                <div style=\"float:left;width:15%;\">Defective</div>\
                                <div style=\"clear:both;\"></div>\
						</div>";
		$.each(keys(stk).sort(), function(i, key) {
				var v = stk[key];
				html_string = html_string + $.format('<div style=\"padding-top:10px;\">\
                				<div style=\"width:40%;float:left;\"><b>{0}</b></div>\
                                <div style=\"color:blue;float:left;width:15%;\">{1}</div>\
                                <div style=\"color:blue;float:left;width:15%;\">{2}</div>\
                                <div style=\"color:blue;float:left;width:15%;\">{3}</div>\
                                <div style=\"color:blue;float:left;width:15%;\">{4}</div>\
                                <div style=\"clear:both;\"></div>\
                            </div>',
						   [v['NAME'], v['CLOSING STOCK'], v['UNCONFIRMED'], v['UNDELIVERED'], v['DEFECTIVE']]);
                console.log(v);
		});   
        html_string = html_string + "<div style=\"clear:both;\"></div><hr>";     
        $(d.body).html(html_string);
        d.$wrapper.find('.modal-dialog').css("width", "800px");
        d.show();
}
