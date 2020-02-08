import frappe
import HTMLParser
from frappe.utils import cint

def sales_invoice_validate(doc, method):
	negative_stock_validation(doc, method)
	validate_stock_entry_serial_no(doc, method)
	#validate_grand_total(doc, method)
	validate_gst_state(doc, method)

def sales_on_submit_validation(doc, method):
	vehicle_validation(doc, method)
	validate_hsn_code(doc, method)
	taxes_and_charges_validation(doc, method)
	finance_validate(doc, method)
	validate_grand_total(doc, method)


def validate_gst_state(doc, method):
	parser = HTMLParser.HTMLParser()
	ship_state = frappe.db.get_value("Address", doc.shipping_address_name, "gst_state")
	if not ship_state:
		frappe.throw("""Please update Correct GST State in Shipping Address and then Try Again""")

	bill_state = frappe.db.get_value("Address", doc.customer_address, "gst_state")
	if not bill_state:
		frappe.throw("""Please update Correct GST State in Billing Address and then Try Again""")

	from frappe.contacts.doctype.address.address import get_address_display
	da = get_address_display(doc.customer_address)
	if da != parser.unescape(doc.address_display):
		frappe.throw("""Please use 'Update Address' under Address to update the correct Billing Address in the Document""")

	da = get_address_display(doc.shipping_address_name)
	if da != parser.unescape(doc.shipping_address):
		frappe.throw("""Please use 'Update Address' under Address to update the correct Shipping Address in the Document""")


	if doc.taxes_and_charges == 'Out of State GST' and ship_state == 'Madhya Pradesh':
		if doc.special_invoice and doc.special_invoice == 'SEZ Supply':
			return
		frappe.throw("""Please Check Correct Shipping Address/Taxes""")

	if doc.taxes_and_charges == 'In State GST' and ship_state != 'Madhya Pradesh':
		frappe.throw("""Please Check Correct Shipping Address/Taxes""")


def sales_order_validate(doc, method):
	finance_validate(doc, method)

def finance_validate(doc, method):
	if doc.is_finance and not doc.finance_charges:
		frappe.throw('Need Finance Details')

def vehicle_validation(doc, method):
	for i in doc.items:
		if cint(i.is_vehicle) and len(doc.items)>1:
			frappe.throw("A Sales Invoice can have only Single Vehicle and No Other Item")

		if cint(i.is_vehicle) and len(i.serial_no.strip(' \n').split('\n'))>1:
			frappe.throw("A Sales Invoice can have only ONE Vehicle")

def negative_stock_validation(doc, method):
	for i in doc.items:
		if (i.actual_qty <= 0 and (i.item_code and frappe.db.get_value("Item", i.item_code, "is_stock_item"))):
			frappe.msgprint("Negative Stock for {0}, Please verify before Submitting".format(i.item_code))

def taxes_and_charges_validation(doc, method):
	if not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
		if doc.total_taxes_and_charges == 0:
			frappe.throw("No Taxes and Charges Applied, Please ensure if this is Ok!!")
		else:
			for i in doc.items:
				if i.net_rate == i.rate:
					frappe.throw("""Taxes Does not seems to be Applied on Item {0}, Please ensure if this is Ok!!""".format(i.item_code))

def validate_hsn_code(doc, method):
	for i in doc.items:
		if not i.gst_hsn_code:
			frappe.throw("HSN Code not found for {0}".format(i.item_code))

def validate_grand_total(doc, method):
	if not doc.grand_total:
		frappe.throw("Invoice Total Should Be Non - Zero. Please Check Total Values")

def validate_stock_entry_serial_no(doc, method):
	if doc.doctype.lower() != 'stock entry' and doc.is_return:
		return

	for i in doc.items:
		warehouse = None
		if doc.doctype.lower() != 'stock entry':
			warehouse = i.warehouse
		else:
			warehouse = i.s_warehouse

		if i.serial_no and warehouse:
			snos = i.serial_no.strip(' \n').split('\n')
			for s in snos:
				if warehouse != frappe.db.get_value("Serial No", s, "warehouse"):
					frappe.throw("""Item {0} with Serial No {1} Not in Warehouse {2}""".format(i.item_code, s, warehouse))


