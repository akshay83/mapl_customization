# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import get_match_cond
from frappe.model.db_query import DatabaseQuery
from frappe.utils import nowdate


def select_customer_supplier_query(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("party_type")=="Customer":
		return mapl_customer_query(doctype, txt, searchfield, start, page_len, filters)
	elif filters.get("party_type")=="Supplier":
		return supplier_query(doctype, txt, searchfield, start, page_len, filters)

def mapl_address_query (doctype, txt, searchfield, start, page_len, filters):
	fields = ["name","customer_name","supplier_name","address_line1", "address_line2"]

	fields = ", ".join(fields)

	condition = ""	
	if filters.get("customer"):
		condition += "and `tabAddress`.customer = %(customer)s"

	if filters.get("supplier"):
		condition += "and `tabAddress`.supplier = %(supplier)s"

	return frappe.db.sql("""select {fields}
			from `tabAddress` where
			({key} like %(txt)s
			or address_line1 like %(txt)s
			or address_line2 like %(txt)s)
			{condition} {mcond}
			order by
			if(locate(%(_txt)s, `tabAddress`.name), locate(%(_txt)s, `tabAddress`.name), 99999),
			`tabAddress`.name, `tabAddress`.customer_name
			limit %(start)s, %(page_len)s""".format(**{
				"fields": fields,
				"key": searchfield,
				"mcond": get_match_cond(doctype),
				"condition": condition
			}), {
				'txt': "%%%s%%" % txt,
				'_txt': txt.replace("%", ""),
				'start': start,
				'page_len': page_len,
				'customer': filters.get("customer",""),
				'supplier': filters.get("supplier","")
			})


			

# searches for customer
def mapl_customer_query(doctype, txt, searchfield, start, page_len, filters):
	cust_master_name = frappe.defaults.get_user_default("cust_master_name")

	if cust_master_name == "Customer Name":
		fields = ["name", "customer_group", "territory"]
	else:
		fields = ["cust.name", "cust.customer_name", 
			"cust.primary_contact_no", "cust.secondary_contact_no",
			"addr.address_line1", "addr.address_line2"]

	fields = ", ".join(fields)

	return frappe.db.sql("""select {fields} from `tabCustomer` cust, `tabAddress` addr 
		where cust.name=addr.customer
			and ({key} like %(txt)s
				or cust.customer_name like %(txt)s
				or cust.primary_contact_no like %(txt)s
				or cust.secondary_contact_no like %(txt)s
				or addr.address_line1 like %(txt)s
				or addr.address_line2 like %(txt)s) and cust.disabled=0
			{mcond}
		group by cust.name
		order by cust.customer_name, cust.name
		limit %(start)s, %(page_len)s""".format(**{
			"fields": fields,
			"key": "cust.name",
			"mcond": get_match_cond(doctype)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

# searches for supplier
def supplier_query(doctype, txt, searchfield, start, page_len, filters):
	supp_master_name = frappe.defaults.get_user_default("supp_master_name")
	if supp_master_name == "Supplier Name":
		fields = ["name", "supplier_type"]
	else:
		fields = ["name", "supplier_name", "supplier_type"]
	fields = ", ".join(fields)

	return frappe.db.sql("""select {field} from `tabSupplier`
		where docstatus < 2
			and ({key} like %(txt)s
				or supplier_name like %(txt)s) and disabled=0
			{mcond}
		order by name, supplier_name
		limit %(start)s, %(page_len)s """.format(**{
			'field': fields,
			'key': searchfield,
			'mcond':get_match_cond(doctype)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

