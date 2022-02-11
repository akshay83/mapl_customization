import frappe
from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry

def payment_entry_validate(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	from frappe.utils import money_in_words
	doc.in_words = money_in_words(doc.paid_amount)

class CustomPaymentEntry(PaymentEntry):
	def get_print_settings(self):
		print_setting_fields = super(PaymentEntry, self).get_print_settings()
		print_setting_fields += ['print_finance_details_in_receipt']
		return print_setting_fields