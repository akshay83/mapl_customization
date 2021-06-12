// Copyright (c) 2017, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.ui.form.on("Adjustments Set Off Tool", "fetch_details", function(frm) {
			frm.clear_table("adjustment_detail");
            frappe.call({
	                method: "mapl_customization.customizations_for_mapl.doctype.adjustments_set_off_tool.adjustments_set_off_tool.fetch_details",
	                args: {
			    		"filters": frm.doc
	                },
               		callback: function(r) {
						if(r.message) {
			               	$.each(r.message, function(i, d) {
		                    	var c = frm.add_child("adjustment_detail");
                        		c.customer_name = d.customer_name;
                        		c.customer = d.party;
                        		c.total_debit = d["Total Debit"];
                        		c.total_credit = d["Total Credit"];
		                        c.difference_amount = d.Difference;
		                        c.difference_percent = d.Percentage;
        			        });
                        frm.refresh_field("adjustment_detail");
						frappe.msgprint(__("Success"));
					   }		       
				   }
            });
});
