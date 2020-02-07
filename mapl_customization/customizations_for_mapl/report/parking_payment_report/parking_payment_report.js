frappe.query_reports['Parking Payment Report'] = {
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
		}
	]
}
