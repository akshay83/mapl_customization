import frappe
import erpnext

@frappe.whitelist()
def update_customer_name(customer, customer_name):
	if not customer:
		return

	if not customer_name:
		return

	# Find all Parents
	parents = frappe.db.sql("""
						select 
							fieldname, 
							parent 
						from 
							`tabDocField` 
						where (options like '%%party%%' or options = 'Customer')
							and fieldtype like '%%Link%%' 
						order by parent""", as_dict=1)

	for p in parents:
		# Get Customer Name Data Fields from Parent
		link_fields = frappe.db.sql("""
						select 
							fieldname 
						from `tabDocField` 
						where parent=%(parent_value)s
							and (fieldname like '%%cust%%' or fieldname like '%%party%%') 
							and (fieldtype = 'Data' or oldfieldtype='Data')
						""",{
							'parent_value' : p.parent
						},as_dict=1)

		for l in link_fields:
			# Update Records
			frappe.db.sql("""update `tab{tab_name}` set {customer_field} = %(value)s
					 where {link_field} = %(link_value)s""".format (**{
						"tab_name":p.parent,
						"customer_field": l.fieldname,
						"link_field": p.fieldname
					}), {
						"value": customer_name,
						"link_value": customer
					})

			# Get Other Fields from Parent where default is Customer Name like title in Sales Invoice
			other_fields = frappe.db.sql("""
								select fieldname 
								from `tabDocField` 
								where parent=%(parent_value)s
								and `default` like '%%{def_field}%%' 
								and fieldtype = 'Data'
								""".format (**{
										'def_field': l.fieldname
									}), {
										'parent_value' : p.parent
									},as_dict=1)

			for o in other_fields:
				# Update Records
				frappe.db.sql("""update `tab{tab_name}` set {other_field} = %(value)s where 
						{link_field} = %(link_value)s""".format (**{
                                                "tab_name":p.parent,
                                                "other_field": o.fieldname,
						"link_field": p.fieldname,
                        }), {
                            	"value": customer_name,
								"link_value": customer
                        })

	#update_dynamic_link(customer, customer_name)
	#update_contact(customer, customer_name)
	frappe.db.commit()

def update_dynamic_link(link_name, link_title, link_doctype="Customer"):
	#Update Dynamic Link Table
	frappe.db.sql("""
					update `tabDynamic Link` 
					set link_title = %(title)s 
					where link_doctype = 'Customer' 
						and link_name = %(customer)s 
						and link_title is not null
				""", {
					"title": link_title,
					"customer": link_name
				})

def update_contact(customer, customer_name, contact_parent="Customer"):
	from mapl_customization.customizations_for_mapl.import_old_db.common import split_name
	from frappe.model.rename_doc import rename_doc
	contact_filters = [
                ["Dynamic Link", "link_doctype", "=", contact_parent],
                ["Dynamic Link", "link_name", "=", customer],
                ["Dynamic Link", "parenttype", "=", "Contact"],
			]                        	
	contacts = frappe.get_all("Contact", filters=contact_filters)
	for c in contacts:
		contact_doc = frappe.get_doc("Contact", c.name)
		contact_doc.first_name, contact_doc.middle_name, contact_doc.last_name = split_name(customer_name)
		new_name = " ".join(filter(None,
            [cstr(f).strip() for f in [contact_doc.first_name, contact_doc.last_name]]))+"-"+customer.strip()
		contact_doc.save()
		rename_doc("Contact", c.name, new_name)