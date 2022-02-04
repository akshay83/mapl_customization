frappe.ui.form.on("Accounts Settings", "refresh", function(frm) {
    console.log(frm.doc.rate_check_threshold);
    frappe.db.get_value("Workflow","Sales Invoice Workflow","is_active", function(val)  {
        frm.set_df_property("rate_check_threshold", "hidden", val.is_active == 0);
        frm.set_df_property("check_rate_cumulatively", "hidden", val.is_active == 0);
    });
});
