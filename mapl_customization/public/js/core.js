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
                                if (parseFloat(r.message) > 0) {
                                        alert_msg = alert_msg+"<b><span style=\"color:red;\">"+parseFloat(r.message)+" Dr.</span></b>";
                                } else if (parseFloat(r.message) < 0) {
                                        alert_msg = alert_msg+"<b><span style=\"color:blue;\">"+parseFloat(r.message)+" Cr.</span></b>";
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
