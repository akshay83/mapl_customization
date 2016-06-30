frappe.TallyImportTool = Class.extend({
	init: function(parent) {
		this.page = frappe.ui.make_app_page({
			parent: parent,
			title: __("Tally Import Tool"),
			single_column: true
		});
		this.make();
		this.make_upload();
	},
	set_route_options: function() {
		var doctype = null;
		if(frappe.get_route()[1]) {
			doctype = frappe.get_route()[1];
		} else if(frappe.route_options && frappe.route_options.doctype) {
			doctype = frappe.route_options.doctype;
		}

		if(in_list(frappe.boot.user.can_import, doctype)) {
				this.select.val(doctype).change();
		}

		frappe.route_options = null;
	},
	make: function() {
		var me = this;
		frappe.boot.user.can_import = frappe.boot.user.can_import.sort();

		$(frappe.render_template("tally_import_main", this)).appendTo(this.page.main);

		this.select = this.page.main.find("select.doctype");
		this.select.on("change", function() {
			me.doctype = $(this).val();
			me.page.main.find(".export-import-section").toggleClass(!!me.doctype);
			if(me.doctype) {
				me.set_btn_links();
				// set button links
			}
		});
	},
	make_upload: function() {
		var me = this;
		frappe.upload.make({
			parent: this.page.main.find(".upload-area"),
			btn: this.page.main.find(".btn-import"),
			get_params: function() {
				return {
					overwrite: !me.page.main.find('[name="always_insert"]').prop("checked")
				}
			},
			args: {
				method: 'mapl_customization.customizations_for_mapl.page.tally_import.tally_import.read_uploaded_file',
			},
			onerror: function(r) {
				me.onerror(r);
			},
			callback: function(attachment, r) {
				if(r.message.error) {
					me.onerror(r);
				} else {
					r.messages = ["<h5 style='color:green'>" + __("Import Successful!") + "</h5>"].
						concat(r.message.messages)

					console.log(r);
				}
			},
			is_private: true
		});	
		frappe.realtime.on("tally_import_progress", function(data) {
				if(data.progress) {
					//show_alert(__("Importing... ")+data.document,1);
					me.write_messages(data);
					console.log(data.message);
				}
		});
	},
	write_messages: function(data) {
		this.page.main.find(".import-log").removeClass("hide");
		var parent = this.page.main.find(".import-log-messages");//.empty();
	
		var v = data.message;
		var $p = $('<div style=\"font-size:12px;margin:1px 1px 1px 10px;\"></div>').html(frappe.markdown(v)).appendTo(parent);
		if(data.error) {
			$p.css('color', 'red');
		} else if (data.message.substr(0,7) == 'Skipped') {
			$p.css('color', 'darkgray');	
		} else {
			$p.css('color', 'green');
		}
	},
	onerror: function(r) {
		if(r.message) {
			// bad design: moves r.messages to r.message.messages

			r.messages = ["<h4 style='color:red'>" + __("Import Failed") + "</h4>"]
				.concat(r.message.messages);

			r.messages.push("Please correct and import again.");

			this.write_messages(r.messages);

			console.log(r.error_desc);
		}
	}
});

frappe.pages['tally-import'].on_page_load = function(wrapper) {
	frappe.data_import_tool = new frappe.TallyImportTool(wrapper);
}

frappe.pages['tally-import'].on_page_show = function(wrapper) {
	frappe.data_import_tool && frappe.data_import_tool.set_route_options();
}



