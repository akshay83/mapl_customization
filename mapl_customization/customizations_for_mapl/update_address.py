import frappe
import erpnext
from frappe.contacts.doctype.address.address import get_address_display


@frappe.whitelist()
def update_address(address_name):
	if not address_name:
		return

	new_address = get_address_display(address_name)

	# Find all Parents
	parents = frappe.db.sql("""
			select distinct parent from (
				(
				  select 
				  distinct parent 
				  from `tabDocField` 
				  where
				   (fieldname = 'shipping_address' or fieldname='address_display')
				   and fieldtype like '%%Text%%'
				)
				union all
				(
				  select 
				  distinct dt 
				  from `tabCustom Field` 
				  where 
				    name like '%%address%%' 
				    and fieldtype like '%%Text%%'
				)
			) a order by parent
			""", as_dict=1)


	for p in parents:

		# Get Link Field Name from Parent
		link_fields = frappe.db.sql("""
						(
						  select 
						    fieldname 
						  from `tabDocField` 
						  where
						    fieldname like '%%address%%' 
						    and fieldtype='Link' 
						    and parent= %(parent_value)s 
						)
						union all
						(
						  select 
						    fieldname 
						  from `tabCustom Field` 
						  where
						    fieldname like '%%address%%' 
						    and fieldtype='Link' 
						    and dt= %(parent_value)s 
						) """,{
							'parent_value' : p.parent
						},as_dict=1)

		for l in link_fields:

			add_field = "address_display" if "shipping" not in l.fieldname.lower() else "shipping_address"

			try:
				# Update Records
				frappe.db.sql("""update `tab{tab_name}` set {address_field} = %(value)s 
					 where {link_field} = %(link_value)s""".format (**{
						"tab_name":p.parent,
						"address_field": add_field,
						"link_field": l.fieldname
					}), {
						"value": new_address,
						"link_value": address_name
					})
			except:

				for ee in get_custom_address_display_fieldnames(p.parent):

					# Update Records
					frappe.db.sql("""update `tab{tab_name}` set {address_field} = %(value)s 
						 where {link_field} = %(link_value)s""".format (**{
							"tab_name":p.parent,
							"address_field": ee.fieldname,
							"link_field": l.fieldname
						}), {
							"value": new_address,
							"link_value": address_name
						})


	frappe.db.commit()


def get_custom_address_display_fieldnames(table_name):

	return frappe.db.sql("""
				  select 
				   fieldname
				  from `tabCustom Field` 
				  where 
				    name like '%%address%%' 
				    and fieldtype like '%%Text%%'
				    and dt = %(table_name)s
				""",{"table_name":table_name}, as_dict=1)
