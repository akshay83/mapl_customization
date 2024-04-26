// Copyright (c) 2024, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Sales and Stock Report"] = {
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
                        "fieldname":"letter_head",
                        "label":__("Letter Head"),
                        "fieldtype": "Select",
                        "options": "All\nVijay Nagar\nGeeta Bhawan\nRanjeet Hanuman",
                        "default": "Geeta Bhawan"
                },
				{
					"fieldname": "brands_array",
					"hidden": 1,
					"fieldtype": "Data",
					"default": ""
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
                {
                        "fieldname":"item_group",
                        "label":__("Item Group"),
                        "fieldtype": "Link",
                        "options": "Item Group"
                },
                {
                        "fieldname":"show_draft",
                        "label":__("Show Entries"),
                        "fieldtype": "Select",
                        "options": "Submitted\nInclude Draft",
                        "default": "Submitted"
                }
        ]
};
