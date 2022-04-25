import frappe
from frappe.utils.data import getdate, format_date
from erpnext.regional.india.e_invoice.utils import validate_address_fields, sanitize_for_json

def get_doc_details(invoice):
    if getdate(invoice.posting_date) < getdate('2021-01-01'):
        frappe.throw(_('IRN generation is not allowed for invoices dated before 1st Jan 2021'), title=_('Not Allowed'))

    invoice_type = 'CRN' if invoice.is_return else 'INV'

    #monkey-here
    invoice_name = invoice.reporting_name
    invoice_date = format_date(invoice.posting_date, 'dd/mm/yyyy')

    return frappe._dict(dict(
        invoice_type=invoice_type,
        invoice_name=invoice_name,
        invoice_date=invoice_date
    ))

def get_party_details(address_name, skip_gstin_validation=False):
    addr = frappe.get_doc('Address', address_name)

    validate_address_fields(addr, skip_gstin_validation)

    if addr.gst_state_number == 97:
        # according to einvoice standard
        addr.pincode = 999999

    #monkey-here - to test sandbox with taxpro
    if frappe.get_cached_doc("E Invoice Settings").sandbox_mode:
        if addr.gstin == '23AABCM2024J1ZY':
            addr.gstin = '34AACCC1596Q002'
            addr.pincode = '605001'
            addr.gst_state_number = '34'

    party_address_details = frappe._dict(dict(
		legal_name=sanitize_for_json(addr.address_title),
		location=sanitize_for_json(addr.city),
		pincode=addr.pincode, 
        gstin=addr.gstin,
		state_code=addr.gst_state_number,
		address_line1=sanitize_for_json(addr.address_line1),
		address_line2=sanitize_for_json(addr.address_line2) if addr.address_line2 else None #Monkey Here
    ))

    return party_address_details

def raise_document_name_too_long_error():
    pass

def get_return_doc_reference(invoice):
    invoice_date = frappe.db.get_value("Sales Invoice", invoice.return_against, "posting_date")
    #monkey-here
    reporting_name = frappe.db.get_value("Sales Invoice", invoice.return_against, "reporting_name")
    return frappe._dict(
        dict(invoice_name=reporting_name, invoice_date=format_date(invoice_date, "dd/mm/yyyy"))
    )

def monkey_patch_einvoice_get_doc_details():
    print ("Monkey Patching E-Invoice----------------------")
    from erpnext.regional.india.e_invoice import utils
    utils.get_doc_details = get_doc_details
    utils.get_party_details = get_party_details
    utils.raise_document_name_too_long_error = raise_document_name_too_long_error
    utils.get_return_doc_reference = get_return_doc_reference

