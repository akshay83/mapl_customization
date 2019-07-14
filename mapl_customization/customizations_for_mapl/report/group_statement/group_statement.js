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
			"get_query": function() {
				var cg = frappe.query_report_filters_by_name.customer_group;
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
	"formatter":function (row, cell, value, columnDef, dataContext, default_formatter) {
		value = default_formatter(row, cell, value, columnDef, dataContext);

		if (dataContext.posting_date == null && ['Opening Balance', 'Closing Totals', 'Balance'].indexOf(dataContext.voucher_type) == -1 && columnDef.id=="Voucher Ref") {
			value = "<span style='font-weight:bold'>" + value + "</span>";
		}

		if (dataContext.voucher_type == 'Balance' && parseFloat(dataContext.debit) > 0 && columnDef.id == "Debit") {
			value = "<span style='color:green!important;font-weight:bold'>" + value + "</span>";
		} else if (dataContext.voucher_type == 'Balance' && parseFloat(dataContext.credit) > 0 && columnDef.id == "Credit") {
			value = "<span style='color:red!important;font-weight:bold'>" + value + "</span>";
		}

		if (dataContext.voucher_type == 'Balance' && columnDef.id == "Type") {
			value = "<span style='font-weight:bold'>" + value + "</span>";
		}

		if (columnDef.id == "Running Balance") {
			value = "<div style='text-align:right;'>" + value + "</div>";
		}
		return value;
	}
}
