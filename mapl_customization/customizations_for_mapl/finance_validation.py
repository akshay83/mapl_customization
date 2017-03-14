import frappe

def sales_invoice_validate(doc, method):
	finance_validate(doc, method)

def sales_order_validate(doc, method):
	finance_validate(doc, method)

def finance_validate(doc, method):
	if doc.is_finance and not doc.finance_charges:
		frappe.throw('Need Finance Details')

def payment_entry_validate(doc, method):
	from frappe.utils import money_in_words
	doc.in_words = money_in_words(doc.paid_amount);
