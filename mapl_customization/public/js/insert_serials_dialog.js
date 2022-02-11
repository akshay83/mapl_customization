custom.show_custom_insert_dialog = function (frm, dt, dn) {
    let doc = null;
    let current_qty = 1;
    let is_vehicle = 0;
    let is_electric_vehicle = 0;
    let existing_serial_no = null;
    let existing_engine_no = "";
    let existing_key_no = "";
    let existing_color = "";

    if (frm.open_grid_row() !== undefined) {
        doc = frm.open_grid_row().doc;
    } else {
        doc = locals[dt][dn];
    }
    if (doc.qty !== undefined) current_qty = doc.qty;
    is_electric_vehicle = doc.is_electric_vehicle;
    is_vehicle = doc.is_vehicle;
    if (doc.serial_no !== undefined && doc.serial_no != "") {
        existing_serial_no = doc.serial_no.split("\n");
        if (is_vehicle) {
            existing_engine_no = doc.engine_nos.split("\n");
            existing_key_no = doc.key_nos.split("\n");
            existing_color = doc.color.split("\n");
        }
    }

    let data = [];
    if (existing_serial_no != null) {
        for (var row = 0; row < existing_serial_no.length; row++) {
            data.push({
                "serial_no": existing_serial_no[row],
                "engine_no": existing_engine_no[row],
                "key_no": existing_key_no[row],
                "color": existing_color[row]
            });
        }
    }

    let fields = [];
    fields.push(
        {
            label: "Item",
            fieldtype: "Data",
            fieldname: "item_code",
            read_only: 1,
            default: doc.item_code
        },
        {
            fieldtype: "Column Break"
        },
        {
            label: "Warehouse",
            fieldtype: "Link",
            options: "Warehouse",
            fieldname: "warehouse",
            reqd: 1,
            default: doc.warehouse === undefined ? frm.doc.set_warehouse : doc.warehouse
        },
        {
            fieldtype: "Section Break",
        },
        {
            fieldname: "serial_details",
            fieldtype: "Table",
            fields: [
                {
                    fieldtype: "Data",
                    label: "Serial No",
                    fieldname: "serial_no",
                    in_list_view: 1,
                    reqd: 1
                },
                {
                    fieldtype: "Data",
                    label: is_electric_vehicle == false ? "Engine No" : "Motor No",
                    fieldname: "engine_no",
                    in_list_view: 1,
                    reqd: is_electric_vehicle == 0 ? 1 : 0,
                    hidden: is_vehicle == 0 ? 1 : 0
                },
                {
                    fieldtype: "Data",
                    label: "Key No",
                    fieldname: "key_no",
                    in_list_view: 1,
                    reqd: is_electric_vehicle == 0 ? 1 : 0,
                    hidden: is_vehicle == 0 ? 1 : 0
                },
                {
                    fieldtype: "Data",
                    label: "Color",
                    fieldname: "color",
                    in_list_view: 1,
                    hidden: is_vehicle == 0 ? 1 : 0
                }
            ],
            data: data,
            get_data: function () {
                return data;
            }
        }
    );

    let d = new frappe.ui.Dialog({
        title: __("Add Serial No"),
        fields
    });

    let validate_child = function (args) {
        for (var i = 0; i < args.serial_details.length; i++) {
            if (!args.serial_details[i].serial_no) { frappe.msgprint("Check Serial/Chassis No At Row " + (i+1)); return false; }
            if (is_vehicle == 1) {
                if (is_electric_vehicle == 0 && !args.serial_details[i].engine_no) { frappe.msgprint("Check Engine/Motor No At Row " + (i+1)); return false; }
                if (is_electric_vehicle == 0 && !args.serial_details[i].key_no) { frappe.msgprint("Check Key No At Row " + (i+1)); return false; }
                if (!args.serial_details[i].color) { frappe.msgprint("Check Color At Row " + (i+1)); return false; }
            }
        }
        return true;
    }

    //Bind Event to Add Button in Dialog
    d.set_primary_action(__("Insert"), function () {
        var args = d.get_values();
        if (!args) return;
        if (!validate_child(args)) return;

        var result_serial_no = "";
        var result_engine_no = "";
        var result_key_no = "";
        var result_color = "";
        for (var rowno = 0; rowno < args.serial_details.length; rowno++) {
            var carr_retu = "\n"
            if (rowno == args.serial_details.length - 1) {
                carr_retu = "";
            }
            result_serial_no = result_serial_no.concat(args.serial_details[rowno].serial_no, carr_retu);
            result_engine_no = result_engine_no.concat(args.serial_details[rowno].engine_no, carr_retu);
            result_key_no = result_key_no.concat(args.serial_details[rowno].key_no, carr_retu);
            result_color = result_color.concat(args.serial_details[rowno].color, carr_retu);
        }

        d.hide();
        doc.warehouse = args.warehouse;
        doc.serial_no = result_serial_no;
        doc.engine_nos = result_engine_no;
        doc.key_nos = result_key_no;
        doc.color = result_color;
        doc.qty = args.serial_details.length;
        frm.refresh_field("items");
    });
    d.$wrapper.find('.modal-content').css("width", "950px");
    d.$wrapper.find('.modal-dialog').css("position", "absolute");
    d.$wrapper.find('.modal-dialog').css("left", "20%");

    d.show();
}