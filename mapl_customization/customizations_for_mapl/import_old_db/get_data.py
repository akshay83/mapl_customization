import frappe
import json
import datetime
from frappe.utils import get_safe_filters, getdate, add_to_date, format_date

class FetchData(object):
    def __init__(self, connection, client_db_api_path, records_per_batch=500, day_interval=1):
        self.DATETIME_FORMAT = "%d-%m-%Y"
        self.conn = connection
        self.client_db_api_path = client_db_api_path
        self.non_stock_transactions = False
        self.stock_transactions = False
        self.transactional = False
        self.base_document = False
        self.max_records_per_batch = records_per_batch
        self.day_interval = day_interval

    def set_datetime_filters(self, from_date, to_date, additional_filters):
        self.from_date = getdate(datetime.datetime.strptime(from_date, self.DATETIME_FORMAT))
        self.to_date = getdate(datetime.datetime.strptime(to_date, self.DATETIME_FORMAT))
        #deducting 1 day as data would be fetched from 1st to 6th Otherwise with 1st included 
        self.fetch_till_date = getdate(add_to_date(self.from_date,days=self.day_interval-1))
        if (self.fetch_till_date > self.to_date):
            self.fetch_till_date = self.to_date            
        self.additional_filters = additional_filters
        #Convert From Json to String
        self.filters = json.dumps(self.build_filters())

    def init_transactional_entries(self, doctype, from_date=None, to_date=None, additional_filters=None):
        self.doctype = doctype
        self.set_datetime_filters(from_date, to_date, additional_filters)
        self.transactional = True
        self.stock_transactions = False
        self.base_document = False
        #--DEBUG--print (self.filters)
        self.process()

    def init_stock_transactions(self, from_date=None, to_date=None, additional_filters=None):
        self.doctype = 'Stock Ledger Entry'
        self.set_datetime_filters(from_date, to_date, additional_filters)
        self.stock_transactions = True
        self.non_stock_transactions = False
        self.transactional = False
        self.base_document = False
        self.process()

    def init_non_stock_transactions(self, from_date=None, to_date=None, additional_filters=None):
        self.doctype = 'Stock Ledger Entry'
        self.set_datetime_filters(from_date, to_date, additional_filters)
        self.non_stock_transactions = True
        self.stock_transactions = False
        self.transactional = False
        self.base_document = False
        self.process()

    def init_base_documents_list(self, doctype, filters=None, order_by=None, fetch_with_children=True, in_batches=True):
        self.doctype = doctype
        self.non_stock_transactions = False
        self.stock_transactions = False
        self.transactional = False
        self.base_document = True
        self.filters = filters
        self.order_by = order_by
        self.fetch_with_children = fetch_with_children
        self.process()

    def process(self):
        #-- DEBUG -- print (self.filters, isinstance(self.filters, str))
        if (not self.non_stock_transactions or self.base_document):
            self.total_records = get_record_count(self.conn, self.client_db_api_path, self.doctype, self.filters)
        else:
            self.total_records = get_record_count(self.conn, self.client_db_api_path, \
                    self.doctype, filters={'from_date':self.from_date, 'to_date':self.to_date}, non_stock=True)
        self.current_record = 0
        self.current_date = getattr(self, 'from_date',None)
        print ('Total Records', self.total_records)

    def has_data(self):
        if not hasattr(self, 'list'):
            return False
        return (self.list != None and len(self.list)>0)

    def get_next_batch(self):
        self.list = self._get_next_batch()
        self.current_record = self.current_record + len(self.list or [])
        #--DEBUG-- print ("Length List", len(self.list))
        return self.list

    def _get_next_batch(self):   
        #--DEBUG -- print (self.day_interval, self.from_date, self.current_date, self.fetch_till_date, self.to_date)     
        list = None
        if self.transactional:
            list = get_entries(self.conn, self.client_db_api_path, self.doctype, from_date=self.current_date, to_date=self.fetch_till_date)
        elif self.non_stock_transactions or self.stock_transactions:
            list = get_stock_transactions(self.conn, self.client_db_api_path, from_date=self.current_date, to_date=self.fetch_till_date, non_stock=self.non_stock_transactions)
        elif self.base_document:
            list = self.get_base_document_list()

        #--DEBUG-- print ('Current Date:', self.current_date)
        if not self.base_document:
            self.current_date = getdate(add_to_date(self.fetch_till_date,days=1))
            self.fetch_till_date = getdate(add_to_date(self.current_date,days=self.day_interval-1)) #Componsate for 1 Day Added to current_date in previous line
            if (self.fetch_till_date > self.to_date):
                self.fetch_till_date = self.to_date        

        if self.has_more_records() and (not list or len(list)<=0):            
            #Skip Current Date which has not Transactions    
            list = self._get_next_batch()
        return list
        
    def get_base_document_list(self):
            if self.fetch_with_children:
                return get_documents_with_childtables(self.conn, self.client_db_api_path, self.doctype, filters=self.filters, from_record=self.current_record, \
                                page_length=self.max_records_per_batch, order_by=self.order_by)
            else:
                return get_documents_without_childtables(self.conn, self.doctype, client_db_api_path=self.client_db_api_path, filters=self.fitlers, \
                                from_record=self.current_record,page_length=self.max_records_per_batch, order_by=self.order_by)

    def has_more_records(self):
        if hasattr(self, 'fetch_till_date') and hasattr(self, 'to_date'):
            if getdate(self.current_date) > getdate(self.to_date):
                return False
        if hasattr(self, 'current_record') and hasattr(self, 'total_records'):                
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

