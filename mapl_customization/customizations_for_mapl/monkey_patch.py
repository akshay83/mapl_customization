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

def validate_entries_for_advance(self):
	for d in self.get('accounts'):
		if d.reference_type not in ("Sales Invoice", "Purchase Invoice", "Journal Entry"):
			if (d.party_type == 'Customer' and flt(d.credit) > 0) or \
					(d.party_type == 'Supplier' and flt(d.debit) > 0):
				#Monkey Here
				#if d.is_advance=="No":
				#	msgprint(_("Row {0}: Please check 'Is Advance' against Account {1} if this is an advance entry.").format(d.idx, d.account), alert=True)
				#elif d.reference_type in ("Sales Order", "Purchase Order") and d.is_advance != "Yes":
				if d.reference_type in ("Sales Order", "Purchase Order") and d.is_advance != "Yes":
					frappe.throw(_("Row {0}: Payment against Sales/Purchase Order should always be marked as advance").format(d.idx))

			if d.is_advance == "Yes":
				if d.party_type == 'Customer' and flt(d.debit) > 0:
					frappe.throw(_("Row {0}: Advance against Customer must be credit").format(d.idx))
				elif d.party_type == 'Supplier' and flt(d.credit) > 0:
					frappe.throw(_("Row {0}: Advance against Supplier must be debit").format(d.idx))

def monkey_patch_payment_entry_validate():
	from erpnext.accounts.doctype.payment_entry import payment_entry
	payment_entry.PaymentEntry.add_party_gl_entries = add_party_gl_entries

def monkey_patch_salary_slip_for_rounding():
	from erpnext.hr.doctype.salary_slip.salary_slip import SalarySlip
	from monkey_patch_salary_slip import get_amount_based_on_payment_days as gabopd
	SalarySlip.get_amount_based_on_payment_days = gabopd

def monkey_patch_journal_entry_validation_advance():
	from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
	JournalEntry.validate_entries_for_advance = validate_entries_for_advance

def do_monkey_patch():
	monkey_patch_payment_entry_validate()
	monkey_patch_salary_slip_for_rounding()
	monkey_patch_journal_entry_validation_advance()
