frappe.provide('frappe');

var compressed_data = "";

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
            splitXML(compressed_data, callback = function(r) {
                if ($('div').find('[name="compress_data"]').prop("checked")) {
                    r.chunkString = compressString(r.chunkString);
                }
                write_messages({"message": "Processing Batch of "+r.chunkCounter.toString()});
                write_messages({"message": "Uploading Data:"+r.chunkString.length.toString()});
                frappe.call({                    
                    method: "mapl_customization.customizations_for_mapl.page.tally_import.tally_import.read_uploaded_file",
                    args: {
                        "filedata" : r.chunkString,
                        "decompress_data" : $('div').find('[name="compress_data"]').prop("checked")?1:0,
            			"overwrite": !$('div').find('[name="always_insert"]').prop("checked"),
                        "open_date": $('div').find('[name="exp_start_date"]').val()
                    },
                    callback: function(cr) {
                    }
                }); 
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
        compressed_data = reader.result;
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

function compressString(chunkXML) {
        write_messages({"message": "Compressing Data"});
        compressed_data = LZString.compressToUTF16(chunkXML);
        write_messages({"message": "Data Compressed"});
        console.log(compressed_data.length);
        return compressed_data;
}

function splitXML(xmlstring, callback) {
    var startTallyMsg = "<TALLYMESSAGE ";
    var endTallyMsg = "</TALLYMESSAGE>";
    var smlStringLength = xmlstring.length;
    var firstMessageStart = xmlstring.indexOf(startTallyMsg);
    var lastMessageEnd = xmlstring.lastIndexOf(endTallyMsg);
    var chunkSize = 100;
    var currentPos = firstMessageStart;
    var chunk = {};
    chunk.chunkString = "";
    chunk.chunkCounter = 1;
    while (true) {
        var messageEndIndex = xmlstring.indexOf(endTallyMsg, currentPos) + endTallyMsg.length;
        var message = xmlstring.substr(currentPos, (messageEndIndex - currentPos));
        chunk.chunkString = chunk.chunkString + "\n" + message;
        chunk.chunkCounter = chunk.chunkCounter + 1;
        if (chunk.chunkCounter == 100) {
            chunk.chunkString = "  <ENVELOPE> <BODY> <IMPORTDATA> <REQUESTDATA>" + chunk.chunkString + "</REQUESTDATA> </IMPORTDATA> </BODY> </ENVELOPE>"
            callback(chunk);
            chunk.chunkString = "";
            chunk.chunkCounter = 0;
        }
        currentPos = xmlstring.indexOf(startTallyMsg, messageEndIndex);
        if (currentPos < 0) {
                if (chunk.chunkCounter > 0) {
                    chunk.chunkString = "  <ENVELOPE> <BODY> <IMPORTDATA> <REQUESTDATA>" + chunk.chunkString + "</REQUESTDATA> </IMPORTDATA> </BODY> </ENVELOPE>"
                    callback(chunk)   
                }
                break;
        }
    }
}

frappe.realtime.on("tally_import_progress", function(data) {
    if (data.progress) {
        write_messages(data);
        //console.log(data.message);
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
