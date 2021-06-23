frappe.ui.form.on("Customer","refresh", function(frm) {
	if (frm.doc.__islocal) {
		frm.add_custom_button(__('Quick Entry'), function() {
			custom.customer_quick_entry(frm);
		});
		custom.customer_quick_entry(frm);
	}

        custom._get_party_balance_in_drcr('Customer', frm.doc.name,
		frappe.defaults.get_user_default("company"), function(result) {
				frm.doc.current_balance=result;
				refresh_field("current_balance");
	});
	if (!frm.doc.__islocal) {
		$.each($('.frappe-control[data-fieldname=address_html] > .address-box'),function(key, value) {
			//$($(value).find('p:not([class])')[0]).append('<span class="btn btn-default btn-xs pull-right upd-button">Update</span>');
			let button = $('<span class="btn btn-default btn-xs pull-right upd-button">Update</span>');
			$(value).append(button);
			let name = $($(value).find('a')).attr('href');
			name = name.substring(name.lastIndexOf('/')+1).replace(/%20/g, " ");
			button.on("click", function() {
				custom.update_address(name);
				frm.refresh();
			});
		});
	}
});

frappe.ui.form.on("Customer","refresh", function(frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Update Customer Name'), function() {
			if (cur_frm.is_dirty()) {
				frappe.msgprint(__("Please Save Changes Before Updating"));
				return;
			}
			frappe.call({
				method: "mapl_customization.customizations_for_mapl.update_customer_name.update_customer_name",
				args: {
					"customer": frm.doc.name,
					"customer_name": frm.doc.customer_name
		                },
	         		callback: function(r) {
					if(!r.exc) {
						frappe.msgprint(__("Customer Name Updated Across All Relevant Documents"));
					}
				}
			});
		}, 'Actions');
	}

	frm.remove_custom_button('Accounting Ledger');
	frm.remove_custom_button('Accounts Receivable');
	frm.add_custom_button('Accounting Ledger', function() {
		frappe.set_route('query-report', 'General Ledger',
			{party_type:'Customer', party:frm.doc.name});
	}, 'View');
	frm.add_custom_button(__('Accounts Receivable'), function() {
		frappe.set_route('query-report', 'Accounts Receivable', {customer:frm.doc.name});
	}, 'View');

	frm.remove_custom_button('Send GST Update Reminder');
	frm.add_custom_button('Send GST Update Reminder', () => {
		return new Promise((resolve) => {
			return frappe.call({
				method: 'erpnext.regional.doctype.gst_settings.gst_settings.send_gstin_reminder',
				args: {
					party_type: frm.doc.doctype,
					party: frm.doc.name,
				}
			}).always(() => { resolve(); });
		});
	}, 'Actions');
});

frappe.ui.form.on("Customer", "relation_to", function (frm) {
         cur_frm.set_df_property("relation_name", "reqd", frm.doc.relation_to!='');
         cur_frm.refresh_field("relation_name");
});

function custom_update_button(frm) {

};
