frappe.ui.form.on("Bank Detail", "refresh", function(frm) {
	frm.page.add_menu_item(__('Send SMS'), function() { 
			BankSMSManager(frm.doc);
	});
});

function BankSMSManager(doc) {
	var me = this;
	this.setup = function() {
    	var default_msg = "Bank Name:"+doc.bank_name+"\n"+
        				"Acc Name:"+doc.account_holder_name+"\n"+
                        "Acc No:"+doc.account_number+"\n"+
                        "IFSC:"+doc.ifsc_code+"\n"+
                        "Branch:"+doc.branch;
		this.show(default_msg);
	};

	this.show = function(message) {
		this.message = message;
		me.show_dialog();
	}
	this.show_dialog = function() {
		if(!me.dialog)
			me.make_dialog();
		me.dialog.set_values({
			'message': me.message
		})
		me.dialog.show();
	}
	this.make_dialog = function() {
		var d = new frappe.ui.Dialog({
			title: 'Send SMS',
			width: 400,
			fields: [
				{fieldname:'number', fieldtype:'Data', label:'Mobile Number', reqd:1},
				{fieldname:'message', fieldtype:'Text', label:'Message', reqd:1},
				{fieldname:'send', fieldtype:'Button', label:'Send'}
			]
		})
		d.fields_dict.send.input.onclick = function() {
			var btn = d.fields_dict.send.input;
			var v = me.dialog.get_values();
			if(v) {
				$(btn).set_working();
				frappe.call({
					method: "erpnext.setup.doctype.sms_settings.sms_settings.send_sms",
					args: {
						receiver_list: [v.number],
						msg: v.message
					},
					callback: function(r) {
						$(btn).done_working();
						if(r.exc) {msgprint(r.exc); return; }
						me.dialog.hide();
					}
				});
			}
		}
		this.dialog = d;
	}
	this.setup();
}
