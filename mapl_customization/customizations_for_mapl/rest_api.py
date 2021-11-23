import frappe
import json
from frappe.utils import cint, getdate

@frappe.whitelist()
def get_entities_with_addresses(doctype, filters=None, from_record=0, page_length=500):
    from_record=cint(from_record)
    page_length=cint(page_length)

    entities = get_complete_list(doctype, filters=filters, from_record=from_record, page_length=page_length, order_by="name")
    for e in entities:
        if isinstance(e, dict):
            address_filters = [
                ["Dynamic Link", "link_doctype", "=", doctype],
                ["Dynamic Link", "link_name", "=", e['name']],
                ["Dynamic Link", "parenttype", "=", "Address"],
            ]                        
            e['addresses'] = get_complete_list('Address', filters=address_filters, page_length=500)
    return entities

@frappe.whitelist()
def get_doc_list_as_per_transactions(filters=None, from_date=None, to_date=None, order_by=None, non_stock=False):

    if isinstance(non_stock, basestring):
        non_stock = non_stock == "True"

    default_fields = ["voucher_type, voucher_no, posting_date, posting_time"]
    default_order_by = "posting_date,posting_time"
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
        document_list = get_complete_list('Stock Ledger Entry', filters=filters, 
                        fields=default_fields,
                        to_record = 100000, #Get Maximum Records 
                        order_by=default_order_by if not order_by else order_by,
                        distinct=1)
    else:
        from mapl_customization.customizations_for_mapl.utils import get_non_stock_sales_purchase
        document_list = get_non_stock_sales_purchase(from_date=from_date, to_date=to_date)
    doc_list = []
    for doc in document_list:
        doc_doc = frappe.get_doc(doc['voucher_type'], doc['voucher_no'])
        if not doc_doc.get('posting_time'):
            doc_doc.posting_time = doc.get('posting_time')
        doc_list.extend([doc_doc.as_dict()])
    return doc_list

@frappe.whitelist()
def get_doc_list(doctype, filters=None, fields=None, from_record=0, page_length=50, order_by=None):
    """
    By default the frappe.get_list method does not return the child tables of the documents. This method 
    Returns a List of Documents having all its child tables included inside the "DICT", as a "LIST"

    :param doctype: The type of Document to Fetch
    :param filters: A List of filters (Optional)
    :param fields: Not yet implemented
    :param from_record: return results starting from record number
    :param page_length: No of Records to Return from pointer "from_record". Default is 50
    :param order_by: order the results by <fieldname>
    """
    if from_record:
        from_record = cint(from_record)
    if page_length:
        page_length = cint(page_length)
    document_list = get_complete_list(doctype, filters=filters, fields="name", from_record=from_record, page_length=page_length, order_by=order_by)
    doc_list = []
    for doc in document_list:
        doc_list.extend([frappe.get_doc(doctype, doc['name']).as_dict()])
    return doc_list

def get_complete_list(doctype, filters=None, fields=None, from_record=0, page_length=50, order_by=None, distinct=0):
    """
    Wrapper method for frappe.get_list method. Returns a list of records or documents without child tables
    """
    return frappe.get_list(doctype, fields=["*"] if not fields else fields, filters=filters,
            limit_start=from_record, limit_page_length=page_length, 
            order_by="name" if not order_by else order_by, distinct=distinct)

@frappe.whitelist()
def get_count(doctype, filters=None, debug=False, cache=False, distinct=0):
    #Backward Compatibilty for Ver 8
    if filters:
        filters = json.loads(filters)
    return frappe.get_all(doctype, filters=filters, fields='count(*)', debug=debug, as_list=True, distinct=distinct)[0][0]

@frappe.whitelist()
def get_non_stock_transaction_count(from_date, to_date):
    if not from_date and not to_date:
        return 0
    if from_date and not to_date:
        to_date = getdate()    
    from mapl_customization.customizations_for_mapl.utils import get_non_stock_sales_purchase_count
    return get_non_stock_sales_purchase_count(from_date=from_date, to_date=to_date)