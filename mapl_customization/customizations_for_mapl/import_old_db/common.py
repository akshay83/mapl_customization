import frappe
import datetime
import difflib
from frappe.utils import cint, cstr, getdate, get_time
from erpnext import get_default_company

def find_closest_match(self, str, in_list):
    uncase_list = [x.lower() for x in in_list]
    match = difflib.get_close_matches(str.lower(), uncase_list, n=1)
    try:
        idx = uncase_list.index(match)
        print (match)
    except ValueError:
        print ('Unable to Find:',str)

def save_point(name):
    frappe.db.sql("SAVEPOINT {0}".format(name))

def rollback_to_savepoint(name):
    frappe.db.sql("ROLLBACK TO SAVEPOINT {0}".format(name))

def release_savepoint(name):
    frappe.db.sql("RELEASE SAVEPOINT {0}".format(name))

def log_info(logging, error, document=None):
    from erpnext.stock.doctype.serial_no.serial_no import SerialNoNotExistsError, SerialNoWarehouseError
    from erpnext.stock.stock_ledger import NegativeStockError, SerialNoExistsInFutureTransaction

    if isinstance(error, str):
        logging.info(error)
    else:
        logging.info(str(error))  
    if not document:
        return          
    if isinstance(error, SerialNoNotExistsError):
        logging.info('Serial No Exists Error. Queueing for Later Insertion, Doctype {0} with Name {1}'.format(document.doctype, document.name))
    elif isinstance(error, SerialNoWarehouseError):
        logging.info('Serial No Warehouse Error. Queueing for Later Insertion, Doctype {0} with Name {1}'.format(document.doctype, document.name))
    elif isinstance(error,NegativeStockError):
        logging.info('Negative Stock Error. Reposting & Retrying Doctype {0} with Name {1}'.format(document.doctype, document.name))

def validate_sle_entries(doc):
    if not doc:
        return True

    expected_balance_qty = None
    if doc.get('doctype') == 'Stock Entry':
        sl_entries = []
        doc.get_sle_for_source_warehouse(sl_entries, [])
        doc.get_sle_for_target_warehouse(sl_entries, [])
        expected_balance_qty = 0
        for s in sl_entries:
            expected_balance_qty = expected_balance_qty + cint(s.get('actual_qty'))
    elif doc.get('doctype') == "Sales Invoice":
        expected_balance_qty = 0
        for i in doc.get('items'):
            if frappe.db.get_value('Item',i.get('item_code'), 'is_stock_item'):
                expected_balance_qty = expected_balance_qty + (cint(i.get('qty')) * -1)
    elif doc.get('doctype') == "Purchase Invoice":
        expected_balance_qty = 0
        for i in doc.get('items'):
            if frappe.db.get_value('Item',i.get('item_code'), 'is_stock_item'):
                expected_balance_qty = expected_balance_qty + cint(i.get('qty'))
        
    balance_qty = get_sle_qty(doc.get('name'), doc.get('doctype'))
    #--DEBUG-- print (balance_qty, expected_balance_qty)
    if expected_balance_qty != None and balance_qty != expected_balance_qty:
        #--DEBUG-- print ("Invalid Stock Entries")
        return False

    return True

def get_sle_qty(doc_name, doctype):
    sl_list = frappe.get_list('Stock Ledger Entry', fields=["sum(actual_qty)"], as_list=1, \
                filters=[["voucher_no", "=", doc_name],["voucher_type","=",doctype]])
    return cint(sl_list[0][0])

def repost_entries(item_code, warehouse, posting_date=None, posting_time=None):    
    from erpnext.stock.stock_ledger import repost_future_sle
    from erpnext.accounts.utils import update_gl_entries_after

    posting_date = getdate(posting_date) if posting_date else getdate(datetime.datetime.strptime("01-04-2017", "%d-%m-%Y"))
    posting_time = get_time(posting_time) if posting_time else "00:00"

    repost_future_sle(args=[frappe._dict({
        "item_code": item_code,
        "warehouse": warehouse,
        "posting_date": posting_date,
        "posting_time": posting_time
    })])

    update_gl_entries_after(posting_date, posting_time, [warehouse], [item_code], company=get_default_company())    

def split_name(customer_name):
    names = customer_name.strip().split(' ')
    fn = (' '.join(names[0:len(names)-2]) if len(names) >= 3 else names[0])
    ln = names[-1]
    mn = (names[-2] if len(names) >= 3 else None)
    return fn, mn, ln        

def trim_values(doc):
    type_map = frappe.db.type_map

    for fieldname, value in doc.get_valid_dict().items():
        df = doc.meta.get_field(fieldname)
        
        if not df or df.fieldtype == 'Check':
            # skip standard fields and Check fields
            continue

        column_type = type_map[df.fieldtype][0] or None

        if not column_type:
            continue

        if column_type == 'varchar':
            default_column_max_length = type_map[df.fieldtype][1] or None
            max_length = cint(df.get("length")) or cint(default_column_max_length)

            if len(cstr(value)) > max_length:
                #--DEBUG-- print ("Truncating {0} to {1} Characters having current Length {2}".format(fieldname,max_length, len(cstr(value))))
                setattr(doc, fieldname, value[:max_length])

# Print iterations progress
def printProgressBar (doctype, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r", supplement_msg=""):
    """
    Call in a loop to create terminal progress bar
    @params:
        iteration   - Required  : current iteration (Int)
        total       - Required  : total iterations (Int)
        prefix      - Optional  : prefix string (Str)
        suffix      - Optional  : suffix string (Str)
        decimals    - Optional  : positive number of decimals in percent complete (Int)
        length      - Optional  : character length of bar (Int)
        fill        - Optional  : bar fill character (Str)
        printEnd    - Optional  : end character (e.g. "\r", "\r\n") (Str)
    """
    if iteration <= 0:
        print ("Importing:", doctype, "Total Records:", total, 'Started At:',datetime.datetime.utcnow())
    percent = ("{0:." + str(decimals) + "f}").format(100 * (iteration / float(total)))
    filledLength = int(length * iteration // total)
    bar = fill * filledLength + '-' * (length - filledLength)
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd+" "+str(supplement_msg))
    # Print New Line on Complete
    if iteration == total: 
        print()
        print ("Imported:", doctype, "Total Records:", total, 'Completed At:',datetime.datetime.utcnow())
