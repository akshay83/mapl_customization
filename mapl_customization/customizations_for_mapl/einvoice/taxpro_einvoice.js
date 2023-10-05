erpnext.setup_einvoice_actions = (doctype) => {
	frappe.ui.form.on(doctype, {
		async refresh(frm) {
			//--DEBUG--console.log("TaxPro Overriden");
			if (frm.doc.docstatus == 2) return;
			
			const einvoice_enabled = await frappe.db.get_single_value('E Invoice Settings', 'enable');
			if (!einvoice_enabled) return;

			const invoice_eligible = await custom.einvoice_eligibility(frm.doc);
			//--DEBUG--console.log(invoice_eligible);
			//if (!invoice_eligible) return;

			let wf = await custom.is_workflow_active_on("Sales Invoice");

			const { doctype, irn, irn_cancelled, ewaybill, eway_bill_cancelled, name, __unsaved } = frm.doc;

			const add_custom_button = (label, action) => {
				if (!frm.custom_buttons[label]) {
					frm.add_custom_button(label, action, __('E Invoicing'));
				}
			};

			if (invoice_eligible && !irn && !__unsaved) {
				const action = () => {
					if (frm.doc.__unsaved) {
						frappe.throw(__('Please save the document to generate IRN.'));
					}
					frappe.call({
						method: 'erpnext.regional.india.e_invoice.utils.get_einvoice',
						args: { doctype, docname: name },
						freeze: true,
						callback: (res) => {
							const einvoice = res.message;
							_custom_show_einvoice_preview(frm, einvoice);
						}
					});
				};
				let negative_check = await custom.check_if_sales_invoice_will_result_in_negative_stock(frm.doc);
				let hsn_code_length_check = await custom.check_sales_invoice_hsn_length(frm.doc);
				if ((!wf || (wf && frm.doc.workflow_state == 'Approved')) && !(negative_check.result || hsn_code_length_check.result)) {
					add_custom_button(__("Generate IRN - Taxpro"), action);
				}
			}
			//--DEBUG--console.log(irn, !irn_cancelled, !ewaybill);
			if (invoice_eligible && irn && !irn_cancelled && !ewaybill) {
				const action = () => {
					const d = new frappe.ui.Dialog({
						title: __("Cancel IRN"),
						fields: _custom_cancel_fields,
						primary_action: function() {
							const data = d.get_values();
							frappe.call({
								method: 'mapl_customization.customizations_for_mapl.einvoice.taxpro_einvoice.cancel_irn',
								args: {
									doctype,
									docname: name,
									irn: irn,
									reason: data.reason.split('-')[0],
									remark: data.remark
								},
								freeze: true,
								callback: () => { d.hide(); frm.reload_doc(); },
								error: () => d.hide()
							});
						},
						primary_action_label: __('Submit')
					});
					d.show();
				};
				if (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Administrator")) {
					add_custom_button(__("Cancel IRN - Taxpro"), action);
				}
			}

			if (invoice_eligible && irn && !irn_cancelled && !ewaybill) {
				const action = () => {
					const d = new frappe.ui.Dialog({
						title: __('Generate E-Way Bill'),
						size: "large",
						fields: get_ewaybill_fields(frm),
						primary_action: function() {
							const data = d.get_values();
							frappe.call({
								method: 'mapl_customization.customizations_for_mapl.einvoice.taxpro_einvoice.generate_eway_bill_by_irn',
								args: {
									doctype,
									docname: name,
									irn,
									...data
								},
								freeze: true,
								callback: () => { d.hide(); frm.reload_doc(); },
								error: () => d.hide()
							});
						},
						primary_action_label: __('Submit')
					});
					d.show();
				};
				//if (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Administrator")) {
				add_custom_button(__("Generate E-Way Bill - Taxpro"), action);
				//}
			}

			if (!invoice_eligible && !ewaybill) {
				const action = () => {
					const d = new frappe.ui.Dialog({
						title: __('Generate E-Way Bill'),
						size: "large",
						fields: get_ewaybill_fields(frm),
						primary_action: function() {
							const data = d.get_values();
							_custom_validate(data, true);
							//return;
							frappe.call({
								method: 'mapl_customization.customizations_for_mapl.einvoice.taxpro_einvoice.generate_eway_bill_by_json',
								args: {
									doctype,
									docname: name,
									...data
								},
								freeze: true,
								callback: () => { d.hide(); frm.reload_doc(); },
								error: () => d.hide()
							});
						},
						primary_action_label: __('Submit')
					});
					d.show();
				};
				//if (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Administrator")) {
					if (frm.doc.docstatus == 1) {
						add_custom_button(__("Generate E-Way Bill - Taxpro"), action);
					}
				//}
			}

			if ((irn && ewaybill && !irn_cancelled && !eway_bill_cancelled) || (!invoice_eligible && ewaybill)) {
				const action = () => {
					const d = new frappe.ui.Dialog({
						title: __("Cancel IRN"),
						fields: _custom_cancel_fields,
						primary_action: function() {
							const data = d.get_values();
							frappe.call({
								method: 'mapl_customization.customizations_for_mapl.einvoice.taxpro_einvoice.cancel_eway_bill',
								args: {
									doctype,
									docname: name,
									reason: data.reason.split('-')[0],
									remark: data.remark
								},
								freeze: true,
								callback: () => { d.hide(); frm.reload_doc(); },
								error: () => d.hide()
							});
						},
						primary_action_label: __('Submit')
					});
					d.show();
				};
				if (frappe.user_roles.includes("System Manager") || frappe.user_roles.includes("Administrator")) {
					add_custom_button(__("Cancel E-Way Bill - Taxpro"), action);
				}
			}
		}
	});
};

