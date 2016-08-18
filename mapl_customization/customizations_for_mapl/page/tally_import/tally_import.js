frappe.provide('frappe');

frappe.TallyImportTool = Class.extend({
    init: function(parent) {
        this.page = frappe.ui.make_app_page({
            parent: parent,
            title: __("Tally Import Tool"),
            single_column: true
        });
        this.make();
    },
    set_route_options: function() {
        var doctype = null;
        if (frappe.get_route()[1]) {
            doctype = frappe.get_route()[1];
        } else if (frappe.route_options && frappe.route_options.doctype) {
            doctype = frappe.route_options.doctype;
        }

        if (in_list(frappe.boot.user.can_import, doctype)) {
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
            if (me.doctype) {
                me.set_btn_links();
                // set button links
            }
        });
    }
});




frappe.pages['tally-import'].on_page_show = function(wrapper) {
    $("#btn_import").prop("disabled",true)

    var $form = $("form[id='frmFileUp']");
    $("#btn_read").click(function() {
      var input = $('div').find("[type='file']").get(0);
  
      if(input.files.length) {
        input.filedata = { "files_data" : [] }; //Initialize as json array.

        window.file_reading = true;

        $.each(input.files, function(key, value) {
          setupReader(value, input);
        });

        window.file_reading = false;
      }
    });

    $("#btn_import").click(function() {
        var filedata = $('#select_files').prop('filedata');
        if (filedata) {
            write_messages({"message": "Uploading Data"});
            frappe.call({
                method: "mapl_customization.customizations_for_mapl.page.tally_import.tally_import.read_uploaded_file",
                args: {
                    "filedata" : filedata,
                    "decompress_data" : $('div').find('[name="compress_data"]').prop("checked")?1:0,
        			"overwrite": !$('div').find('[name="always_insert"]').prop("checked"),
                    "open_date": $('div').find('[name="exp_start_date"]').val()
                },
                callback: function(r) {
                    if (!r.exc) {
                        frappe.msgprint(__("Files uploaded"));
                    } else {
                        frappe.msgprint(__("Files not uploaded. <br /> " + r.exc));
                    }
                }
            });
        }
    });
};

function setupReader(file, input) {
    var name = file.name;
    var reader = new FileReader();
	var freeze = $('<div id="freeze" class="modal-backdrop fade"></div>')
				.appendTo("#body_div");
    reader.onload = function(e) {
        freeze.remove();
        var compressed_data = "";
        if ($('div').find('[name="compress_data"]').prop("checked")) {
            write_messages({"message": "Compressing Data"});
            compressed_data = LZString.compressToUTF16(reader.result);
            write_messages({"message": "Data Compressed"});
        } else {
            compressed_data = reader.result;
        }
        input.filedata.files_data.push({
            "__file_attachment": 1,
            "filename": file.name,
            "dataurl": compressed_data
        });
        $("#btn_import").prop("disabled",false)
        //TEST
        //console.log(reader.result.length);
        //console.log(LZString.compressToUTF16(reader.result).length);
        //var t = LZString.compress("HELLO");
        //console.log(t);
        //console.log(LZString.decompress(t));
    }
	freeze.html('<div class="freeze-message-container"><div class="freeze-message"><p class="lead">Reading</p></div></div>');
    freeze.addClass("in")
    reader.readAsText(file);
}

frappe.realtime.on("tally_import_progress", function(data) {
    if (data.progress) {
        write_messages(data);
        console.log(data.message);
    }
});
write_messages = function(data) {
    $('div').find('.import-log').removeClass("hide");
    var parent = $('div').find(".import-log-messages"); //.empty();

    var v = data.message;
    if (v == null) return;
    var $p = $('<div style=\"font-size:12px;margin:1px 1px 1px 10px;\"></div>').html(frappe.markdown(v)).appendTo(parent);
    if (data.error) {
        $p.css('color', 'red');
    } else if (data.message.substr(0, 7) == 'Skipped') {
        $p.css('color', 'darkgray');
    } else {
        $p.css('color', 'green');
    }
};

frappe.pages['tally-import'].on_page_load = function(wrapper) {
    frappe.data_import_tool = new frappe.TallyImportTool(wrapper);
}
