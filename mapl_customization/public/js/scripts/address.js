let gst_fetch_button_inserted = false;
frappe.ui.form.on("Address", "refresh", function (frm) {
	if (!frm.doc.__islocal && !cur_frm.is_dirty()) {
		frm.add_custom_button(__('Update Address'), function () {
			custom.update_address(frm);
		}, 'Actions');
	}
	if (!gst_fetch_button_inserted) {
		let button = $('<div style="float:left;margin-top:20px;margin-left:15px;"><span class="btn btn-default btn-xs pull-right upd-button">Fetch GSTIN Details</span></div><div style="clear:both;"></div>');
		$('.frappe-control[data-fieldname=gstin]').find('.control-input-wrapper').css({ 'width': '300px', 'float': 'left' });
		$('.frappe-control[data-fieldname=gstin]').find('.form-group').append(button);
		button.on("click", async function () {
			await custom.setGSTINDetails(frm.get_field("gstin").get_value(), frm, {
				"address_line_1": "address_line1",
				"address_line_2": "address_line2",
				"pincode": "pincode",
				"city": "city",
				"state": "state",
				"gst_state": "gst_state"
			});
		});
		gst_fetch_button_inserted = true;
	}
});