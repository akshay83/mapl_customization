frappe.listview_settings['Payment Entry'] = {
	//add_columns: ["payment_type", "paid_amount", "mode_of_payment", "posting_date"],
	//add_fields: ["payment_type", "paid_amount", "mode_of_payment", "posting_date"],
	override_all_columns: [
		{
			colspan: 1,
			fieldname: "posting_date"
		},
		{
			colspan: 4,
			fieldname: "party_name"
		},
		{
			colspan: 1,
			fieldname: "mode_of_payment"
		},
		{
			colspan: 1,
			fieldname: "payment_type"
		},
		{
			colspan: 1,
			fieldname: "paid_amount"
		}
	],
	//hide_activity: 1,
	//hide_name_column: 1,
	//selectable: 0,
	//hide_list_view_items:1,
	get_indicator: function(doc) {
		var stat = "Submitted";
		var color = "green";
		if (doc.docstatus == 0) {
			stat = "Draft";
			color = "darkgrey";
		} else if (doc.docstatus == 1) {
			stat = "Submitted";
			color = "green";
		} else if (doc.docstatus == 2) {
			stat = "Cancelled";
			color = "red";
		}
		return [stat, color, "status,=," + stat];
	}
};
