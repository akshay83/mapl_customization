import frappe
import erpnext

from frappe import _
from frappe.core.doctype.doctype.doctype import validate_fields_for_doctype
from frappe.utils import flt

def add_party_gl_entries(self, gl_entries):
	if self.party_account:
		if self.payment_type=="Receive":
			against_account = self.paid_to
		else:
			against_account = self.paid_from

		party_gl_dict = self.get_gl_dict({
			"account": self.party_account,
			"party_type": self.party_type,
			"party": self.party,
			"against": against_account,
			"account_currency": self.party_account_currency,
			"cost_center": self.cost_center
		}, item=self)

		# Monkey Here
		dr_or_cr = "credit" if self.payment_type == "Receive" else "debit"
		#dr_or_cr = "credit" if erpnext.get_party_account_type(self.party_type) == 'Receivable' else "debit"

		for d in self.get("references"):
			gle = party_gl_dict.copy()
			gle.update({
				"against_voucher_type": d.reference_doctype,
				"against_voucher": d.reference_name
			})

			allocated_amount_in_company_currency = flt(flt(d.allocated_amount) * flt(d.exchange_rate),
				self.precision("paid_amount"))

			gle.update({
				dr_or_cr + "_in_account_currency": d.allocated_amount,
				dr_or_cr: allocated_amount_in_company_currency
			})

			gl_entries.append(gle)

		if self.unallocated_amount:
			base_unallocated_amount = base_unallocated_amount = self.unallocated_amount * \
				(self.source_exchange_rate if self.payment_type=="Receive" else self.target_exchange_rate)

			gle = party_gl_dict.copy()

			gle.update({
				dr_or_cr + "_in_account_currency": self.unallocated_amount,
				dr_or_cr: base_unallocated_amount
			})

			gl_entries.append(gle)

def monkey_patch_payment_entry_validate():
	from erpnext.accounts.doctype.payment_entry import payment_entry
	payment_entry.PaymentEntry.add_party_gl_entries = add_party_gl_entries

def do_monkey_patch():
	print ('-'*20,'MONKEY PATCH MAPL-CUSTOMIZATION','-'*10)
	monkey_patch_payment_entry_validate()

	from mapl_customization.customizations_for_mapl.gst_monkey import monkey_patch_gst
	monkey_patch_gst()

	from mapl_customization.customizations_for_mapl.monkey_patch_salary_slip import monkey_patch_for_salary_slip
	monkey_patch_for_salary_slip()
