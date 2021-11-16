import frappe

def sales_order_validate(doc, method):
	if doc.get('ignore_validate_hook'):
		return			
	finance_validate(doc, method)

def finance_validate(doc, method):
	if doc.is_finance and not doc.finance_charges:
		frappe.throw('Need Finance Details')