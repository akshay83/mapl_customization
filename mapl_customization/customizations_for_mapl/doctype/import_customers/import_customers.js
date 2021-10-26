// Copyright (c) 2021, Akshay Mehta and contributors
// For license information, please see license.txt

function custom_import_customer_make_upload(frm) {
	var $wrapper = $(frm.fields_dict.upload_html.wrapper).empty();
	new frappe.ui.FileUploader({
		wrapper: $wrapper,
		method: 'mapl_customization.customizations_for_mapl.doctype.import_customers.import_customers.upload'
	});
}

frappe.ui.form.on('Import Customers', {
	refresh: function(frm) {
		frm.disable_save();
		custom_import_customer_make_upload(frm);

		$(frm.fields_dict.help.wrapper).append(`
				<h2>Upload a .csv file having Doctype-fieldname as column heading. For instance:</h2>
				<p>1. "Customer-name"</p>
				<p>2. "Customer-customer_name"</p>
				<p>3. "Customer-customer_group"</p>
				<p>4. "Address-address_line1"</p>
				<p>5. "Contact-phone_no"</p>
				<p>...</p>
				`);

		frm.refresh_field('help');

	}
});
