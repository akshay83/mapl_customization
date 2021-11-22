import frappe
import json
import datetime
from frappe.utils import get_safe_filters, getdate, add_to_date, format_date

class FetchData(object):
    def __init__(self, connection, parent_module):
        self.DATETIME_FORMAT = "%d-%m-%Y"
        self.conn = connection
        self.parent_module = parent_module
        self.non_stock_transactions = False
        self.stock_transactions = False
        self.transactional = False

    def set_datetime_filters(self, from_date, to_date, additional_filters, max_records_per_batch):
        self.from_date = getdate(datetime.datetime.strptime(from_date, self.DATETIME_FORMAT))
        self.to_date = getdate(datetime.datetime.strptime(to_date, self.DATETIME_FORMAT))
        self.max_records_per_batch = max_records_per_batch if max_records_per_batch else 500
        self.additional_filters = additional_filters
        #Convert From Json to String
        self.filters = json.dumps(self.build_filters())

    def init_transactional_entries(self, doctype, from_date=None, to_date=None, \
                    additional_filters=None, max_records_per_batch=None):
        self.doctype = doctype
        self.set_datetime_filters(from_date, to_date, additional_filters, max_records_per_batch)
        self.transactional = True
        self.stock_transactions = False
        #--DEBUG--print (self.filters)
        self.process()

    def init_stock_transactions(self, from_date=None, to_date=None, \
                    additional_filters=None, max_records_per_batch=None):
        self.doctype = 'Stock Ledger Entry'
        self.set_datetime_filters(from_date, to_date, additional_filters, max_records_per_batch)
        self.stock_transactions = True
        self.non_stock_transactions = False
        self.transactional = False
        self.process()

    def init_non_stock_transactions(self, from_date=None, to_date=None, \
                    additional_filters=None, max_records_per_batch=None):
        self.doctype = 'Stock Ledger Entry'
        self.set_datetime_filters(from_date, to_date, additional_filters, max_records_per_batch)
        self.non_stock_transactions = True
        self.stock_transactions = False
        self.transactional = False
        self.process()

    def process(self):
        #-- DEBUG -- print (self.filters, isinstance(self.filters, str))
        if not self.non_stock_transactions:
            self.total_records = get_record_count(self.conn, self.parent_module, self.doctype, self.filters)
        else:
            self.total_records = get_record_count(self.conn, self.parent_module, \
                    self.doctype, filters={'from_date':self.from_date, 'to_date':self.to_date}, non_stock=True)
        self.current_record = 0
        self.current_date = self.from_date
        print ('Total Records', self.total_records)

    def get_next_batch(self):
        list = self._get_next_batch()
        self.current_record = self.current_record + len(list if list else [])
        #--DEBUG-- print ("Length List", len(list))
        return list

    def _get_next_batch(self):        
        list = None
        if self.transactional:
            list = get_entries(self.conn, self.parent_module, self.doctype, from_date=self.current_date, to_date=self.current_date)
        elif self.stock_transactions:
            list = get_transactions(self.conn, self.parent_module, from_date=self.current_date, to_date=self.current_date)
        elif self.non_stock_transactions:
            list = get_transactions(self.conn, self.parent_module, from_date=self.current_date, to_date=self.current_date, non_stock=True)
        #--DEBUG-- print ('Current Date:', self.current_date)
        self.current_date = getdate(add_to_date(self.current_date,days=1))
        if self.has_more_records() and (not list or len(list)<=0):            
            #Skip Current Date which has not Transactions    
            list = self._get_next_batch()
        return list

    def has_more_records(self):
        if getdate(self.current_date) > getdate(self.to_date):
            return False
        if self.current_record >= self.total_records:
            return False
        #if self.current_record >= self.max_records_per_batch:
        #    return False
        return True

    def build_filters(self):
        dt_filters = build_date_filter(self.doctype, self.from_date, self.to_date)
        if self.additional_filters:
            if dt_filters:
                self.additional_filters.extend(dt_filters)
            return self.additional_filters
        elif dt_filters:
            return dt_filters
        return None

def build_date_filter(doctype, from_date=None, to_date=None):        
    date_filters = []
    if from_date:
        date_filters.append([doctype, "posting_date", ">=", format_date(from_date, format_string="yyyy-mm-dd")])
    if to_date:
        date_filters.append([doctype, "posting_date", "<=", format_date(to_date, format_string="yyyy-mm-dd")])
    if len(date_filters)<=0:
        date_filters = None
    return date_filters

def get_record_count(conn, parent_module, doctype, filters=None, non_stock=False):
    if not non_stock:
        return conn.get_api(parent_module+'.rest_api.get_count', params={'doctype':doctype, 'filters':filters, 'distinct':1})
    else:
        return conn.get_api(parent_module+".rest_api.get_non_stock_transaction_count",
                                        params={'from_date':filters.get('from_date'),'to_date':filters.get('to_date')})[0][0]        

def get_entries(conn, parent_module, doctype, from_date=None, to_date=None, page_length=None):
    if not page_length and not to_date:
        page_length = 50
    else:
        page_length = 1000000 #Try and Get All Transactions Till The To Date Specified

    date_filters = build_date_filter(doctype, from_date, to_date)
    if date_filters:
        date_filters = json.dumps(date_filters)

    return get_doc_list(conn, parent_module, doctype, filters=date_filters, 
                    to_record=page_length if page_length else 50,order_by="posting_date")

def get_transactions(conn, parent_module, from_date=None, to_date=None, non_stock=False):
    if not from_date:
        from_date = '2017-04-01' # '01-04-2017'
    if not to_date:
        to_date = '2017-06-30' # '30-06-2017'
    return conn.get_api(parent_module+'.rest_api.get_doc_list_as_per_transactions',
                            params={'from_date':from_date,
                                'to_date':to_date,
                                'non_stock':non_stock})
                
def get_item_list(conn, from_record=0, to_record=None):
    return conn.get_list('Item', fields=["*"], 
                limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 50, order_by="name")

def get_address_list(conn, doctype, docname, from_record=0, to_record=None):
    filters = [
            ["Dynamic Link", "link_doctype", "=", doctype],
            ["Dynamic Link", "link_name", "=", docname],
            ["Dynamic Link", "parenttype", "=", "Address"],
        ]
    return conn.get_list("Address", fields=["*"], filters=filters,
                limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 500, order_by="name")                

def get_doc_list(conn, parent_module, doctype, fields=None,filters=None,from_record=0,to_record=500,order_by=None):
    return conn.get_api(parent_module+'.rest_api.get_doc_list',
                            params={'doctype':doctype,
                                'filters':filters,
                                'fields':fields,
                                'from_record':from_record,
                                'to_record':to_record,
                                'order_by':order_by})