def get_record_count(conn, client_db_api_path, doctype, filters=None, non_stock=False):
    if not non_stock:
        return conn.get_api(client_db_api_path+'.rest_api.get_count', params={'doctype':doctype, 'filters':filters, 'distinct':1})
    else:
        return conn.get_api(client_db_api_path+".rest_api.get_non_stock_transaction_count",
                                        params={'from_date':filters.get('from_date'),'to_date':filters.get('to_date')})[0][0]        

def get_entries(conn, client_db_api_path, doctype, from_date=None, to_date=None, page_length=None):
    if not page_length and not to_date:
        page_length = 50
    else:
        page_length = 1000000 #Try and Get All Transactions Till The To Date Specified

    date_filters = build_date_filter(doctype, from_date, to_date)
    if date_filters:
        date_filters = json.dumps(date_filters)

    return get_documents_with_childtables(conn, client_db_api_path, doctype, filters=date_filters, 
                    page_length=page_length,order_by="posting_date")

def get_stock_transactions(conn, client_db_api_path, from_date=None, to_date=None, non_stock=False):
    if not from_date:
        from_date = '2017-04-01' # '01-04-2017'
    if not to_date:
        to_date = '2017-06-30' # '30-06-2017'
    return conn.get_api(client_db_api_path+'.rest_api.get_doc_list_as_per_transactions',
                            params={'from_date':from_date,
                                'to_date':to_date,
                                'non_stock':non_stock})

def get_documents_with_childtables(conn, client_db_api_path, doctype, fields=None,filters=None,from_record=0,page_length=50,order_by=None):
    return conn.get_api(client_db_api_path+'.rest_api.get_doc_list',
                            params={'doctype':doctype,
                                'filters':filters,
                                'fields':fields,
                                'from_record':from_record,
                                'page_length':page_length,
                                'order_by':order_by})

def get_documents_without_childtables(conn, doctype, client_db_api_path=None, fields=None,filters=None,from_record=0,page_length=50,order_by=None):
    return conn.get_list(doctype, fields=(fields or ["*"]), filters=filters,
                limit_start=from_record, limit_page_length=page_length, order_by=(order_by or "name"))
