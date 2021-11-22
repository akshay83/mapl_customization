import frappe
import json
import datetime
from frappe.utils import cint, getdate, today
from six import string_types

def purchase_receipt_on_submit(doc,method):
	validate_hsn_code(doc, method)
	for i in doc.items:
		if cint(i.is_vehicle):
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n") if i.engine_nos else []
			key_nos = i.key_nos.split("\n") if i.key_nos else []
			color = i.color.split("\n")

			index = 0
			for serials in chassis_nos:
				serial_doc = frappe.get_doc("Serial No",serials)
				serial_doc.is_vehicle = 1
				serial_doc.is_electric_vehicle = i.is_electric_vehicle
				serial_doc.chassis_no = serials
				serial_doc.engine_no = engine_nos[index] if len(engine_nos) > index else None
				serial_doc.key_no = key_nos[index] if len(key_nos) > index else None
				serial_doc.color = color[index]
				serial_doc.year_of_manufacture = i.year_of_manufacture
				serial_doc.save()
				index = index+1

def validate_hsn_code(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	for i in doc.items:
		if not i.gst_hsn_code:
			frappe.throw("HSN Code not found for {0}".format(i.item_code))

def purchase_receipt_validate(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	for i in doc.items:
		if cint(i.is_vehicle):
			chassis_nos = i.serial_no.split("\n")
			color = i.color.split("\n")
			engine_nos = i.engine_nos.split("\n") if i.engine_nos else []
			key_nos = i.key_nos.split("\n") if i.key_nos else []

			throw_error = False
			if len(chassis_nos) != len(engine_nos) and not cint(i.is_electric_vehicle):
				throw_error = True
			if not throw_error and len(engine_nos) != len(key_nos) and not cint(i.is_electric_vehicle):
				throw_error = True
			if not throw_error and len(key_nos) != len(color) and not cint(i.is_electric_vehicle):
				throw_error = True
			if not throw_error and cint(i.is_electric_vehicle) and len(color) != len(chassis_nos):
				throw_error = True

			if throw_error:
				frappe.throw("Check Entered Serial Nos Values")

			if not i.year_of_manufacture:
				frappe.throw("Check Year of Manufacture")

def purchase_receipt_before_submit(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	purchase_receipt_serial_no_validate_before_submit(doc, method)
	purchase_item_rate_validate_before_submit(doc, method)
	purchase_invoice_gst_check(doc, method)

def purchase_receipt_serial_no_validate_before_submit(doc, method):
	if doc.is_return:
		return

	for i in doc.items:
		if not i.serial_no:
			continue

		snos = i.serial_no.strip(' \n').split('\n')
		snos = "|".join(snos)

		rows = frappe.db.sql("""select name from `tabSerial No` where name regexp '%s'""" % snos)

		for r in rows:
			frappe.throw("""Atleast One of The Serial No(s) for Item {0} Already Exists. Please Verify""".format(i.item_code))

def purchase_item_rate_validate_before_submit(doc, method):
	for i in doc.items:
		if not i.rate:
			frappe.throw("""Please Check Item Rates, Should Be Non-Zero. Item {0}""".format(i.item_code))

def purchase_invoice_gst_check(doc, method):
	from html.parser import HTMLParser
	state = frappe.db.get_value("Address", doc.supplier_address, "gst_state")
	if not state:
		frappe.throw("""Please update Correct GST State in Supplier Address and then Try Again""")

	from frappe.contacts.doctype.address.address import get_address_display
	parser = HTMLParser()
	da = get_address_display(doc.supplier_address)
	if da != parser.unescape(doc.address_display):
		frappe.throw("""Please use 'Update Address' under Address to update the correct Address in the Document""")

	if doc.taxes_and_charges == 'Out of State GST' and state == 'Madhya Pradesh':
		frappe.throw("""Please Check Correct Address/GSTIN""")

	if (doc.taxes_and_charges == 'In State GST' or not doc.taxes_and_charges or doc.taxes_and_charges == "") and state != 'Madhya Pradesh':
		frappe.throw("""Please Check Correct Address/GSTIN""")