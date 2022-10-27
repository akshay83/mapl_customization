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

	def make_gl_entries(self, cancel=0, adv_adj=0):
		gl_entries = self.build_gl_map()
		#Activate when you want system to post CB Amount to an Account
		#gl_entries = self.add_cashback_gl_entries(gl_entries)
		gl_entries = process_gl_map(gl_entries)
		make_gl_entries(gl_entries, cancel=cancel, adv_adj=adv_adj)

	def add_cashback_gl_entries(self, gl_entries):
		if self.cash_back_amount and self.cash_back_amount > 0 and self.instant_cash_back_provider:
			icb_account = frappe.db.get_value("Instant Cashback Providers", self.instant_cash_back_provider, "linked_account")
			gl_entries.append(self.get_gl_dict({
						"account": icb_account,
						"against": self.party,
						"debit_in_account_currency": self.cash_back_amount,
						"debit": self.cash_back_amount,
						"cost_center": self.cost_center			
					}
				)
			)
			gl_entries.append(self.get_gl_dict({
						"account": self.party_account,
						"against": self.party,
						"credit_in_account_currency": self.cash_back_amount,
						"credit": self.cash_back_amount,
						"cost_center": self.cost_center			
					}
				)
			)
		return gl_entries
