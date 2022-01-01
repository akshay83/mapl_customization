frappe.ui.form.on("Stock Problem", "refresh", function (frm) {
    frm.toggle_enable("status", frm.doc.status === "Open")
});
frappe.ui.form.on("Stock Problem", "status", function (frm) {
    frm.set_df_property("resolution", "reqd", frm.doc.status == "Closed");
});

frappe.ui.form.on("Stock Problem", "setup", function (frm) {
    frm.set_query("customer", function (doc) {
        return {
            query: "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
        }
    });
    frm.set_query("serial_no", function(doc) {
        let filters = {};
        if (doc.item && doc.warehouse) {
            console.log(doc.item);
            filters = {
                'item_code': doc.item,
                'warehouse': doc.warehouse
            }
        }
        return {
            filters: filters
        }    
    });
});
frappe.ui.form.on("Stock Problem", "is_customer_return", function (frm) {
    frm.set_df_property("customer", "reqd", frm.doc.is_customer_return == 1);
    frm.set_df_property("returned_on", "reqd", frm.doc.is_customer_return == 1);
    frm.refresh_field("hypothecation");
});