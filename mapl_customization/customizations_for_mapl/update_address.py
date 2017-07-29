import frappe
import erpnext
from frappe.contacts.doctype.address.address import get_address_display


@frappe.whitelist()
def update_address(address_name):
	if not address_name:
		return

	new_address = get_address_display(address_name)

	# Find all Parents
	parents = frappe.db.sql("""select distinct parent from `tabDocField` where 
		(fieldname='shipping_address' or fieldname='address_display') 
		and fieldtype like '%%Text%%' order by parent""", as_dict=1)


	for p in parents:

		# Get Link Field Name from Parent
		link_fields = frappe.db.sql("""select fieldname from `tabDocField` where 
			fieldname like '%%address%%' and fieldtype='Link' and parent= %(parent_value)s """,{
					'parent_value' : p.parent
					},as_dict=1)

		for l in link_fields:

			# Update Records
			frappe.db.sql("""update `tab{tab_name}` set {address_field} = %(value)s 
					 where {link_field} = %(link_value)s""".format (**{
						"tab_name":p.parent,
						"address_field": "address_display" if "shipping" not in l.fieldname.lower() else "shipping_address",
						"link_field": l.fieldname
					}), {
						"value": new_address,
						"link_value": address_name
					})

	frappe.db.commit()
