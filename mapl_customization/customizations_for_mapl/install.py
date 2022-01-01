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
	

def create_index_on_address_title():
	frappe.db.sql("""create index address_title on `tabAddress` (address_title)""")

def after_install():
	create_index_on_address_title()
	set_default_options()
