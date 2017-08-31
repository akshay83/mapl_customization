frappe.listview_settings['Sales Invoice'] = {
	override_all_columns: [
		{
			colspan: 1,
			fieldname: "posting_date"
		},
		{
			colspan: 1,
			fieldname: "letter_head"
		},
		{
			colspan: 1,
			fieldname: "hypothecation"
		},
		{
			colspan: 1,
			fieldname: "grand_total"
		},
	],
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
