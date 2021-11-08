import frappe

def payment_entry_validate(doc, method):
	if doc.ignore_validate_hook:
		return	
	from frappe.utils import money_in_words
	doc.in_words = money_in_words(doc.paid_amount);
