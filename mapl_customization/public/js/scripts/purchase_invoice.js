cur_frm.add_fetch('item_code', 'is_vehicle', 'is_vehicle');
cur_frm.add_fetch('item_code', 'is_electric_vehicle', 'is_electric_vehicle');

frappe.ui.form.on("Purchase Invoice", "onload_post_render", async function (frm) {
    //Set Default Warehouse
    if (frm.is_new() !== undefined && frm.is_new()) {
        frm.set_value("set_warehouse", await custom.get_default_warehouse());
        frm.refresh_field("set_warehouse");
    }
});

frappe.ui.form.on("Purchase Invoice", "items_on_form_rendered", function (frm, cdt, cdn) {
    let grid_row = frm.open_grid_row();
    // Add Button to Child Form ... Wrap it around the "dialog_result" field
    let $btn = $('<button class="btn btn-sm btn-default" style="background:var(--bg-blue);">' + __("Add Serial No") + '</button>')
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
    setTimeout(async function () {
        let doc = null;
        if (frm.open_grid_row() !== undefined) {
            doc = frm.open_grid_row().doc;
        } else {
            doc = locals[cdt][cdn];
        }
        if (frm.doc.update_stock && doc.item_code && doc.has_serial_no) {
            custom.show_custom_insert_dialog(frm, cdt, cdn);
        }
    }, 500);
});

frappe.ui.form.on("Purchase Invoice", "refresh", function (frm) {
    setTimeout(function () {
        if (frm.doc.__islocal !== undefined && frm.doc.__islocal) {
            console.log("Onload Purchase Invoice");
            frappe.db.get_single_value("Global Defaults", "disable_rounded_total").then(val => {
                frm.doc.disable_rounded_total = val;
                frm.refresh_field('disable_rounded_total');
            });
        }
    },2000);
});