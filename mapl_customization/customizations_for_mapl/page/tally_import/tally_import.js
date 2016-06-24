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
			callback: function(attachment, r) {
				console.log(r);
			},
			is_private: true
		});
	}
});

frappe.pages['tally-import'].on_page_load = function(wrapper) {
	frappe.data_import_tool = new frappe.TallyImportTool(wrapper);
}

frappe.pages['tally-import'].on_page_show = function(wrapper) {
	frappe.data_import_tool && frappe.data_import_tool.set_route_options();
}