const _custom_request_irn_generation = (frm) => {
	frappe.call({
		method: 'mapl_customization.customizations_for_mapl.einvoice.taxpro_einvoice.generate_irn',
		args: { doctype: frm.doc.doctype, docname: frm.doc.name },
		freeze: true,
		callback: () => frm.reload_doc()
	});
};

const _custom_get_preview_dialog = (frm, action) => {
	const dialog = new frappe.ui.Dialog({
		title: __("Preview"),
		size: "large",
		fields: [
			{
				"label": "Preview",
				"fieldname": "preview_html",
				"fieldtype": "HTML"
			}
		],
		primary_action: () => action(frm) || dialog.hide(),
		primary_action_label: __('Generate IRN')
	});
	return dialog;
};

const _custom_show_einvoice_preview = (frm, einvoice) => {
	const preview_dialog = _custom_get_preview_dialog(frm, _custom_request_irn_generation);

	// initialize e-invoice fields
	einvoice["Irn"] = einvoice["AckNo"] = ''; einvoice["AckDt"] = frappe.datetime.nowdate();
	frm.doc.signed_einvoice = JSON.stringify(einvoice);

	// initialize preview wrapper
	const $preview_wrapper = preview_dialog.get_field("preview_html").$wrapper;
	$preview_wrapper.html(
		`<div>
			<div class="print-preview">
				<div class="print-format"></div>
			</div>
			<div class="page-break-message text-muted text-center text-medium margin-top"></div>
		</div>`
	);

	frappe.call({
		method: "frappe.www.printview.get_html_and_style",
		args: {
			doc: frm.doc,
			print_format: "GST E-Invoice",
			no_letterhead: 1
		},
		callback: function (r) {
			if (!r.exc) {
				$preview_wrapper.find(".print-format").html(r.message.html);
				const style = `
					.print-format { box-shadow: 0px 0px 5px rgba(0,0,0,0.2); padding: 0.30in; min-height: 80vh; }
					.print-preview { min-height: 0px; }
					.modal-dialog { width: 720px; }`;

				frappe.dom.set_style(style, "custom-print-style");
				preview_dialog.show();
			}
		}
	});
};

const _custom_cancel_fields = [
	{
		"label": "Reason",
		"fieldname": "reason",
		"fieldtype": "Select",
		"reqd": 1,
		"default": "1-Duplicate",
		"options": ["1-Duplicate", "2-Data Entry Error", "3-Order Cancelled", "4-Other"]
	},
	{
		"label": "Remark",
		"fieldname": "remark",
		"fieldtype": "Data",
		"reqd": 1
	}
];

const _custom_validate = function(data, is_urp) {
	if (is_urp) {
		if (!data.distance) {
			frappe.throw("Distance Required");
		}
		if (!data.mode_of_transport) {
			frappe.throw("Mode of Transport Required");
		}
		if (!data.gst_transporter_id && !data.vehicle_no) {
			frappe.throw("Transporter GST ID/Vehicle No Required");
		}
	} else {
		//TO DO
	}
	console.log(data);
};