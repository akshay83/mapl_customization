cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
/***************************************************************/
/*              Invoke Dialog On Child Form                    */
/***************************************************************/

frappe.ui.form.on("Purchase Receipt", "items_on_form_rendered", function(frm) {
    // Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
    // The button in child form
    var grid_row = cur_frm.open_grid_row();

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
        for (var rows = 1; rows <= grid_row.grid_form.fields_dict.received_qty.get_value(); rows++) {
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
                            label: "Engine No",
                            fieldname: "engine_no_".concat(rows),
                            fieldtype: "Data",
                            reqd: 1
                        });
                    }
                    if (columns == 3) {
                        fields.push({
                            label: "Key No",
                            fieldname: "key_no_".concat(rows),
                            fieldtype: "Data",
                            reqd: 1
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
            var existing_engine_no = grid_row.grid_form.fields_dict.serial_no.get_value().split("\n");
            var existing_key_no = grid_row.grid_form.fields_dict.serial_no.get_value().split("\n");
            var existing_color = grid_row.grid_form.fields_dict.color.get_value().split("\n");
            for (var row = 1; row <= existing_serial_no.length + 1; row++) {
                d.set_value("chassis_no_".concat(row), existing_serial_no[row - 1]);
                d.set_value("engine_no_".concat(row), existing_engine_no[row - 1]);
                d.set_value("key_no_".concat(row), existing_key_no[row - 1]);
                d.set_value("color_".concat(row), existing_color[row - 1]);
            }
        }
        //Bind Event to Add Button in Dialog
        d.set_primary_action(__("Save"), function() {
            /*****************/
            args = d.get_values();
            if (!args) return;
            frappe.call({
                method: "mapl_customization.customizations_for_mapl.utils.validate_input_serial",
                args: {
                    "args": d.get_values(),
                    "rows": grid_row.grid_form.fields_dict.received_qty.get_value(),
                    "is_vehicle": grid_row.grid_form.fields_dict['is_vehicle'].value
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
            for (var rows = 1; rows <= grid_row.grid_form.fields_dict.received_qty.get_value(); rows++) {
                result_serial_no = result_serial_no.concat(d.get_value("chassis_no_".concat(rows)), "\n");
                result_engine_no = result_engine_no.concat(d.get_value("engine_no_".concat(rows)), "\n");
                result_key_no = result_key_no.concat(d.get_value("key_no_".concat(rows)), "\n");
                result_color = result_color.concat(d.get_value("color_".concat(rows)), "\n");
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
    });
});
/***************************************************************/
/*              End Dialog On Child Form                       */
/***************************************************************/
