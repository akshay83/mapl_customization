cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
cur_frm.add_fetch('item_code', 'is_electric_vehicle', 'is_electric_vehicle');

frappe.ui.form.on("Purchase Invoice", "items_on_form_rendered", function (frm, cdt, cdn) {
    var grid_row = frm.open_grid_row();
    // Add Button to Child Form ... Wrap it around the "dialog_result" field
    var $btn = $('<button class="btn btn-sm btn-default" style="background:var(--bg-blue);">' + __("Add Serial No") + '</button>')
        .appendTo($("<div>")
            .css({
                "margin-bottom": "10px",
                "margin-top": "10px"
            })
            .appendTo(grid_row.grid_form.fields_dict.serial_no.$wrapper));
    $btn.on("click", function () {
        if (frm.doc.update_stock && grid_row.grid_form.fields_dict.item_code.get_value()) {
            custom.show_custom_insert_dialog(frm, cdt, cdn);
        }
    });
});

frappe.ui.form.on("Purchase Invoice", "items_on_form_rendered", function (frm) {
    var grid_row = frm.open_grid_row();
    //grid_row.grid_form.fields_dict.warehouse.set_model_value(frm.doc.default_accepted_warehouse);
    //Set rejected_warehouse as Null, overcome problem of Default Warehouse
    grid_row.grid_form.fields_dict.rejected_warehouse.set_model_value(null);
});

frappe.ui.form.on("Purchase Invoice", "validate", function (frm) {
    if (frm.doc.set_warehouse !== undefined) {
        frm.doc.items.forEach(function (i) {
            if (i.warehouse == null) {
                i.warehouse = frm.doc.set_warehouse;
            }
        });
    }
    if (frm.doc.update_stock == 0) {
        frappe.msgprint("Update Stock not Ticked. Please Verify Before Continuing");
    }
});

frappe.ui.form.on("Purchase Invoice Item", "item_code", function (frm, cdt, cdn) {
    if (frm.doc.update_stock && locals[cdt][cdn].item_code) {
        custom.show_custom_insert_dialog(frm, cdt, cdn);
    }
});