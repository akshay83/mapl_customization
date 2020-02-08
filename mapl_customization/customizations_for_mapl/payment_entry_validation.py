import frappe

def payment_entry_validate(doc, method):
	from frappe.utils import money_in_words
	doc.in_words = money_in_words(doc.paid_amount);
