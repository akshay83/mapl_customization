import frappe
import json

@frappe.whitelist()
def fetch_address_details_payments_receipts(party, party_type, party_address = None):
	if (not party_address):
		party_address = frappe.db.get_value("Address", {party_type.lower(): party, "is_primary_address":1}, "name")

	from erpnext.utilities.doctype.address.address import get_address_display
	return get_address_display(party_address)
	

@frappe.whitelist()
def validate_input_serial(args,rows,is_vehicle=1):
	if isinstance(args, basestring):
		args = json.loads(args)

	serial_keys = args.keys()

	int_rows = int(float(rows))
	rows = str(int_rows)
	is_vehicle = int(float(is_vehicle))

	for i in range(1, int_rows):
		if is_vehicle==1:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Chassis No At Row "+rows)

			if "engine_no_"+rows not in serial_keys:
				frappe.throw("Check Engine No At Row "+rows)

			if "key_no_"+rows not in serial_keys:
				frappe.throw("Check Key No At Row "+rows)

		if is_vehicle!=0:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Serial No At Row "+rows)

	return True

def purchase_receipt_on_submit(doc,method):
	for i in doc.items:
		if i.is_vehicle == 1:
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")

			index = 0
			for serials in chassis_nos:
				serial_doc = frappe.get_doc("Serial No",serials)
				serial_doc.is_vehicle = 1
				serial_doc.engine_no = engine_nos[index]
				serial_doc.key_no = key_nos[index]
				serial_doc.save()
				index = index+1

def purchase_receipt_validate(doc, method):
	for i in doc.items:
		if i.is_vehicle == 1:
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")

			if len(chassis_nos) != len(engine_nos) != len(key_nos):
				frappe.throw("Check Entered Serial Nos Values")

def check_receipt_in_journal_entry(doc, method):
	if (doc.receipt_link or doc.payment_link):
		frappe.throw("Cannot Cancel/Delete - Linked With a Receipt/Payments");
