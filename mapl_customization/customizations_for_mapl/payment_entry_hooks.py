import frappe

def payment_entry_on_update_after_submit(doc, method):
	if doc.difference_amount:
		frappe.throw(_("Difference Amount must be zero"))

	doc.validate()
	doc.docstatus = 2
	doc.db_update()
	doc.update_advance_paid()

	frappe.db.sql("""delete from `tabGL Entry` where voucher_no=%(vname)s""", {
            'vname': doc.name })

	doc.docstatus = 1
	doc.title = doc.party_name
	doc.db_update()

	doc.setup_party_account_field()
	doc.make_gl_entries()
	doc.update_advance_paid()

	frappe.db.commit()
