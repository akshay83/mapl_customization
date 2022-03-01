cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
cur_frm.add_fetch('item_code', 'is_electric_vehicle', 'is_electric_vehicle');
frappe.ui.form.on("Purchase Receipt", "items_on_form_rendered", function (frm) {
    // Important Note : Sub Form Fieldname+"_on_form_rendered" would trigger and add
    // The button in child form
    var grid_row = cur_frm.open_grid_row();

    //Set rejected_warehouse as Null, overcome problem of Default Warehouse
    grid_row.grid_form.fields_dict.rejected_warehouse.set_model_value(null);

    // Add Button to Child Form ... Wrap it around the "dialog_result" field
    var $btn = $('<button class="btn btn-sm btn-default" style="background:var(--bg-blue);">' + __("Add Serial No") + '</button>')
        .appendTo($("<div>")
            .css({
                "margin-bottom": "10px",
                "margin-top": "10px"
            })
            .appendTo(grid_row.grid_form.fields_dict.serial_no.$wrapper));

    // Bind a Event to Added Button
    $btn.on("click", function () {
        if (frm.doc.update_stock && grid_row.grid_form.fields_dict.item_code.get_value()) {
            custom.show_custom_insert_dialog(frm, cdt, cdn);
        }
    });
});


frappe.ui.form.on("Purchase Receipt", "items_on_form_rendered", function (frm) {
    var grid_row = frm.open_grid_row();
    //grid_row.grid_form.fields_dict.warehouse.set_model_value(frm.doc.default_accepted_warehouse);
    //Set rejected_warehouse as Null, overcome problem of Default Warehouse
    grid_row.grid_form.fields_dict.rejected_warehouse.set_model_value(null);
});

frappe.ui.form.on("Purchase Receipt", "validate", function (frm) {
    if (frm.doc.set_warehouse !== undefined) {
        frm.doc.items.forEach(function (i) {
            if (i.warehouse == null) {
                i.warehouse = frm.doc.set_warehouse;
            }
        });
    }
});

frappe.ui.form.on("Purchase Receipt Item", "item_code", function (frm, cdt, cdn) {
    setTimeout(function () {
        let doc = null;
        if (frm.open_grid_row() !== undefined) {
            doc = frm.open_grid_row().doc;
        } else {
            doc = locals[cdt][cdn];
        }
        if (frm.doc.update_stock && locals[cdt][cdn].item_code && locals[cdt][cdn].has_serial_no) {
            custom.show_custom_insert_dialog(frm, cdt, cdn);
        }
        if (frm.doc.update_stock && doc.item_code) {
            doc.expense_account = "";
            frm.refresh_field("items");
        }
    }, 500);
});