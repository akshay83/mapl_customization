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
	elif filters.get("party_type")=="Employee":
		return employee_query(doctype, txt, searchfield, start, page_len, filters)

def mapl_address_query (doctype, txt, searchfield, start, page_len, filters):
	fields = ["addr.name","dyn.link_name","addr.address_line1", "addr.address_line2"]

	fields = ", ".join(fields)

	condition = ""	
	if filters.get("customer"):
		condition += "and dyn.link_name = %(customer)s"

	if filters.get("supplier"):
		condition += "and dyn.link_name = %(supplier)s"

	return frappe.db.sql("""select {fields}
			from `tabAddress` addr, `tabDynamic Link` dyn where dyn.parent=addr.name and 
			(addr.{key} like %(txt)s
			or address_line1 like %(txt)s
			or address_line2 like %(txt)s
			or city like %(txt)s)
			{condition} {mcond}
			order by
			if(locate(%(_txt)s, addr.name), locate(%(_txt)s, addr.name), 99999),
			addr.name 
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
	return frappe.db.sql("""select * from 
          (
            (select cust.name, cust.customer_name, cust.primary_contact_no,
              cust.secondary_contact_no,addr.address_line1,addr.address_line2 
              from `tabCustomer` cust, `tabAddress` addr, `tabDynamic Link` dyn
              where cust.name=dyn.link_name and dyn.parent=addr.name and
              ({key} like %(txt)s
                or cust.customer_name like %(txt)s
                or cust.primary_contact_no like %(txt)s
                or cust.secondary_contact_no like %(txt)s
                or addr.address_line1 like %(txt)s
                or addr.address_line2 like %(txt)s) and cust.disabled=0
              group by cust.name)
            union all
            (select cust.name, cust.customer_name, cust.primary_contact_no,
              cust.secondary_contact_no,null,null 
              from `tabCustomer` cust where 
              ({key} like %(txt)s
                or cust.customer_name like %(txt)s
                or cust.primary_contact_no like %(txt)s
		or cust.vehIcle_no like %(txt)s
                or cust.secondary_contact_no like %(txt)s) and cust.disabled=0)
            ) 
            as temp_tb group by name order by customer_name, name limit %(start)s, %(page_len)s""".format(**{
			"key": "cust.name",
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


def employee_query(doctype, txt, searchfield, start, page_len, filters):
	return frappe.db.sql("""select name, employee_name from `tabEmployee`
			where docstatus < 2
			and ({key} like %(txt)s
			or employee_name like %(txt)s)
			{mcond}
			order by name, employee_name
			limit %(start)s, %(page_len)s """.format(**{
			'key': searchfield,
			'mcond':get_match_cond(doctype)
		}), {
			'txt': "%%%s%%" % txt,
			'_txt': txt.replace("%", ""),
			'start': start,
			'page_len': page_len
		})

