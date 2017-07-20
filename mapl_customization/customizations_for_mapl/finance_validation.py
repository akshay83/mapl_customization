import frappe
from frappe.utils import cint

def sales_invoice_validate(doc, method):
	finance_validate(doc, method)
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
