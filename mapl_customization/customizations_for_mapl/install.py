import frappe

def set_default_options():
	frappe.db.set_value("Selling Settings", None, "cust_master_name", "Naming Series")
	frappe.db.set_value("Buying Settings", None, "supp_master_name", "Naming Series")
	frappe.db.set_value("Accounts Settings", None, "add_taxes_from_item_tax_template", 0)
	frappe.db.set_value("Accounts Settings", None, "suppress_advance_warning", 1)
	frappe.db.set_value("Stock Settings", None, "no_repost_item_valuation_document", 1)
	frappe.db.set_value("Global Defaults", None, "disable_rounded_total", 1)
	frappe.db.set_value("Dashboard Chart", "Profit and Loss", "is_public", 0)
	frappe.db.set_value("Dashboard Chart", "Outgoing Salary", "is_public", 0)
	frappe.db.set_value("Payroll Settings", None, "simplify_employee_loan_repayment", 1)
	session_defaults = frappe.get_single("Session Default Settings")
	sd = session_defaults.append("session_defaults")
	sd.ref_doctype = "Letter Head"
	session_defaults.save()

def set_view_permissions():
	frappe.db.set_value("Role","Accounts User", "search_bar", 1)
	frappe.db.set_value("Role","Stock User", "search_bar", 1)
	frappe.db.set_value("Role","Stock User", "form_sidebar", 1)
	frappe.db.set_value("Role","Stock User", "list_sidebar", 1)
	frappe.db.set_value("Role","Accounts User", "form_sidebar", 1)
	frappe.db.set_value("Role","Accounts User", "list_sidebar", 1)
	from frappe.permissions import add_permission
	add_permission("Workflow", "Accounts User")
	add_permission("Workflow", "Stock User")

def set_report_permissions():
	from unrestrict.unrestrict.utils import set_report_allowed_roles
	set_report_allowed_roles("Profit and Loss Statement", ["Accounts Manager","Auditor"])
	set_report_allowed_roles("Trial Balance", ["Accounts Manager","Auditor"])
	set_report_allowed_roles("Balance Sheet", ["Accounts Manager","Auditor"])
	set_report_allowed_roles("Consolidated Financial Statement", ["Accounts Manager","Auditor"])

def rebuild_regional_custom_fields():
	#Hope to Avoid Layout Issues
	from erpnext.regional.india.setup import create_custom_fields, get_custom_fields
	custom_fields = get_custom_fields()
	custom_fields['Sales Invoice'] = update_allow_on_submit(custom_fields, 'Sales Invoice')
	create_custom_fields(custom_fields, update=True)

def update_allow_on_submit(custom_fields, doctype):
	cf = custom_fields.get(doctype)
	for f in cf:
		if f.get('fieldtype') not in ['Section Break', 'Column Break']:
			f.update({'allow_on_submit':1})
	return cf

def create_index_on_address_title():
	try:
		frappe.db.sql("""create index address_title on `tabAddress` (address_title)""")
	except Exception:
		pass

def after_install():
	create_index_on_address_title()
	set_default_options()
	rebuild_regional_custom_fields()
	set_view_permissions()
	set_report_permissions()

def on_login(login_manager):
	try:
		letter_head = frappe.db.get_value("User", login_manager.user, "user_group")
		letter_head = frappe.db.get_value("Letter Head",letter_head,"name") or \
						frappe.db.get_value("Letter Head",{"is_default":1},"name")
		frappe.defaults.set_user_default("letter_head",letter_head, login_manager.user)
	except Exception:
		pass