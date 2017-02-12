import frappe

def sales_invoice_validate(doc, method):
	finance_validate(doc, method)

def sales_order_validate(doc, method):
	finance_validate(doc, method)

def finance_validate(doc, method):
	if doc.is_finance and not doc.finance_charges:
		frappe.throw('Need Finance Details')
