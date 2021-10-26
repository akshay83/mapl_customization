// Copyright (c) 2016, Akshay Mehta and contributors
// For license information, please see license.txt
/* eslint-disable */

frappe.query_reports["Group Statement"] = {
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
			"fieldname":"party_type",
			"label": __("Party Type"),
			"fieldtype": "Link",
			"options": "Party Type",
			"hidden": 0,
			"default": "Customer",
			on_change: function(frm, doc) {
				var cg = frappe.query_report_filters_by_name.customer_group;
				var party_type = frm.get_values().party_type;
				if (party_type != 'Customer') cg.set_value(null);
				$(cg.wrapper).toggle(party_type==='Customer');
			}
		},
		{
			"fieldname":"customer_group",
			"label":"Customer Group",
			"fieldtype": "Link",
			"options": "Customer Group",
			"hidden": 0,
		},
		{
			"fieldname":"party",
			"label": __("Party"),
			"fieldtype": "Dynamic Link",
			"get_options": function() {
				var party_type = frappe.query_report.get_filter_value('party_type');
				var party = frappe.query_report.get_filter_value('party');
				if(party && !party_type) {
					frappe.throw(__("Please select Party Type first"));
				}
				return party_type;
			},
			"on_change": function() {
				var party_type = frappe.query_report.get_filter_value('party_type');
				var party = frappe.query_report.get_filter_value('party');
				if(!party_type || !party) {
					frappe.query_report.set_filter_value('party_name','');
					return;
				}

				var fieldname = party_type.toLowerCase() + "_name";
				frappe.db.get_value(party_type, party, fieldname, function(value) {
					frappe.query_report.set_filter_value('party_name',value[fieldname]);
				});
			},
			"get_query": function() {
				var cg = frappe.query_report.get_filter_value('customer_group');
				if (cg.value != null) {
					//console.log(cg.value);
					return {
						filters: { 'customer_group': cg.value }
					}
				}
				return;
			}
		},
		{
			"fieldname":"party_name",
			"label": __("Party Name"),
			"fieldtype": "Data",
			"read_only": 1
		}
	],
	"formatter":function (value, row, column, data, default_formatter) {
		value = default_formatter(value, row, column, data);

		if (data.posting_date == null && ['Opening Balance', 'Closing Totals', 'Balance'].indexOf(data.voucher_type) == -1 && column.fieldname=="voucher_ref") {
			value = "<span style='font-weight:bold'>" + value + "</span>";
		}

		if (data.voucher_type == 'Balance' && parseFloat(data.debit) > 0 && column.fieldname == "debit") {
			value = "<span style='color:green!important;font-weight:bold'>" + value + "</span>";
		} else if (data.voucher_type == 'Balance' && parseFloat(data.credit) > 0 && column.fieldname == "credit") {
			value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
		}

		if (data.voucher_type == 'Balance' && column.fieldname == "type") {
			value = "<span style='font-weight:bold'>" + value + "</span>";
		}

		if (column.fieldname == "running") {
			value = "<div style='text-align:right;'>" + value + "</div>";
		}
		return value;
	}
}
