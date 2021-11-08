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
		let sample_data = `
		<div style="font-size:10px;font-family:monospace;">
		<table border="1">
		<tr><th>Customer-name</th><th>Customer-customer_name</th><th>Address-address_line1</th><th>Address-address_line2</th><th>Address-city</th><th>Address-state</th><th>Address-gstin</th><th>Address-gst_state</th><th>Address-address_type</th><th>Contact-phone_nos</th><th>Contact-email_id</th></tr>
		<tr><td>CUST-00004</td><td>Govind Maurya</td><td> 38/39, ADARSH MOULIK NAGAR </td><td> VIJAY NAGAR ,  </td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>8962000626</td><td></td></tr>
		<tr><td>CUST-00004</td><td>Govind Maurya</td><td>22 SHYAM NAGAR ANNEX </td><td></td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>8962000626</td><td></td></tr>
		<tr><td>CUST-00040</td><td>ABDUL WAZID KHAN</td><td> House.No.R-285 , Mahalaxmi Nagar </td><td> Nr. Bombay Hospital ,  </td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>9893301885</td><td></td></tr>
		<tr><td>CUST-00040</td><td>ABDUL WAZID KHAN</td><td>D-33 HIG COLONY BEHIND SHOPPING COMPLEX</td><td>NEAR DR. CHHABRA CLINIC </td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>9893301885</td><td></td></tr>
		<tr><td>CUST-01057</td><td>ANIL AGRAWAL</td><td> A-1 704, MAPLE WOODS PIPLIYA </td><td>KUMAR NIPANIYA MAIN ROAD</td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td> 8878819000,8878719000 </td><td></td></tr>
		<tr><td>CUST-01066</td><td>ANIL AGRWAL</td><td> A-01, 704, MAPLE WOODS PIPLIYA </td><td>KUMAR NIPANIYA MAN RAOD </td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td> 8878819000,8878719000 </td><td></td></tr>
		<tr><td>CUST-06449</td><td>DR. A.K. JINSIWALE</td><td>137-PHADNIS COLONY</td><td>NR. SANJEEVNI NURSING HOME </td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>9827036973</td><td></td></tr>
		<tr><td>CUST-06449</td><td>DR. A.K. JINSIWALE</td><td>ORTHOPEDIC SURGEON</td><td></td><td>Indore</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>9827036973</td><td></td></tr>
		<tr><td>CUST-11328</td><td>A.K. JINSIWALE</td><td>A/8 MIG B/H SANJIVNI NURSINGH HOME </td><td></td><td>INDORE</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td>9827027222</td><td></td></tr>
		<tr><td>CUST-16133</td><td>GAURAV REWAL</td><td> 35, NEER NAGAR, NEAR MAYANK </td><td>BLUE WATER PARK</td><td>INDORE</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td> 9294677111,9893677111 </td><td>GAURAV.REWAL224@GMAIL.COM</td></tr>
		<tr><td>CUST-16133</td><td>GAURAV REWAL</td><td> 402, B-BLOCK, SAHIL SIDHI VINAYAK </td><td>NEAR MAYANK BLUE WATER PARK</td><td>INDORE</td><td>MADHYA PRADESH</td><td>23ABCHF2422J1ZS</td><td>Madhya Pradesh</td><td>Billing</td><td> 9294677111,9893677111 </td><td>GAURAV.REWAL224@GMAIL.COM</td></tr>
		<tr><td>CUST-16148</td><td>RAKESH JAISWAL</td><td> 103, BLOCK-C, EWS, BUILDING, </td><td> SINGAPUR TOWNSHIP, TALAWALI CHANDA </td><td>INDORE</td><td>Madhya Pradesh</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td> 9039350464,9039215178 </td><td>RRAKESHJAISWAL93@GMAIL.COM</td></tr>
		<tr><td>CUST-16148</td><td>RAKESH JAISWAL</td><td> BLOCK C , 103 EWS FLAT </td><td>SINGAPURE TOWNSHIP INDORE</td><td>INDORE</td><td>MADHYA PRADESH</td><td></td><td>Madhya Pradesh</td><td>Billing</td><td> 9039350464,9039215178 </td><td>RRAKESHJAISWAL93@GMAIL.COM</td></tr>
		</table>		
		</div>
		`;
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
				<h2>Sample Data</h2>				
				`+sample_data);

		frm.refresh_field('help');

	}
});
