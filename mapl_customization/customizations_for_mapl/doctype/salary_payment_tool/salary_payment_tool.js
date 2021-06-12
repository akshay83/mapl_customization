// Copyright (c) 2017, Akshay Mehta and contributors
// For license information, please see license.txt

frappe.ui.form.on("Salary Payment Tool", "fetch_details", function(frm) {
		frm.clear_table("payment_details");
		frappe.call({
                method: "mapl_customization.customizations_for_mapl.doctype.salary_payment_tool.salary_payment_tool.fetch_details",
                args: {
		    		"from_date": frm.doc.from_date,
					"to_date": frm.doc.to_date
                },
           		callback: function(r) {
					if(r.message) {
						var total_pay = 0;
		               	$.each(r.message, function(i, d) {
							if (!d.designation || d.designation != "Director") {
			                    	var c = frm.add_child("payment_details");
	                        		c.employee_name = d.employee_name;
	                        		c.employee = d.employee_id;
	                        		c.amount_paid = d.net_pay;
                                    total_pay = total_pay + c.amount_paid;
							}
       			        });
                        frm.set_value("total_payment", total_pay);
						frm.refresh_field("payment_details");
                        frm.refresh_field("total_payment");
						frappe.msgprint(__("Success"));
					}		       
				}
		});
});


frappe.ui.form.on("Salary Payment Tool", "refresh", function(frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Make Journal Entries'), function() { 
			if (cur_frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
            frappe.call({
	                method: "mapl_customization.customizations_for_mapl.doctype.salary_payment_tool.salary_payment_tool.make_jv",
	                args: {
			    		"docname": frm.doc.name
	                },
               		callback: function(r) {
						if(!r.exc) {
							frappe.msgprint(__("Success"));
	                                frm.reload_doc();
					}		       
				}
            });
		});
	}
});

frappe.ui.form.on("Salary Payment Details", "employee", function(frm, dt, dn) {
	var grid_row = cur_frm.open_grid_row();
	var p = null;
    if (!grid_row) {
    	party = frappe.get_doc(dt, dn);
        p = party.employee;
    } else {
		p = grid_row.grid_form.fields_dict.employee.get_value();
    }    

	if(p) {
		frappe.call({
			method: "mapl_customization.customizations_for_mapl.utils.get_party_name",
			args: {
				party_type: 'Employee',
				party: p
			},
			callback: function(r) {
				if(!r.exc && r.message) {
                	if (grid_row) {
						grid_row.grid_form.fields_dict.employee_name.set_value(r.message);
                    } else {
                    	party.employee_name = r.message;
                    }
                    cur_frm.refresh_field('payment_details');
				}
			}
		});  
	}
});
