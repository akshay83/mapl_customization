cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
cur_frm.add_fetch('item_code', 'is_electric_vehicle', 'is_electric_vehicle');
/***************************************************************/
/*              Invoke Dialog On Child Form                    */
/***************************************************************/

frappe.ui.form.on("Purchase Invoice", "items_on_form_rendered", function(frm) {
    // Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
    // The button in child form
    var grid_row = frm.open_grid_row();

	//Set rejected_warehouse as Null, overcome problem of Default Warehouse
	grid_row.grid_form.fields_dict.rejected_warehouse.set_model_value(null);


    // Add Button to Child Form ... Wrap it around the "dialog_result" field
    var $btn = $('<button class="btn btn-sm btn-default">' + __("Add Serial No") + '</button>')
        .appendTo($("<div>")
            .css({
                "margin-bottom": "10px",
                "margin-top": "10px"
            })
            .appendTo(grid_row.grid_form.fields_dict.serial_no.$wrapper));

    // Bind a Event to Added Button
    $btn.on("click", function() {
        var fields = [];
        for (var rows = 1; rows <= Math.abs(grid_row.grid_form.fields_dict.qty.get_value()); rows++) {
            fields.push({
                label: "Row No:".concat(rows),
                fieldname: "row_no_".concat(rows),
                fieldtype: "Section Break"
            });
            for (var columns = 1; columns <= 4; columns++) {
                if (columns == 1) {
                    fields.push({
                        label: "Serial/Chassis No",
                        fieldname: "chassis_no_".concat(rows),
                        fieldtype: "Data",
                        reqd: 1
                    });
                }
                if (grid_row.grid_form.fields_dict['is_vehicle'].value == 1) {
                    if (columns == 2) {
                        fields.push({
                            label: grid_row.grid_form.fields_dict['is_electric_vehicle'].value==0?"Engine No":"Motor No",
                            fieldname: "engine_no_".concat(rows),
                            fieldtype: "Data",
                            reqd: grid_row.grid_form.fields_dict['is_electric_vehicle'].value==0?1:0
                        });
                    }
                    if (columns == 3) {
                        fields.push({
                            label: "Key No",
                            fieldname: "key_no_".concat(rows),
                            fieldtype: "Data",
                            reqd: grid_row.grid_form.fields_dict['is_electric_vehicle'].value==0?1:0
                        });
                    }
                    if (columns == 4) {
                        fields.push({
                            label: "Color",
                            fieldname: "color_".concat(rows),
                            fieldtype: "Data",
                            reqd: 1
                        });
                    }
                    if (columns < 4) {
                        fields.push({
                            fieldname: "column_no_".concat(columns),
                            fieldtype: "Column Break"
                        });
                    }
                }
            }
        }
        // Add "Add" Button to the Dialog
        fields.push({
            fieldtype: "Section Break"
        });
        //fields.push({fieldtype: "Button", "label": "Set", fieldname: "add"});


        var d = new frappe.ui.Dialog({
            title: __("Add Serial No"),
            fields
        });
		
        if (grid_row.grid_form.fields_dict.serial_no.get_value() != "") {
            var existing_serial_no = grid_row.grid_form.fields_dict.serial_no.get_value().split("\n");
			var existing_engine_no = "";
			var existing_key_no = "";
			var existing_color = "";
			if (grid_row.grid_form.fields_dict['is_vehicle'].value == 1) {
				existing_engine_no = grid_row.grid_form.fields_dict.engine_nos.get_value().split("\n");
				existing_key_no = grid_row.grid_form.fields_dict.key_nos.get_value().split("\n");
				existing_color = grid_row.grid_form.fields_dict.color.get_value().split("\n");
			}
			for (var row = 1; row <= existing_serial_no.length + 1; row++) {
				d.set_value("chassis_no_".concat(row), existing_serial_no[row - 1]);
				if (grid_row.grid_form.fields_dict['is_vehicle'].value == 1) {
					d.set_value("engine_no_".concat(row), existing_engine_no[row - 1]);
					d.set_value("key_no_".concat(row), existing_key_no[row - 1]);
					d.set_value("color_".concat(row), existing_color[row - 1]);
				}
			}	
        }
        //Bind Event to Add Button in Dialog
        d.set_primary_action(__("Save"), function() {
            /*****************/
            var args = d.get_values();
            if (!args) return;
            frappe.call({
                method: "mapl_customization.customizations_for_mapl.utils.validate_input_serial",
                args: {
                    "args": d.get_values(),
                    "rows": grid_row.grid_form.fields_dict.received_qty.get_value(),
                    "is_vehicle": grid_row.grid_form.fields_dict['is_vehicle'].value,
					"is_electric_vehicle": grid_row.grid_form.fields_dict['is_electric_vehicle'].value
                },

                callback: function(r) {
                    if (!r.message) {
                        //return;
                    }
                }
            });

            /*****************/

            //d.get_input("add").on("click", function() {
            var result_serial_no = "";
            var result_engine_no = "";
            var result_key_no = "";
            var result_color = "";
            var color = "";
            for (var rows = 1; rows <= grid_row.grid_form.fields_dict.qty.get_value(); rows++) {
            	var carr_retu = "\n"
                if (rows == grid_row.grid_form.fields_dict.qty.get_value()) {
                	carr_retu = "";
                }
                result_serial_no = result_serial_no.concat(d.get_value("chassis_no_".concat(rows)), carr_retu);
                result_engine_no = result_engine_no.concat(d.get_value("engine_no_".concat(rows)), carr_retu);
                result_key_no = result_key_no.concat(d.get_value("key_no_".concat(rows)), carr_retu);
                result_color = result_color.concat(d.get_value("color_".concat(rows)), carr_retu);
            }

            d.hide();
                //Set Resultant Value from Dialog in a Child Form Field - Here dialog_result
                grid_row.grid_form.fields_dict.serial_no.set_value(result_serial_no);
                //Set Resultant Value from Dialog in a Child Form Field - Here dialog_result
                grid_row.grid_form.fields_dict.engine_nos.set_value(result_engine_no);
                //Set Resultant Value from Dialog in a Child Form Field - Here dialog_result
                grid_row.grid_form.fields_dict.key_nos.set_value(result_key_no);
                grid_row.grid_form.fields_dict.color.set_value(result_color);


            return false;
        });

        d.show();
		d.$wrapper.find('.modal-dialog').css("width","950px");
    });
});
/***************************************************************/
/*              End Dialog On Child Form                       */
/***************************************************************/

frappe.ui.form.on("Purchase Invoice", "items_on_form_rendered", function(frm) {
	var grid_row = frm.open_grid_row();
	grid_row.grid_form.fields_dict.warehouse.set_model_value(frm.doc.default_accepted_warehouse);
});

frappe.ui.form.on("Purchase Invoice", "validate", function(frm) {
	if (frm.doc.default_accepted_warehouse != null) {
		frm.doc.items.forEach(function(i) {
			if (i.warehouse == null) {
				i.warehouse = frm.doc.default_accepted_warehouse;
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

frappe.ui.form.on("Purchase Invoice", "refresh", function(frm) {
   frm.enable_save();
   if (!frm.doc.__islocal && !frappe.user.has_role("System Manager") && frm.doc.docstatus!=0) {
       frm.disable_save();
   }
});
