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
