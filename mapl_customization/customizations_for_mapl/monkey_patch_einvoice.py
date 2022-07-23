import frappe
from frappe import _
from frappe.utils.data import getdate, format_date, flt
from erpnext.regional.india.e_invoice.utils import validate_address_fields, sanitize_for_json, get_gst_accounts, update_other_charges, validate_eligibility

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

def update_invoice_taxes(invoice, invoice_value_details):
    gst_accounts = get_gst_accounts(invoice.company)
    gst_accounts_list = [d for accounts in gst_accounts.values() for d in accounts if d]

    invoice_value_details.total_cgst_amt = 0
    invoice_value_details.total_sgst_amt = 0
    invoice_value_details.total_igst_amt = 0
    invoice_value_details.total_cess_amt = 0
    invoice_value_details.total_other_charges = 0
    considered_rows = []

    for t in invoice.taxes:
        tax_amount = t.base_tax_amount_after_discount_amount
        #--DEBUG--print ("GST Account:", t.account_head in gst_accounts_list)
        if t.account_head in gst_accounts_list:
            if t.account_head in gst_accounts.cess_account:
                # using after discount amt since item also uses after discount amt for cess calc
                invoice_value_details.total_cess_amt += abs(t.base_tax_amount_after_discount_amount)

            for tax_type in ['igst', 'cgst', 'sgst']:
                if t.account_head in gst_accounts[f'{tax_type}_account']:

                    invoice_value_details[f'total_{tax_type}_amt'] += abs(tax_amount)
                update_other_charges(t, invoice_value_details, gst_accounts_list, invoice, considered_rows)
        #Monkey-here, as there is no provision for subsidy in erpnext
        #else:
            #invoice_value_details.total_other_charges += abs(tax_amount)
        elif "subsidy" in t.account_head.lower():
            invoice_value_details.invoice_discount_amt += abs(tax_amount)
        else:
            invoice_value_details.total_other_charges += abs(tax_amount)
            
    return invoice_value_details

def validate_einvoice_fields(doc):
    invoice_eligible = validate_eligibility(doc)

    if not invoice_eligible:
        return

    is_admin = (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles())
    if doc.docstatus == 0 and doc._action == 'save':
        #Monkey Here
        if doc.irn and not is_admin:
            frappe.throw(_('You cannot edit the invoice after generating IRN'), title=_('Edit Not Allowed'))
        if len(doc.name) > 16:
            raise_document_name_too_long_error()

        doc.einvoice_status = 'Pending'

    elif doc.docstatus == 1 and doc._action == 'submit' and not doc.irn:
        frappe.throw(_('You must generate IRN before submitting the document.'), title=_('Missing IRN'))

    elif doc.irn and doc.docstatus == 2 and doc._action == 'cancel' and not doc.irn_cancelled and not is_admin:
        frappe.throw(_('You must cancel IRN before cancelling the document.'), title=_('Cancel Not Allowed'))

def monkey_patch_einvoice_get_doc_details():
    print ("Monkey Patching E-Invoice----------------------")
    from erpnext.regional.india.e_invoice import utils
    utils.get_doc_details = get_doc_details
    utils.get_party_details = get_party_details
    utils.raise_document_name_too_long_error = raise_document_name_too_long_error
    utils.get_return_doc_reference = get_return_doc_reference
    utils.update_invoice_taxes = update_invoice_taxes
    utils.validate_einvoice_fields = validate_einvoice_fields

