# Copyright (c) 2021, Akshay Mehta and contributors
# For license information, please see license.txt

import frappe
import re
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
			self.row_dict = self.get_row_dict(r)

			#Ignore "'"
			for element in self.row_dict.keys():
				if (self.row_dict.get(element)):
					self.row_dict[element] = self.row_dict.get(element).replace("'","\\'")

			self.create_customer()
			self.create_address()
			self.create_contact()
			self.create_email()
			#DEBUG -- print (self.row_dict)

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

	def create_customer(self):
		if not frappe.db.exists("Customer", self.row_dict.get("Customer-name")):
			doc = frappe.new_doc("Customer")
			for k in self.row_dict.keys():
				if k.startswith("Customer-"):
					setattr(doc, k[9:], self.row_dict.get(k))					
			doc.ignore_validate_hook = 1 #Custom Value to Ignore Validation in Our Hooks
			doc.insert(ignore_permissions=True, set_name=self.row_dict.get("Customer-name"))
			#DEBUG -- print ('-'*40)			
			#DEBUG -- print ("Created Customer-",self.row_dict.get("Customer-name"))
			#DEBUG -- print ('-'*40)

	def create_address(self):
		query = """
				select address.name from `tabAddress` address,`tabDynamic Link` link
				where link.parent = address.name and link.link_name = '{0}'
				and link.link_doctype = 'Customer' and address.address_line1 = '{1}'
				{2} and address.city = '{3}'
			""".format(self.row_dict.get("Customer-name"),
				self.row_dict.get("Address-address_line1"),
				"""and address.address_line2 = '{0}'""".format(self.row_dict.get("Address-address_line2")) if self.row_dict.get("Address-address_line2") else "",
				self.row_dict.get("Address-city"))

		#DEBUG -- print (query)
		check_doc = frappe.db.sql(query,as_dict=1)

		if not check_doc or len(check_doc) <= 0:
			doc = frappe.new_doc("Address")
			doc.append('links', dict(link_doctype='Customer', link_name=self.row_dict.get("Customer-name")))
			for k in self.row_dict.keys():
				if k.startswith("Address-"):
					setattr(doc, k[8:], self.row_dict.get(k))
			doc.flags.ignore_validate = True
			doc.insert(ignore_mandatory=True)

	def create_contact(self):
		query = """
				select contact.name from `tabContact` contact,`tabDynamic Link` link,`tabContact Phone` phone
				where link.parent = contact.name and link.link_name = '{0}' and phone.parent = contact.name
				and link.link_doctype = 'Customer' and phone.phone = '{1}'
			"""
		contact_nos = self.break_contact_nos(self.row_dict.get("Contact-phone_nos"))
		if not contact_nos:
			return

		for c in contact_nos:
			if not self.check_contact_no(c):
				print ('Contact No {0} Not Valid for Customer {1}, Skipping.'.format(c,self.row_dict.get("Customer-name")))
				continue

			#DEBUG -- print (query.format(self.row_dict.get("Customer-name"),c))
			check_doc = frappe.db.sql(query.format(self.row_dict.get("Customer-name"),c),as_dict=1)

			if not check_doc or len(check_doc) <= 0:
				doc = self.get_contact_doc()
				if not doc:
					continue				

				if doc.is_new():
					doc.append('links', dict(link_doctype='Customer', link_name=self.row_dict.get("Customer-name")))

				for k in self.row_dict.keys():
					if k == 'Contact-email_id':
						continue
					if k.startswith("Contact-") and k[8:].lower() == 'phone':
						setattr(doc, k[8:], c)
					elif k.startswith("Contact-") and k[8:].lower() == 'phone_nos':
						continue
					else:
						setattr(doc, k[8:], self.row_dict.get(k))

				doc.add_phone(c, is_primary_mobile_no=1 if self.row_dict.get('Contact-is_primary_mobile_no') else 0)
				doc.flags.ignore_validate = True
				doc.save(ignore_permissions=True)

	def get_contact_doc(self):		
		doc = None
		filters = [
				["Dynamic Link", "link_doctype", "=", "Customer"],
				["Dynamic Link", "link_name", "=", self.row_dict.get("Customer-name")],
				["Dynamic Link", "parenttype", "=", "Contact"],
		]				
		contact_list = frappe.get_all("Contact", filters=filters, fields=["first_name","last_name","middle_name","name"])
		if not contact_list or len(contact_list) <=0:
			doc = self.create_new_contact_doc()

		for contact_doc in contact_list:
			#DEBUG -- print ("-"*40)
			#DEBUG -- print (contact_doc)
			#DEBUG -- print (contact_doc.first_name)
			#DEBUG -- print (contact_doc.last_name)
			#DEBUG -- print (contact_doc.middle_name)
			fn, mn, ln = self.split_name()
			if contact_doc.first_name == fn and \
				contact_doc.last_name == ln and \
				contact_doc.middle_name == mn:
				doc = frappe.get_doc('Contact',contact_doc.name)
			else:
				doc = self.create_new_contact_doc()
		#DEBUG -- print ("*"*50)
		#DEBUG -- print (doc)
		#DEBUG -- print ("*"*50)
		return doc

	def create_new_contact_doc(self):
		doc = frappe.new_doc("Contact")
		doc.first_name, doc.middle_name, doc.last_name = self.split_name()
		return doc

	def split_name(self):
		names = self.row_dict.get("Customer-customer_name").strip().split(' ')
		fn = self.row_dict.get("Contact-first_name") or (' '.join(names[0:len(names)-2]) if len(names) >= 3 else names[0])
		ln = self.row_dict.get("Contact-last_name") or names[-1]
		mn = self.row_dict.get("Contact-middle_name") or (names[-2] if len(names) >= 3 else None)
		return fn, mn, ln


	def create_email(self):
		if not self.row_dict.get("Contact-email_id"):
			return

		query = """
				select contact.name from `tabContact` contact,`tabDynamic Link` link,`tabContact Email` email
				where link.parent = contact.name and link.link_name = '{0}' and email.parent = contact.name
				and link.link_doctype = 'Customer' and email.email_id = '{1}'
			"""
		print (query.format(self.row_dict.get("Customer-name"),self.row_dict.get("Contact-email_id")))

		check_doc = frappe.db.sql(query.format(self.row_dict.get("Customer-name"),self.row_dict.get("Contact-email_id")),as_dict=1)

		if not check_doc or len(check_doc) <= 0:
			doc = self.get_contact_doc() #frappe.new_doc("Contact")
			if not doc:
				return

			if doc.is_new():
				doc.append('links', dict(link_doctype='Customer', link_name=self.row_dict.get("Customer-name")))

			for k in self.row_dict.keys():
				if k == 'Contact-email_id':
					continue
				if k == 'Contact-phone_nos' or k == 'Contact-phone':
					continue
				if k.startswith("Contact-"):
					setattr(doc, k[8:], self.row_dict.get(k))

			doc.add_email(self.row_dict.get("Contact-email_id"), is_primary=True)
			doc.flags.ignore_validate = True
			doc.save(ignore_permissions=True)
	
	def break_contact_nos(self, contactno):
		if not contactno:
			return None

		#Search for '$' and Break
		contact_return = []
		contact_nos = contactno.split('$')
		for c in contact_nos:
			contact_return.extend(c.split(','))
		return contact_return

	def check_contact_no(self, contactno):
		return re.match('[0-9]',contactno)


@frappe.whitelist()
def upload():
	from frappe.utils.csvutils import read_csv_content
	rows = read_csv_content(frappe.local.uploaded_file)
	if not rows:
		frappe.throw(_("Please select a csv file"))
	frappe.enqueue(import_customers, rows=rows, now=True if len(rows) < 200 else False)

def import_customers(rows):
	DoImportCustomers(rows)
