# Copyright (c) 2021, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document

class ImportCustomers(Document):
	pass

class DoImportCustomers():
	def __init__(self, rows):
		self.create_columns(rows[0])
		self.process(rows[1:])

	def create_columns(self, header_row):
		self.columns = []
		for h in header_row:
			self.columns.append(h)

	def process(self, rows):
		for r in rows:
			row_dict = self.get_row_dict(r)
			self.create_customer(row_dict)
			self.create_address(row_dict)
			self.create_contact(row_dict)
			print (row_dict)

	def get_row_dict(self, row):
		row_dict = {}
		if (self.is_row_length_correct(row)):
			for i, r in enumerate(row):
				row_dict[self.columns[i]] = r

		return frappe._dict(row_dict)

	def is_row_length_correct(self, row):
		if len(row) != len(self.columns):
			return False
		return True

	def create_customer(self, row_dict):
		if not frappe.db.exists("Customer", row_dict.get("Customer-name")):
			doc = frappe.new_doc("Customer")
			for k in row_dict.keys():
				if k.startswith("Customer-"):
					setattr(doc, k[9:], row_dict.get(k))
			doc.name = row_dict.get("Customer-name")
			doc.save()
			print ('-'*40)
			print ("Created Customer-",row_dict.get("Customer-name"))
			print ('-'*40)

	def create_address(self, row_dict):
		query = """
				select address.name from `tabAddress` address,`tabDynamic Link` link
				where link.parent = address.name and link.link_name = '{0}'
				and link.link_doctype = 'Customer' and address.address_line1 = '{1}'
				{2} and address.city = '{3}'
			""".format(row_dict.get("Customer-name"),
				row_dict.get("Address-address_line1"),
				"""and address.address_line2 = '{0}'""".format(row_dict.get("Address-address_line2")) if row_dict.get("Address-address_line2") else "",
				row_dict.get("Address-city"))
		print (query)
		check_doc = frappe.db.sql(query,as_dict=1)
		if not check_doc or len(check_doc) <= 0:
			doc = frappe.new_doc("Address")
			doc.append('links', dict(link_doctype='Customer', link_name=row_dict.get("Customer-name")))
			for k in row_dict.keys():
				if k.startswith("Address-"):
					setattr(doc, k[8:], row_dict.get(k))
			doc.flags.ignore_validate = True
			doc.insert(ignore_mandatory=True)

	def create_contact(self, row_dict):
		query = """
				select contact.name from `tabContact` contact,`tabDynamic Link` link,`tabContact Phone` phone
				where link.parent = contact.name and link.link_name = '{0}' and phone.parent = contact.name
				and link.link_doctype = 'Customer' and phone.phone = '{1}'
			""".format(row_dict.get("Customer-name"),row_dict.get("Contact-phone"))
		check_doc = frappe.db.sql(query,as_dict=1)
		if not check_doc or len(check_doc) <= 0:
			doc = frappe.new_doc("Contact")
			doc.append('links', dict(link_doctype='Customer', link_name=row_dict.get("Customer-name")))
			for k in row_dict.keys():
				if k.startswith("Contact-"):
					setattr(doc, k[8:], row_dict.get(k))
			doc.add_phone(row_dict.get('Contact-phone'), row_dict.get('Contact-is_primary_mobile_no'))
			#contact.add_email(args.get('primary_email'), is_primary=True)
			doc.flags.ignore_validate = True
			doc.insert(ignore_mandatory=True)


@frappe.whitelist()
def upload():
	from frappe.utils.csvutils import read_csv_content
	rows = read_csv_content(frappe.local.uploaded_file)
	if not rows:
		frappe.throw(_("Please select a csv file"))
	frappe.enqueue(import_customers, rows=rows, now=True if len(rows) < 200 else False)

def import_customers(rows):
	DoImportCustomers(rows)
