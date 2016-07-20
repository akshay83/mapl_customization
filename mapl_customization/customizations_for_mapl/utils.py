import frappe
import json


@frappe.whitelist()
def get_party_name(party, party_type):
	doc = frappe.get_doc(party_type, party)
	if (party_type == "Customer"):
		return doc.customer_name
	else:
		return doc.supplier_name

@frappe.whitelist()
def get_primary_billing_address(party, party_type):
	party_address = frappe.db.get_value("Address", { 
			party_type.lower(): party, 
			"is_primary_address":1,
			"address_type":"Billing"
			}, "name")
	return party_address

@frappe.whitelist()
def fetch_address_details_payments_receipts(party_address):
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

		if is_vehicle==0:
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
				serial_doc.chassis_no = serials
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

@frappe.whitelist()
def get_party_balance(party, party_type, company):
	outstanding_amount = frappe.db.sql("""select sum(debit) - sum(credit)
			from `tabGL Entry` where party_type = %s and company=%s
			and party = %s""", (party_type, company, party))
	return outstanding_amount


def validate_salesinvoice(doc, method):
	if not frappe.db.get_single_value("Selling Settings", "raise_approval_for_undercut"):
		return

	print "Validate:SI::WF_ST:"+doc.workflow_state
	print "Validate:SI::Local:"+str(doc.get('__islocal'))

	if doc.workflow_state not in ["Draft"]:
		return

	if not doc.get('__islocal'):
		return

	if doc.get('__islocal') == None:
		return

	validate_undercut_salesinvoice(doc)

def on_update_salesinvoice(doc, method):
	if not frappe.db.get_single_value("Selling Settings", "raise_approval_for_undercut"):
		return 

	print "On Update:SI:WF_ST:"+doc.workflow_state
	print "On Update:SI:IL:"+str(doc.get('__islocal'))

	old_values = frappe.db.sql("""select workflow_state from `tabSales Invoice` where name=%(name)s""",{'name':doc.name},as_dict=1)
	print "On Update:SI:OVWS:"+old_values[0].workflow_state

	if old_values != None:
		if old_values[0].workflow_state in ["Draft","Pending","Approved"]:
			if doc.workflow_state in ["Rejected","Approved"]:
				return
		elif old_values[0].workflow_state not in ["Rejected"]:
			return

	validate_undercut_salesinvoice(doc)


def validate_undercut_salesinvoice(doc):
	total_selling_rate = 0
	total_avg_rate = 0
	for i in doc.items:
		total_selling_rate = total_selling_rate+i.net_amount
		item_rate = frappe.db.sql("""select ifnull(sum(incoming_rate)/sum(actual_qty),0) as avg_rate 
				from `tabStock Ledger Entry` where item_code = %(item)s""", {'item':i.item_code}, as_dict=1)
		total_avg_rate = total_avg_rate+item_rate[0].avg_rate

	if (total_selling_rate < total_avg_rate):
		doc.db_set("workflow_state", "Pending")
	else:
		doc.db_set("workflow_state", "Draft")

