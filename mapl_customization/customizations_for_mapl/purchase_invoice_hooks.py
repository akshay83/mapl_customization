import frappe
import json
import time
from frappe.utils import today
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import cstr, cint
from erpnext.stock.stock_ledger import update_entries_after
from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
from erpnext.controllers.stock_controller import update_gl_entries_after


def purchase_invoice_on_update_after_submit(doc, method):
    doc.validate()
    frappe.db.sql("""delete from `tabGL Entry` where voucher_no=%(vname)s""", {
            'vname': doc.name })
    doc.update_valuation_rate("items")
    doc.update_children()
    doc.db_update()

    if cint(doc.update_stock):
        for i in doc.items:
            update_incoming_rate_serial_no(get_serial_nos(i.serial_no), i.valuation_rate)

        frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no=%(vname)s""", {
            'vname': doc.name })

        #raw_input("Press Enter to continue...")
        doc.update_stock_ledger()

    doc.make_gl_entries(repost_future_gle=False)

    if cint(doc.update_stock):
        for i in doc.items:
            update_entries_after({
					"item_code": i.item_code, 
					"warehouse": i.warehouse,
                    "posting_time": doc.posting_time,
					"posting_date": doc.posting_date #get_fiscal_year(today())[1]
				}, allow_zero_rate=True)

    if cint(doc.update_stock):
        for i in doc.items:
            repost_se(i.item_code)
            repost_si(i.item_code)
            repost_dn(i.item_code)

    update_outstanding_amt(doc.credit_to, "Supplier", doc.supplier,doc.doctype, doc.name)

    frappe.db.commit()

def get_serial_nos(serial_no):
	return [s.strip() for s in cstr(serial_no).strip().upper().replace(',', '\n').split('\n')
		if s.strip()]

def update_incoming_rate_serial_no(serial_nos, rate):
    if not serial_nos:
        return

    for s_no in serial_nos:
        serial = frappe.get_doc('Serial No', s_no)
        serial.purchase_rate = rate
        serial.db_update()


def repost_se(item_code):
    se_list = frappe.db.sql("""select distinct se.name, se.docstatus
                from `tabStock Entry` se, `tabStock Entry Detail` se_detail
                where se.name=se_detail.parent and se.docstatus = 1 and se.purpose='Material Transfer'
                and se_detail.item_code = %(item_code)s 
                order by se.posting_date asc""", { 'item_code': item_code }, as_dict=1)

    for se in se_list:
        frappe.db.sql("""delete from `tabGL Entry` where voucher_no=%(vname)s""", {
            'vname': se.name })

        frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_no=%(vname)s""", {
            'vname': se.name })

        se_doc = frappe.get_doc("Stock Entry", se.name)
        se_doc.calculate_rate_and_amount(force=True)

        se_doc.update_children()
        se_doc.db_update()
        se_doc.update_stock_ledger()

        se_doc.make_gl_entries()


def repost_si(item_code):
    si_list = frappe.db.sql("""select distinct si.name, si.docstatus
                from `tabSales Invoice` si, `tabSales Invoice Item` si_item
                where si.name=si_item.parent and si.docstatus = 1 and si.update_stock=1
                and si_item.item_code=%(item_code)s 
                order by si.posting_date asc""", { 'item_code': item_code }, as_dict=1)

    for si in si_list:
        si_doc = frappe.get_doc("Sales Invoice", si.name)
        si_doc.docstatus = 2
        si_doc.update_stock_ledger()
        frappe.db.sql("""delete from `tabGL Entry` 
				where voucher_type='Sales Invoice' and voucher_no=%s""", si.name)
			
        si_doc = frappe.get_doc("Sales Invoice", si.name)
        si_doc.docstatus = 1
        si_doc.update_stock_ledger()
        si_doc.make_gl_entries()

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

