frappe.query_reports['GFK Sales Report'] = {
	"filters": [
		{
			"fieldname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": get_today()
		},
		{
			"fieldname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": get_today()
		},
		{
			"fieldname": "brands_array",
			"hidden": 1,
			"fieldtype": "Data",
			"default": "Samsung"
		},
		{
			"fieldname": "brands",
			"label": __("Brands"),
			"fieldtype": "MultiSelectList",
			"options": "Brand",
			get_data: function (txt) {
				return frappe.db.get_link_options('Brand', txt);
			},
			on_change: async function () {
				let brands = await frappe.query_report.get_filter_value('brands');
				frappe.query_report.set_filter_value('brands_array', brands.join("|"));
			},
		},
	]
}