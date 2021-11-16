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
	refresh: function (frm) {
		frm.disable_save();
		custom_import_customer_make_upload(frm);
		$(frm.fields_dict.help.wrapper).append(`
				<h2>Upload a .csv file having Doctype-fieldname as column heading. For instance:</h2>
				<p>1. "Customer-name"</p>
				<p>2. "Customer-customer_name"</p>
				<p>3. "Customer-customer_group"</p>
				<p>4. "Address-address_line1"</p>
				<p>5. "Contact-phone"</p>
				<p>6. "Contact-email_id"</p>
				<p>...</p>
				<p>Contact-phone can have a Single Phone No </p>
				<p>Can also include a Column "Contact-phone_nos" having multiple Phone Numbers seperated by ',' </p>
				<h3>No More use of this Page/Doc, Just kept it for reference</h3>`);

		frm.refresh_field('help');

	}
});
