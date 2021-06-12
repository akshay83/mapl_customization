frappe.ui.form.on("Item","refresh", function(frm) {
	$("div.frappe-control[data-fieldname='description']").find('.note-editing-area').css('height','100px');
});
