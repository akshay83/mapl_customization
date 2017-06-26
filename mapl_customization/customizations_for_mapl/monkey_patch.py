import frappe
import erpnext

from frappe import _
from frappe.core.doctype.doctype.doctype import validate_fields_for_doctype
from frappe.custom.doctype.customize_form.customize_form import docfield_properties
from frappe.utils import flt

def save_customization(self):
	if not self.doc_type:
		return

	if docfield_properties.has_key('allow_on_submit'):
		del docfield_properties['allow_on_submit']

	self.set_property_setters()
	self.set_allow_on_submit()
	self.update_custom_fields()
	validate_fields_for_doctype(self.doc_type)

	frappe.msgprint(_("Completed Updating {0}").format(_(self.doc_type)))
	frappe.clear_cache(doctype=self.doc_type)
	self.fetch_to_customize()

def set_allow_on_submit(self):
	meta = frappe.get_meta(self.doc_type)

	for df in self.get("fields"):
		if df.get("__islocal"):
			continue

		meta_df = meta.get("fields", {"fieldname": df.fieldname})

		if not meta_df or meta_df[0].get("is_custom_field"):
			continue    

		if df.get("allow_on_submit"):
				self.make_property_setter(property="allow_on_submit", value=df.get("allow_on_submit"),
					property_type="Check", fieldname=df.fieldname)

def allow_transition_from_0_to_2(self, docstatus):
		"""Ensures valid `docstatus` transition.
		Valid transitions are (number in brackets is `docstatus`):
		- Save (0) > Save (0)
		- Save (0) > Submit (1)
		- Save (0) > Cancel (2)
		- Submit (1) > Submit (1)
		- Submit (1) > Cancel (2)
		If docstatus is > 2, it will throw exception as document is deemed queued
		"""

		if self.docstatus > 2:
			frappe.throw(_('This document is currently queued for execution. Please try again'),
				title=_('Document Queued'), indicator='red')

		if not self.docstatus:
			self.docstatus = 0
		if docstatus==0:
			if self.docstatus==0:
				self._action = "save"
			elif self.docstatus==1:
				self._action = "submit"
				self.check_permission("submit")
			#else:
			#	raise frappe.DocstatusTransitionError, _("Cannot change docstatus from 0 to 2")

		elif docstatus==1:
			if self.docstatus==1:
				self._action = "update_after_submit"
				self.check_permission("submit")
			elif self.docstatus==2:
				self._action = "cancel"
				self.check_permission("cancel")
			else:
				raise frappe.DocstatusTransitionError, _("Cannot change docstatus from 1 to 0")

		elif docstatus==2:
			raise frappe.ValidationError, _("Cannot edit cancelled document")


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
			"account_currency": self.party_account_currency
		})
		
		# Changed the following line in Monkey Patch
		dr_or_cr = "credit" if self.payment_type == "Receive" else "debit"
		
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


def validate_payment_against_negative_invoice(self):
	pass

def monkey_patch_payment_entry_validate():
	from erpnext.accounts.doctype.payment_entry import payment_entry
	payment_entry.PaymentEntry.validate_payment_against_negative_invoice = validate_payment_against_negative_invoice
	payment_entry.PaymentEntry.add_party_gl_entries = add_party_gl_entries

def monkey_patch_allow_transition_from_0_to_2():
	from frappe.model.document import Document
	Document.check_docstatus_transition = allow_transition_from_0_to_2

def monkey_patch_for_allow_on_submit():
	from frappe.custom.doctype.customize_form.customize_form import CustomizeForm
	CustomizeForm.set_allow_on_submit = set_allow_on_submit
	CustomizeForm.save_customization = save_customization

def monkey_patch_for_serial_validation():
	from erpnext.stock.doctype.serial_no import serial_no
	from monkey_patch_serial import validate_serial_no as vsn
	serial_no.validate_serial_no = vsn

	from monkey_patch_serial import set_purchase_details as spd
	serial_no.SerialNo.set_purchase_details = spd 

def do_monkey_patch():
	monkey_patch_for_allow_on_submit()
	monkey_patch_allow_transition_from_0_to_2()
	monkey_patch_for_serial_validation()
	monkey_patch_payment_entry_validate()
