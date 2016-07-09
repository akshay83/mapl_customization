frappe.provide("frappe");

var orig_mk_control = frappe.ui.form.make_control;

frappe.ui.form.make_control = function(opts) {
    var control_name = "Control"+opts.df.fieldtype.replace(/ /g,"");
    //console.log(control_name);
    if (control_name == "ControlVolatile") {
        return new frappe.ui.form["ControlReadOnly"](opts);
    }    
    return orig_mk_control(opts);
};
