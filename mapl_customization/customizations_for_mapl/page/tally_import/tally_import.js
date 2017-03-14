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
<<<<<<< HEAD
    $("#btn_import").prop("disabled", true)
=======
    $("#btn_import").prop("disabled", true);
    //$("#btn_import_next_batch").prop("disabled", true);
>>>>>>> temp

    var $form = $("form[id='frmFileUp']");
    $("#btn_read").click(function() {
        var input = $('div').find("[type='file']").get(0);

        if (input.files.length) {
            input.filedata = {
                "files_data": []
            }; //Initialize as json array.

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
            write_messages({
                "message": "Uploading Data"
            });
            initImportProcess();
            processNextBatch(doCallback);
        }
    });
    $("#btn_import_internal").click(function() {
            write_messages({
                "message": "Starting Internal Process"
            });

<<<<<<< HEAD
            start_internal_import();
=======
            start_internal_import(-1);
    });
    $("#btn_import_next_batch").click(function() {
            write_messages({
                "message": "Starting Next Batch"
            });

            start_internal_import(1);
>>>>>>> temp
    });
};


<<<<<<< HEAD
function start_internal_import() {
=======
function start_internal_import(next_batch) {
>>>>>>> temp
    frappe.call({
        method: "mapl_customization.customizations_for_mapl.tally_import_stock_internal.process_import",
        args: {
            "open_date": $('div').find('[name="exp_start_date"]').val(),
<<<<<<< HEAD
	    "brand": $('div').find('[name="brand"]').val()
        },
        callback: function(r) {
            if (!r.exc) {
                 frappe.msgprint(__("Process Complete"));
=======
	    "brand": $('div').find('[name="brand"]').val(),
            "next_batch": next_batch
        },
        callback: function(r) {
            if (!r.exc) {
		 console.log(r.message.messages);
		 if (parseInt(r.message.messages)<=0) {
                   frappe.msgprint(__("Process Complete, Ready for Next Batch"));
		   $("#btn_import_next_batch").prop("disabled", false);
		 } else {
		   frappe.msgprint(__("Process Complete"));
		   $("#btn_import_next_batch").prop("disabled", true);
		 }
>>>>>>> temp
            } else {
                 frappe.msgprint(__("Error during Importing <br /> " + r.exc));
            }
        }
    });
};


function doCallback(r, isLastChunk) {
    if ($('div').find('[name="compress_data"]').prop("checked")) {
        r.chunkString = compressString(r.chunkString);
    }
    write_messages({
        "message": "Processing Batch of " + r.chunkCounter.toString()
    });
    write_messages({
        "message": "Length of Data Uploaded:" + r.chunkString.length.toString()
    });
    frappe.call({
        method: "mapl_customization.customizations_for_mapl.page.tally_import.tally_import.read_uploaded_file",
        args: {
            "filedata": r.chunkString,
            "decompress_data": $('div').find('[name="compress_data"]').prop("checked") ? 1 : 0,
            "overwrite": !$('div').find('[name="always_insert"]').prop("checked"),
            "open_date": $('div').find('[name="exp_start_date"]').val(),
	    "brand": $('div').find('[name="brand"]').val()
        },
        callback: function(cr) {
            if (!r.exc) {
                if (!isLastChunk) {
                    processNextBatch(doCallback);   
                } else {
                 frappe.msgprint(__("Process Complete"));
                }
            } else {
                 frappe.msgprint(__("Error during Importing <br /> " + r.exc));
            }
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
        $("#btn_import").prop("disabled", false)

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
    write_messages({
        "message": "Compressing Data"
    });
    compressedXML = LZString.compressToUTF16(chunkXML);
    write_messages({
        "message": "Data Compressed"
    });
    console.log(compressed_data.length);
    return compressedXML;
}

var chunk = {};
var processImport = {};

function initImportProcess() {
    processImport.startTallyMsg = "<TALLYMESSAGE ";
    processImport.endTallyMsg = "</TALLYMESSAGE>";
    processImport.xmlStringLength = compressed_data.length;
    processImport.firstMessageStart = compressed_data.indexOf(processImport.startTallyMsg);
    processImport.lastMessageEnd = compressed_data.lastIndexOf(processImport.endTallyMsg);
    processImport.chunkSize = 100;
    processImport.currentPos = processImport.firstMessageStart;
    chunk.chunkString = "";
    chunk.chunkCounter = 0;
    processImport.chunksSent = 0;
}


function processNextBatch(callback) {
    while (true) {
        var messageEndIndex = compressed_data.indexOf(processImport.endTallyMsg, processImport.currentPos) + processImport.endTallyMsg.length;
        var message = compressed_data.substr(processImport.currentPos, (messageEndIndex - processImport.currentPos));
        chunk.chunkString = chunk.chunkString + "\n" + message;
        chunk.chunkCounter = chunk.chunkCounter + 1;
        processImport.currentPos = compressed_data.indexOf(processImport.startTallyMsg, messageEndIndex);
        if (chunk.chunkCounter == processImport.chunkSize) {
            chunk.chunkString = "  <ENVELOPE> <BODY> <IMPORTDATA> <REQUESTDATA>" + chunk.chunkString + "</REQUESTDATA> </IMPORTDATA> </BODY> </ENVELOPE>"
            callback(chunk, false);
            chunk.chunkString = "";
            chunk.chunkCounter = 0;
            processImport.chunksSent = processImport.chunksSent+1;
            break;
        }
        if (processImport.currentPos < 0 /* For Testing || processImport.chunksSent > 5*/) {
            if (chunk.chunkCounter > 0) {
                chunk.chunkString = "  <ENVELOPE> <BODY> <IMPORTDATA> <REQUESTDATA>" + chunk.chunkString + "</REQUESTDATA> </IMPORTDATA> </BODY> </ENVELOPE>"
                callback(chunk, true);
            }
            break;
        }
    }
}


frappe.realtime.on("tally_import_progress", function(data) {
    //if (data.progress) {
        write_messages(data);
        //console.log(data.message);
    //}
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
