import frappe
import erpnext

@frappe.whitelist()
def update_customer_name(customer, customer_name):
	if not customer:
		return

	if not customer_name:
		return

	# Find all Parents
	parents = frappe.db.sql("""select fieldname, parent from `tabDocField` where (options like '%%party%%' or options = 'Customer') 
				and fieldtype like '%%Link%%' order by parent""", as_dict=1)


	for p in parents:

		# Get Customer Name Data Fields from Parent
		link_fields = frappe.db.sql("""select fieldname from `tabDocField` where parent=%(parent_value)s
				and (fieldname like '%%cust%%' or fieldname like '%%party%%') and fieldtype = 'Data'""",{
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
			other_fields = frappe.db.sql("""select fieldname from `tabDocField` where parent=%(parent_value)s
                                and `default` like '%%{def_field}%%' and fieldtype = 'Data'""".format (**{
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


	frappe.db.commit()
