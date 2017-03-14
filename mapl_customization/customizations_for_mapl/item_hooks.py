import frappe
from erpnext.controllers.accounts_controller import get_taxes_and_charges 

def item_validate(doc, method):
	if doc.taxes_template and not doc.taxes:
		doc.extend("taxes",get_taxes_and_charges('Item Taxes Template', doc.taxes_template))

