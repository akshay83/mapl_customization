frappe.provide("frappe");
frappe.provide("custom");

custom.customer_quick_entry = function (doc) {
		var dialog = new frappe.ui.Dialog({
			title: __("Quick Customer Entry"),
			fields: [
				{fieldtype: "Select", fieldname: "customer_type", label: __("Customer Type"), reqd: 1, options: "Company\nIndividual", default: "Individual"},
				{fieldtype: "Link", fieldname: "salutation", label: __("Salutation"), reqd:0, options: "Salutation"},
				{fieldtype: "Data", fieldname: "customer_name", label: __("Customer Name"), reqd: 1},
				{fieldtype: "Select", fieldname: "relation_to", label: __("Relation To"), reqd: 0, options: "\nS/o\nD/o\nW/o\nDIR.", default: ""},
				{fieldtype: "Data", fieldname: "relation_name", label: __("Relation Name"), reqd: 0, hidden: 1},
				{fieldtype: "Data", fieldname: "company_name", label: __("Company Name"), reqd: 0},
				{fieldtype: "Data", fieldname: "tax_id", label: __("Tax ID"), reqd: 0},
				{fieldtype: "Column Break", fieldname: "column_break_2"},
				{fieldtype: "Link", fieldname: "customer_group", label: __("Customer Group"), reqd: 1, options: "Customer Group"},
				{fieldtype: "Link", fieldname: "territory", label: __("Territory"), reqd: 1, options: "Territory"},
				{fieldtype: "Data", fieldname: "pan_no", label: __("PAN No"), reqd: 0},
				{fieldtype: "Data", fieldname: "primary_contact_no", label: __("Primary Contact No"), reqd: 1},
				{fieldtype: "Data", fieldname: "secondary_contact_no", label: __("Secondary Contact No"), reqd: 0},
				{fieldtype: "Data", fieldname: "vehicle_no", label: __("Vehicle No"), reqd: 0},
				{fieldtype: "Section Break", fieldname: "section_break_1"},
				{fieldtype: "Data", fieldname: "billing_address_1", label: __("Billing Address 1"), reqd: 1},
				{fieldtype: "Data", fieldname: "billing_address_2", label: __("Billing Address 2"), reqd: 0},
				{fieldtype: "Data", fieldname: "billing_city", label: __("Billing City"), reqd: 1},
				{fieldtype: "Data", fieldname: "billing_state", label: __("Billing State"), reqd: 0, default: "Madhya Pradesh"},
				{fieldtype: "Link", fieldname: "billing_country", label: __("Billing Country"), reqd: 0, options:"Country"},
				{fieldtype: "Data", fieldname: "billing_phone", label: __("Billing Phone"), reqd: 0},
				{fieldtype: "Data", fieldname: "billing_fax", label: __("Billing Fax"), reqd: 0},
				{fieldtype: "Data", fieldname: "billing_email_id", label: __("Billing Email ID"), reqd: 0},
				{fieldtype: "Data", fieldname: "billing_gst_id", label: __("GST ID"), reqd: 0},
				{fieldtype: "Select", fieldname: "billing_gst_state", label: __("GST State"), reqd: 0, options: " \nAndhra Pradesh\nArunachal Pradesh\nAssam\nBihar\nChandigarh\nChattisgarh\nDadra and Nagar Haveli\nDaman and Diu\nDelhi\nGoa\nGujarat\nHaryana\nHimachal Pradesh\nJammu and Kashmir\nJharkhand\nKarnataka\nKerala\nLakshadweep Islands\nMadhya Pradesh\nMaharashtra\nManipur\nMeghalaya\nMizoram\nNagaland\nOdisha\nPondicherry\nPunjab\nRajasthan\nSikkim\nTamil Nadu\nTelangana\nTripura\nUttar Pradesh\nUttarakhand\nWest Bengal", default: "Madhya Pradesh"},
				{fieldtype: "Column Break", fieldname: "column_break_1"},
				{fieldtype: "Data", fieldname: "shipping_address_1", label: __("Shipping Address 1"), reqd: 0},
				{fieldtype: "Data", fieldname: "shipping_address_2", label: __("Shipping Address 2"), reqd: 0},
				{fieldtype: "Data", fieldname: "shipping_city", label: __("Shipping City"), reqd: 0},
				{fieldtype: "Data", fieldname: "shipping_state", label: __("Shipping State"), reqd: 0},
				{fieldtype: "Link", fieldname: "shipping_country", label: __("Shipping Country"), reqd: 0, options:"Country"},
				{fieldtype: "Data", fieldname: "shipping_phone", label: __("Shipping Phone"), reqd: 0},
				{fieldtype: "Data", fieldname: "shipping_fax", label: __("Shipping Fax"), reqd: 0},
				{fieldtype: "Data", fieldname: "shipping_email_id", label: __("Shipping Email ID"), reqd: 0},
				{fieldtype: "Data", fieldname: "shiping_gst_id", label: __("GST ID"), reqd: 0},
				{fieldtype: "Select", fieldname: "shipping_gst_state", label: __("GST State"), reqd: 0, options: " \nAndhra Pradesh\nArunachal Pradesh\nAssam\nBihar\nChandigarh\nChattisgarh\nDadra and Nagar Haveli\nDaman and Diu\nDelhi\nGoa\nGujarat\nHaryana\nHimachal Pradesh\nJammu and Kashmir\nJharkhand\nKarnataka\nKerala\nLakshadweep Islands\nMadhya Pradesh\nMaharashtra\nManipur\nMeghalaya\nMizoram\nNagaland\nOdisha\nPondicherry\nPunjab\nRajasthan\nSikkim\nTamil Nadu\nTelangana\nTripura\nUttar Pradesh\nUttarakhand\nWest Bengal"},
				{fieldtype: "Check", fieldname: "shipping_preferred", label: __("Is Preferred Shipping Address") }
			]
		});


	//TO HIDE A FIELD IN DIALOG
	var fd = dialog.fields_dict;

	$(fd.company_name.wrapper).toggle(fd.customer_type.get_value()==='Individual')
	$(fd.customer_type.input).change(function() {
		$(fd.company_name.wrapper).toggle(fd.customer_type.get_value()==='Individual');
	});

	fd.relation_to.$input.on("change", function (e) {
		fd.relation_name.df.reqd = this.value != "";
		fd.relation_name.df.hidden = this.value == "";
		fd.relation_name.refresh();
	});


	dialog.set_primary_action(__("Save"), function() {
		args = dialog.get_values();
		if (!args) return;
		frappe.call({
			method:"mapl_customization.customizations_for_mapl.quick_customer.do_quick_entry",
			args : { "args": dialog.get_values() },
			callback: function (r) {
				if (r.message) {
					dialog.hide();
					var inline_doc = r.message;
					if (frappe._from_link) {
  						frappe.ui.form.update_calling_link(inline_doc);
					} else if (custom._customer_called_from != null) { 
						doc.set_value(custom._customer_called_from,inline_doc.name);
						custom.customer_quick_entry.unset_called_from();
					} else {
					  	frappe.set_route("Form", doc.doctype, inline_doc.name);
					}
				}
			}
		});
	});

	custom.customer_quick_entry.set_default_values(dialog, dialog.fields);
	dialog.show();
        //$("div").find(".modal-dialog").css({"line-height":".5"});
        //$("div[class*='modal-dialog']").find(".control-label").css({"font-size":"12px","font-weight":"500","margin-bottom":"1px"});
        //$("div").find(".modal-dialog").attr("style","font-size: 8px !important");
        //$("div[class*='modal-dialog']").find(".control-input").css({"line-height":"1","font-size":"10px"});
}

custom.customer_quick_entry.set_called_from = function(from) {
	custom._customer_called_from = from;
}

custom.customer_quick_entry.unset_called_from = function() {
	custom._customer_called_from = null;
}

custom.customer_quick_entry.set_default_values = function(doc, docfields) {
	for(var fid=0;fid<docfields.length;fid++) {
		var f = docfields[fid];
		var v;
		try {
			v = frappe.model.get_default_value(f, {doctype: 'Customer'}, null);
		} catch (err) {
		}
		if(v) {
			doc.set_value(f.fieldname, v);
		} else if(f.fieldtype == "Select" && f.options && typeof f.options === 'string'
					&& !in_list(["[Select]", "Loading..."], f.options)) {
				doc.set_value(f.fieldname,f.options.split("\n")[0]);
		}
	}
}
