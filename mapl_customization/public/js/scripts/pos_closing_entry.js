frappe.ui.form.on('POS Closing Entry', {
	onload(frm) {
		if ($(window).width() < 999 && frappe.user.has_role("POS User") && !frappe.user.has_role("System User")) {
		    $(`.btn.btn-primary.btn-sm.primary-action[data-label="Save"]`).detach().appendTo(".collapse.navbar-collapse.justify-content-end");
		    $(`.btn.btn-primary.btn-sm.primary-action[data-label="Save"]`).css({"margin-left":"20px"});
		    $(`.btn.btn-primary.btn-sm.primary-action[data-label="Submit"]`).detach().appendTo(".collapse.navbar-collapse.justify-content-end");
		    $(`.btn.btn-primary.btn-sm.primary-action[data-label="Submit"]`).css({"margin-left":"20px"});
		}
	}
})