import frappe
import json
from frappe.utils import now, cint

@frappe.whitelist()
def validate(doc, method):
	if cint(doc.is_payment_received):
		if not doc.payments:
			frappe.throw("""Please verify Payments""")

		else:
			for p in doc.payments:
				if p.amount_paid <= 0:
					frappe.throw("""Please Verify Payment Amount""")

				if p.mode_of_payment.lower() != "cash":
					if not p.reference_no and not p.bank and not p.reference_date:
						frappe.throw("""Bank Details required in Payment Details""")

@frappe.whitelist()
def make_payment_entry_with_sales_order(doc, method):
	if doc.amended_from:
		doc.payments = None
		doc.is_payment_received = 0
		doc.db_update()
		frappe.msgprint("""Did not Create any Payment Entry as the Sales Order was Amended from a Cancelled Sales Order""")	
		return

	if not cint(doc.is_payment_received):
		return 

	if not doc.payments:
		frappe.throw("""Please verify Payments""")
		

	for p in doc.payments:
		payment_entry = frappe.new_doc('Payment Entry')
		payment_entry.posting_date = doc.transaction_date
		payment_entry.company = doc.company
		payment_entry.payment_type = 'Receive'
		payment_entry.mode_of_payment = p.mode_of_payment
		payment_entry.party_type = 'Customer'
		payment_entry.party = doc.customer
		payment_entry.party_name = doc.customer_name
		payment_entry.party_address = doc.customer_address
		payment_entry.address = doc.address_display
		payment_entry.paid_to = p.account
		payment_entry.paid_from = doc.customer_account
		payment_entry.paid_amount = p.amount_paid
		payment_entry.received_amount = p.amount_paid
		payment_entry.reference_no = p.reference_no
		payment_entry.reference_date = p.reference_date
		payment_entry.cheque_bank = p.bank

		ref = payment_entry.append('references')
		ref.reference_doctype = 'Sales Order'
		ref.reference_name = doc.name
		ref.total_amount = doc.grand_total
		ref.outstanding_amount = doc.grand_total
		ref.allocated_amount = p.amount_paid

		if 'VN' in doc.naming_series:
			payment_entry.naming_series = """MAPL/VN/REC/.YYYY./.######"""
		elif 'GB' in doc.naming_series:
			payment_entry.naming_serial = """MAPL/GB/REC/.YYYY./.######"""
		elif 'RH' in doc.naming_series:
			payment_entry.naming_serial = """MAPL/RH/REC/.YYYY./.######"""

		payment_entry.save()
		payment_entry.submit()

		frappe.msgprint("Payment entry {0} Made".format(payment_entry.name))


@frappe.whitelist()
def before_cancel_sales_order(doc, method):
	from erpnext.accounts.utils import remove_ref_doc_link_from_pe
	remove_ref_doc_link_from_pe('Sales Order', doc.name)
	frappe.db.sql("""update `tabGL Entry`
		set against_voucher_type=null, against_voucher=null,
		modified=%s, modified_by=%s
		where against_voucher_type=%s and against_voucher=%s
		and voucher_no != ifnull(against_voucher, '')""",
		(now(), frappe.session.user, 'Sales Order', doc.name))
