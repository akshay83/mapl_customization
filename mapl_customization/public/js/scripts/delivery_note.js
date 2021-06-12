cur_frm.add_fetch('item_code','is_vehicle','is_vehicle');
frappe.ui.form.on("Delivery Note", "shipping_address_name", function(frm) {
    if (!frm.doc.shipping_address_name) {
       frm.set_value("shipping_address",null);
    }
});
cur_frm.cscript.onload = function() {
   cur_frm.set_query("customer", function(doc) {
   	return{
		query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
	}
   });
   cur_frm.set_query("shipping_address_name", function(doc) {
   	return{
		query: "mapl_customization.customizations_for_mapl.queries.mapl_address_query",
                filters: {'customer':doc.customer}
	}
   });
};
frappe.ui.form.on("Delivery Note", "items_on_form_rendered", function(frm) {	
    // Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
    // The button in child form
    var grid_row = cur_frm.open_grid_row();

	//Set target_warehouse as Null, overcome problem of Default Warehouse
	grid_row.grid_form.fields_dict.target_warehouse.set_model_value(null);
});
