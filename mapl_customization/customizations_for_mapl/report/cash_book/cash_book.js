frappe.query_reports['Cash Book'] = {
        "filters": [
                {
                        "fieldname":"from_date",
                        "label":__("From Date"),
                        "fieldtype": "Date",
                        "default": get_today()
                },
                {
                        "fieldname":"to_date",
                        "label":__("To Date"),
                        "fieldtype": "Date",
                        "default": get_today()
                },
                {
                        "fieldname":"let",
                        "label":__("Letter Head"),
                        "fieldtype": "Link",
                        "options": "Letter Head",
                        "default": "%%"
                }

        ],
	"formatter":function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);
		if (column.fieldname != "posting_date") {
			value = "<div style='text-align:right;'>" + value + "</div>";
		}
		return value;
	}        
}
