frappe.listview_settings["Employee"] = {
    onload: function(listview) {
      listview.page.add_menu_item('Generate Regn. Codes', () => {
        //--DEBUG--console.log("Employee List Button Clicked");
        frappe.dom.freeze("Working","custom_freeze_class");
        const random_function = function(min, max) {
            return Math.floor(Math.random() * (max - min + 1)) + min;
        };
        let args = {
            fields: ['name'], 
            filters: { 
                "status": "Active"
            },
            limit: 500
        };
        frappe.db.get_list('Employee', args).then(val => {
            //--DEBUG--console.log(val.length);
            for (d = 0; d<val.length; d++) {
                frappe.db.set_value("Employee", val[d].name, "registration_code", random_function(100001,999999));                
            }
            frappe.msgprint("Generated Registration Codes for All Active Employees");
        });
        frappe.dom.unfreeze();        
      });
    }
  };