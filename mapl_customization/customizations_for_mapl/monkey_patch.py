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

#Patch to Use mapl_customization.customizations_for_mapl.utils.check_average_purchase in Workflow Condition
#Condition in such a way that if CAP return 0 then only Allowed Role can Approve the Sales Invoice/Or Other Document
#To use condition like this - Create two Conditions 1. Which can allow all the roles to approve depending on condition == 1
#2. Which allows only allowed role to Approove depending on Condition == 0
def get_workflow_safe_globals():
	# access to frappe.db.get_value, frappe.db.get_list, and date time utils.
	from mapl_customization.customizations_for_mapl.utils import check_average_purchase as cap
	return dict(
		frappe=frappe._dict(
			db=frappe._dict(get_value=frappe.db.get_value, get_list=frappe.db.get_list),
			session=frappe.session,
			utils=frappe._dict(
				now_datetime=frappe.utils.now_datetime,
				add_to_date=frappe.utils.add_to_date,
				get_datetime=frappe.utils.get_datetime,
				now=frappe.utils.now,
			),
		),
		mapl_customization=frappe._dict(
			utils=frappe._dict(check_average_purchase=cap)
		)
	)

def monkey_patch_safeworkflow():
	from frappe.model import workflow
	workflow.get_workflow_safe_globals = get_workflow_safe_globals

def monkey_patch_payment_entry_validate():
	from erpnext.accounts.doctype.payment_entry import payment_entry
	payment_entry.PaymentEntry.add_party_gl_entries = add_party_gl_entries

def do_monkey_patch():
	print ('-'*20,'MONKEY PATCH MAPL-CUSTOMIZATION','-'*10)
	monkey_patch_payment_entry_validate()

	from mapl_customization.customizations_for_mapl.gst_monkey import monkey_patch_gst_validate_document_name
	monkey_patch_gst_validate_document_name()

	from mapl_customization.customizations_for_mapl.monkey_patch_salary_slip import monkey_patch_for_salary_slip
	monkey_patch_for_salary_slip()

	monkey_patch_safeworkflow()
