import frappe
from frappe.utils import cint

def sales_invoice_validate(doc, method):
	finance_validate(doc, method)
	negative_stock_validation(doc, method)
	validate_hsn_code(doc, method)
	vehicle_validation(doc, method)

def sales_order_validate(doc, method):
	finance_validate(doc, method)

def finance_validate(doc, method):
	if doc.is_finance and not doc.finance_charges:
		frappe.throw('Need Finance Details')

def payment_entry_validate(doc, method):
	from frappe.utils import money_in_words
	doc.in_words = money_in_words(doc.paid_amount);

def vehicle_validation(doc, method):
	for i in doc.items:
		if cint(i.is_vehicle) and len(doc.items)>1:
			frappe.throw("A Sales Invoice can have only Single Vehicle and No Other Item")

		if cint(i.is_vehicle) and len(i.serial_no.split('\n'))>1:
			frappe.throw("A Sales Invoice can have only ONE Vehicle")

def negative_stock_validation(doc, method):
	for i in doc.items:
		if (i.actual_qty <= 0 and (i.item_code and frappe.db.get_value("Item", i.item_code, "is_stock_item"))):
			frappe.msgprint("Negative Stock for {0}, Please verify before Submitting".format(i.item_code))

def validate_hsn_code(doc, method):
	for i in doc.items:
		if not i.gst_hsn_code:
			frappe.throw("HSN Code not found for {0}".format(i.item_code))
