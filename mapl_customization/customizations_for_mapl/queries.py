# Copyright (c) 2015, Frappe Technologies Pvt. Ltd. and Contributors
# License: GNU General Public License v3. See license.txt

from __future__ import unicode_literals
import frappe
from frappe.desk.reportview import get_match_cond
from frappe.model.db_query import DatabaseQuery
from frappe.utils import nowdate

@frappe.whitelist()
def select_customer_supplier_query(doctype, txt, searchfield, start, page_len, filters):
	if filters.get("party_type")=="Customer":
		return mapl_customer_query(doctype, txt, searchfield, start, page_len, filters)
	elif filters.get("party_type")=="Supplier":
		return supplier_query(doctype, txt, searchfield, start, page_len, filters)
	elif filters.get("party_type")=="Employee":
		return employee_query(doctype, txt, searchfield, start, page_len, filters)

@frappe.whitelist()
def mapl_address_query (doctype, txt, searchfield, start, page_len, filters):
	fields = ["addr.name","addr.address_name","dyn.link_name","addr.address_line1", "addr.address_line2"]

	fields = ", ".join(fields)

	condition = ""
	if filters.get("customer"):
		condition += "and dyn.link_name = %(customer)s"

	if filters.get("supplier"):
		condition += "and dyn.link_name = %(supplier)s"

	return frappe.db.sql("""select {fields}
			from `tabAddress` addr, `tabDynamic Link` dyn where dyn.parent=addr.name and 
			(addr.{key} like %(txt)s
			or address_name like %(txt)s
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
@frappe.whitelist()
def mapl_customer_query(doctype, txt, searchfield, start, page_len, filters):
	#Index To Be Created in DB on Column `tabAddress`.address_title - New Query
	old_query = """
			select
			  cust.name,
			  cust.customer_name,
			  phone_numbers.phone,
			  addr.address_line1,
			  addr.address_line2
			from (`tabCustomer` cust left join `tabAddress` addr on addr.address_title = cust.name) left join
			  (select
			    link.link_name,
			    phone.phone
			   from `tabContact Phone` phone,
			     `tabDynamic Link` link
			    where phone.parent = link.parent
			      and link.link_doctype = 'Customer') phone_numbers on phone_numbers.link_name = cust.name
			where (cust.customer_name like %(txt)s
			  or phone_numbers.phone like %(txt)s
			  or cust.name like %(txt)s) and cust.disabled=0
			group by cust.name
			order by customer_name, name limit %(start)s, %(page_len)s
		"""

	new_query = """
 					select
        				cust.name,
        				cust.customer_name,
        				addr.address_line1,
        				addr.address_line2
      				from (`tabCustomer` cust left join `tabAddress` addr on addr.address_title = cust.name)
  					where (cust.customer_name like %(txt)s
        				or cust.name like %(txt)s or addr.address_line1 like %(txt)s or addr.address_line2 like %(txt)s
  						or cust.name in (select link.link_name
         					from
           						`tabContact Phone` phone,
           						`tabDynamic Link` link
          					where phone.parent = link.parent
            					and phone.phone like %(txt)s)) and cust.disabled=0
  					group by cust.name
  					order by cust.customer_name, name limit {0}, {1}
				"""

	return frappe.db.sql(new_query.format(start, page_len), {
			'txt': "%%%s%%" % txt
		})

# searches for customer by phone only
@frappe.whitelist()
def mapl_customer_by_phone_query(doctype, txt, searchfield, start, page_len, filters):
	new_query = """
 					select
        				cust.name
      				from `tabCustomer` cust
  					where (cust.name in (select link.link_name
         					from
           						`tabContact Phone` phone,
           						`tabDynamic Link` link
          					where phone.parent = link.parent
            					and phone.phone like %(txt)s)) and cust.disabled=0
  					group by cust.name
  					order by cust.customer_name, name limit {0}, {1}
				"""

	return frappe.db.sql(new_query.format(start, page_len), {
			'txt': "%%%s%%" % txt
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

