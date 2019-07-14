// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Ledger Statement"] = {
	"filters": [
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.add_months(frappe.datetime.get_today(), -1),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1,
			"width": "60px"
		},
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account"
		},
		{
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type"
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var party_type = frappe.query_report_filters_by_name.party_type.get_value();
				var party = frappe.query_report_filters_by_name.party.get_value();
				if(party && !party_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return party_type;
			},
			"on_change": function() {
				var party_type = frappe.query_report_filters_by_name.party_type.get_value();
				var party = frappe.query_report_filters_by_name.party.get_value();
				if(!party_type || !party) {
					frappe.query_report_filters_by_name.party_name.set_value("");
					return;
				}

				var fieldname = party_type.toLowerCase() + "_name";
				frappe.db.get_value(party_type, party, fieldname, function(value) {
					frappe.query_report_filters_by_name.party_name.set_value(value[fieldname]);
				});
			},
		},
		{
			"fieldname":"party_name",
			"label": __("Party Name"),
			"fieldtype": "Data",
			"read_only": 1
		}
	]
}
