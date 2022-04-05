import frappe
from frappe.utils import cint, cstr

def set_default_series():
	def scrub_options_list(ol):
		options = list(filter(lambda x: x, [cstr(n).strip() for n in ol]))
		return options

	def set_series_for(doctype, ol):
		options = scrub_options_list(ol)
		default = options[0] if options else ''

		# update in property setter
		prop_dict = {'options': "\n".join(options), 'default': default}

		for prop in prop_dict:
			ps_exists = frappe.db.get_value("Property Setter",
				{"field_name": 'naming_series', 'doc_type': doctype, 'property': prop})

			if ps_exists:
				ps = frappe.get_doc('Property Setter', ps_exists)
				ps.value = prop_dict[prop]
				ps.save()
			else:
				ps = frappe.get_doc({
					'doctype': 'Property Setter',
					'doctype_or_field': 'DocField',
					'doc_type': doctype,
					'field_name': 'naming_series',
					'property': prop,
					'value': prop_dict[prop],
					'property_type': 'Text',
					'__islocal': 1
				})
				ps.save()
	#Backward Compatibility
	set_series_for('Customer', ['CUST-'])
	set_series_for('Employee', ['EMP/'])
	set_series_for('Supplier', ['SUPP-'])

def set_default_options():
	from erpnext.setup.doctype.naming_series.naming_series import set_by_naming_series	
	frappe.db.set_value("Selling Settings", None, "cust_master_name", "Naming Series")
	frappe.db.set_default("cust_master_name", "Naming Series")	
	set_by_naming_series("Customer", "customer_name", True, hide_name_field=False)	

	frappe.db.set_value("Buying Settings", None, "supp_master_name", "Naming Series")
	frappe.db.set_default("supp_master_name", "Naming Series")	
	set_by_naming_series("Supplier", "supplier_name", True, hide_name_field=False)

	frappe.db.set_value("Accounts Settings", None, "add_taxes_from_item_tax_template", 0)
	frappe.db.set_default("add_taxes_from_item_tax_template",0)	

	frappe.db.set_value("Accounts Settings", None, "enable_common_party_accounting", 1)
	frappe.db.set_default("enable_common_party_accounting", 1)

	frappe.db.set_value("Accounts Settings", None, "suppress_advance_warning", 1)
	frappe.db.set_value("Stock Settings", None, "no_repost_item_valuation_document", 1)
	frappe.db.set_value("Global Defaults", None, "disable_rounded_total", 1)
	frappe.db.set_value("Dashboard Chart", "Profit and Loss", "is_public", 0)
	frappe.db.set_value("Dashboard Chart", "Outgoing Salary", "is_public", 0)
	frappe.db.set_value("Payroll Settings", None, "simplify_employee_loan_repayment", 1)
	frappe.db.set_value("Scheduled Job Type", "process_loan_interest_accrual.process_loan_interest_accrual_for_term_loans", \
						"stopped", 1)	
	session_defaults = frappe.get_single("Session Default Settings")
	sd = session_defaults.append("session_defaults")
	sd.ref_doctype = "Letter Head"
	#sd = session_defaults.append("session_defaults")
	#sd.ref_doctype = "Warehouse"
	session_defaults.save()

def set_view_permissions():
	frappe.db.set_value("Role","Accounts User", "search_bar", 1)
	frappe.db.set_value("Role","Stock User", "search_bar", 1)
	frappe.db.set_value("Role","Stock User", "form_sidebar", 1)
	frappe.db.set_value("Role","Stock User", "list_sidebar", 1)
	frappe.db.set_value("Role","Accounts User", "form_sidebar", 1)
	frappe.db.set_value("Role","Accounts User", "list_sidebar", 1)
	frappe.db.set_value("Role","Accounts User", "view_switcher", 1)
	frappe.db.set_value("Role","Accounts User", "timeline", 1)
	from frappe.permissions import add_permission, update_permission_property
	add_permission("Workflow", "Accounts User")
	add_permission("Workflow", "Stock User")
	add_permission("Stock Settings", "Stock User")
	add_permission("Global Defaults", "Accounts User")
	update_permission_property("Sales Invoice", "Accounts User", 0, ptype="cancel", value=1)

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
	"""This Index is Important"""
	try:
		frappe.db.sql("""create index address_title on `tabAddress` (address_title)""")
	except Exception:
		pass

def after_install():
	rebuild_regional_custom_fields()	
	set_default_series()	
	create_index_on_address_title()
	set_default_options()
	set_view_permissions()
	set_report_permissions()

def on_login(login_manager):
	warehouse_map = {"Vijay Nagar":"Main Location - MAPL","Geeta Bhawan":"Geeta Bhawan - MAPL","Ranjeet Hanuman":"Ranjeet Hanuman - MAPL"}
	try:
		letter_head = frappe.db.get_value("User", login_manager.user, "user_group")
		letter_head = frappe.db.get_value("Letter Head",letter_head,"name") or \
						frappe.db.get_value("Letter Head",{"is_default":1},"name")
		frappe.defaults.set_user_default("letter_head",letter_head, login_manager.user)
		#frappe.defaults.set_user_default("warehouse", warehouse_map.get(letter_head), login_manager.user)
	except Exception:
		pass