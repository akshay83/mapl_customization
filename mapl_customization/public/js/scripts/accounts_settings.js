frappe.ui.form.on("Accounts Settings", "refresh", function(frm) {
    frappe.db.get_value("Workflow","Sales Invoice Workflow","is_active", function(val)  {
        frm.set_df_property("standard_sales_invoice_workflow_options", "hidden", val.is_active == 0);
    });
});