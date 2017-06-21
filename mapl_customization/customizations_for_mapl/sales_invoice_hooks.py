import frappe
import json
import time
from frappe.utils import today
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import cstr, cint
from erpnext.stock.stock_ledger import update_entries_after
from erpnext.controllers.stock_controller import update_gl_entries_after


def sales_invoice_on_update_after_submit(doc, method):
	for i in doc.items:
		if i.delivered_qty > 0:
			frappe.throw("Items Delivered on Delivery Note Against this Invoice, Please Cancel the Delivery Note(s) before Updating")

	doc.validate()
	doc.docstatus = 2
	doc.db_update()

	if cint(doc.update_stock):
		doc.update_stock_ledger()

	frappe.db.sql("""delete from `tabGL Entry` where voucher_no=%(vname)s""", {
            'vname': doc.name })

	doc.docstatus = 1
	doc.title = doc.customer_name
	doc.db_update()

	if cint(doc.update_stock):
		doc.update_stock_ledger()

	doc.make_gl_entries()

	frappe.db.commit()


def repost_dn(item_code):
    dn_list = frappe.db.sql("""select distinct dn.name, dn.docstatus
		from `tabDelivery Note` dn, `tabDelivery Note Item` dn_item
		where dn.name=dn_item.parent and dn.docstatus = 1 and dn_item.item_code = %(item_code)s
		order by dn.posting_date asc""", { 'item_code': item_code }, as_dict=1)
		
    for dn in dn_list:
        dn_doc = frappe.get_doc("Delivery Note", dn.name)
        dn_doc.docstatus = 2
        dn_doc.update_prevdoc_status()
        dn_doc.update_stock_ledger()
        dn_doc.cancel_packing_slips()
        frappe.db.sql("""delete from `tabGL Entry` 
				where voucher_type='Delivery Note' and voucher_no=%s""", dn.name)

        dn_doc = frappe.get_doc("Delivery Note", dn.name)
        dn_doc.docstatus = 1
        dn_doc.on_submit()

