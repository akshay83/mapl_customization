frappe.query_reports['Daily Collection Report'] = {
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
			"default": "Vijay Nagar"
		},
		{
			"fieldname":"mop",
			"label":__("Mode of Payment"),
			"fieldtype": "Link",
			"options": "Mode of Payment",
			"default": "%%"
		}
	]
}
