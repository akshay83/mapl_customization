frappe.ui.form.on("Loan", "refresh", function (frm) {
    frappe.db.get_single_value("Payroll Settings", "simplify_employee_loan_repayment").then((value) => {
        if (value === 1) {
            if (["Sanctioned", "Partially Disbursed"].includes(frm.doc.status) && frm.doc.docstatus == 1) {
                frm.add_custom_button('Create Journal Entry', function () {
                    custom.create_loan_jv(frm);
                }, __('Create'));
            }
        }
    });
});

custom.create_loan_jv = function (frm) {
    frappe.call({
        method: "mapl_customization.customizations_for_mapl.utils.create_loan_disbursal_jv",
        args: {
            "doc": frm.doc
        },
        callback: function (r) {
            if (r.message) {
                var doc = frappe.model.sync(r.message)[0];
                frappe.set_route("Form", doc.doctype, doc.name);
            }
        }
    });
};