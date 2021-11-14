import frappe
from frappe.utils import cint, getdate

@frappe.whitelist()
def get_doc_list_as_per_transactions(transaction_doctype, filters=None, \
            from_date=None, to_date=None, page_length=None, order_by=None, non_stock=False):
    if page_length:
        page_length = cint(page_length)
    default_fields = ["voucher_type, voucher_no, posting_date"]
    default_order_by = "posting_date"
    default_records_length = 10000
    date_filters = []
    if from_date:
        date_filters.extend([
            ["posting_date", ">=", from_date]
        ])
    if to_date:
        date_filters.extend([
            ["posting_date", "<=", to_date]
        ])
    if filters:
        filters.extend(date_filters)
    else:
        filters = date_filters
    document_list = None
    if not non_stock:
        document_list = get_complete_list(transaction_doctype, filters=filters, 
                       fields=default_fields,
                       to_record = default_records_length if not page_length else page_length,
                       order_by=default_order_by if not order_by else order_by)
    else:
        document_list = mapl_customization.customizations_for_mapl.utils.get_non_stock_sales_purchase(from_date=from_date, to_date=to_date)
    doc_list = []
    for doc in document_list:
        doc_list.extend([frappe.get_doc(doc['voucher_type'], doc['voucher_no']).as_dict()])
    return doc_list

@frappe.whitelist()
def get_doc_list(doctype, filters=None, fields=None, from_record=0, to_record=None, order_by=None):
    if from_record:
        from_record = cint(from_record)
    if to_record:
        to_record = cint(to_record)
    document_list = get_complete_list(doctype, filters=filters, fields="name" if not fields else fields, from_record=from_record, to_record=to_record, order_by=order_by)
    doc_list = []
    for doc in document_list:
        doc_list.extend([frappe.get_doc(doctype, doc['name']).as_dict()])
    return doc_list

def get_complete_list(doctype, filters=None, fields=None, from_record=0, to_record=None, order_by=None):
    return frappe.get_list(doctype, fields=["*"] if not fields else fields, filters=filters,
            limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 500, 
            order_by="name" if not order_by else order_by)
