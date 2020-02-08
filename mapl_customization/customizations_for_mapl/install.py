import frappe

def create_index_on_address_title():
	frappe.db.sql("""create index address_title on `tabAddress` (address_title)""")

def create_unique_index_on_customer():
	frappe.db.sql("""alter table `tabCustomer` add constraint unique_customer_record unique (customer_name, primary_contact_no, secondary_contact_no)""")

def after_install():
	create_index_on_address_title()
	create_unique_index_on_customer()
