import frappe
import datetime
import logging
from .frappeclient import FrappeClient
from .get_data import FetchData, get_documents_without_childtables, get_documents_with_childtables, get_record_count
from frappe.utils import cstr, validate_email_address, validate_phone_number, flt, getdate, format_date
from erpnext import get_default_company

class SkipRecordException(Exception):
    pass 

class ImportDB(object):
    def __init__(self, url, username, password, parent_module=None):
        self.remoteDBClient = FrappeClient(url, username=username, password=password)
        self.parent_module = parent_module
        logging.basicConfig(filename="/home/frappe/import_log.log",level=logging.INFO)
        logging.info('Initialized Importing Instance at {0}'.format(datetime.datetime.utcnow()))
        self.COMMIT_DELAY = 500
        if not self.parent_module:
            self.parent_module = "mapl_customization.customizations_for_mapl"

    def __exit__(self, *args, **kwargs):
        self.logout()

    def logout(self):
        self.remoteDBClient.logout()

    def get_connection(self):
        return self.remoteDBClient

    def set_parent_module(name):
        self.parent_module = name

    def import_masters(self):
        self.import_accounts(overwrite=True)
        self.import_mode_of_payment()
        self.import_salutation()
        self.import_customer_group()
        self.import_price_list()
        self.import_user_groups()
        self.import_employee_branches()
        self.import_employee_designation()        
        self.import_brands()
        self.import_warehouses()
        self.import_itemgroups()
        self.import_uom()
        self.import_cost_center()
        self.import_fiscal_years()
        self.import_asset_category()
        self.import_tax_and_charges_template()
        self.import_item_tax_templates()
        self.import_terms_conditions()
        self.import_hypthecation()
        self.import_finance_charges()        
        self.import_special_payment()
        self.import_special_invoice()
        self.import_loan_types()
        self.import_salary_components()
        self.import_holiday_lists()

    def import_entities(self, page_length=None):
        self.import_employees()
        self.import_customers() #30000
        self.import_suppliers()

    def import_salary_details(self):
        self.import_salary_structures()
        self.import_employee_loans()
        self.import_employee_salary_slips()
    
    def process(self, till_date=False, import_modules=None):
        print ("Staring Process at",datetime.datetime.utcnow())
        logging.info('Started Process at {0}'.format(datetime.datetime.utcnow()))
        if not frappe.db.get_single_value('Global Defaults', 'default_company'):
            frappe.throw("Please set Global Defaults")
        if not import_modules or "masters" in import_modules:
            self.import_masters()
        if not import_modules or "entities" in import_modules:            
            self.import_entities()
        if not import_modules or "items" in import_modules:            
            self.import_items()
        if not import_modules or "salary_details" in import_modules:                        
            self.import_salary_details()
        dates_map = [
            #["01-04-2017", "30-06-2017"],
            ["01-07-2017", "20-07-2017"],
            #["01-07-2017", "30-09-2017"],
            #["01-10-2017", "31-03-2018"]
            #["01-04-2018", "30-09-2018"],
            #["01-10-2018", "31-03-2019"],
            #["01-04-2019", "30-09-2019"],
            #["01-10-2019", "31-03-2020"],
            #["01-04-2020", "30-09-2020"],
            #["01-10-2020", "31-03-2021"],
        ]
        dt = format_date(getdate())        
        if not import_modules or "stock_transactions" in import_modules:
            for d in dates_map:
                self.import_stock_transactions(from_date=d[0],to_date=d[1])
            if till_date:
                self.import_stock_transactions(from_date="01-04-2021",to_date=dt)
        if not import_modules or "non_stock_transactions" in import_modules:
            for d in dates_map:
                self.import_stock_transactions(from_date=d[0],to_date=d[1], non_sle_entries=True)
            if till_date:
                self.import_stock_transactions(from_date="01-04-2021",to_date=dt, non_sle_entries=True)
        if not import_modules or "payments" in import_modules:
            for d in dates_map:
                self.import_payment_entries(from_date=d[0],to_date=d[1])
            if till_date:
                self.import_payment_entries(from_date="01-04-2021",to_date=dt)
        if not import_modules or "journal" in import_modules:                
            for d in dates_map:
                self.import_journal_entries(from_date=d[0],to_date=d[1])        
            if till_date:
                self.import_journal_entries(from_date="01-04-2021",to_date=dt)
        if not import_modules or "period_closing" in import_modules:                
            self.import_period_closing_vouchers()
        print ("Completed Process at",datetime.datetime.utcnow())
        logging.info('Completed Process at {0}'.format(datetime.datetime.utcnow()))

    def import_accounts(self, overwrite=False):
        def before_inserting(new_doc, old_doc):
            new_doc.lft = None
            new_doc.rgt = None
            if not new_doc.get('parent_account'):
                new_doc.flags.ignore_mandatory = True
            if not new_doc.is_new() and not new_doc.get('parent_account'):
                raise SkipRecordException("Skiped Record {0}".format(new_doc.name))

        self.import_documents_having_childtables('Account', order_by="lft", before_insert=before_inserting, overwrite=overwrite)                

    def import_customer_group(self):
        self.import_documents_having_childtables('Customer Group')

    def import_price_list(self):
        self.import_documents_having_childtables('Price List')        

    def import_customers(self, overwrite=False, id=None):
        def before_insert(new_doc, old_doc):
            new_doc.pan = old_doc.get('pan_no')

        def after_insert(new_doc, old_customer_dict, import_addresses=True, auto_create_customer_contacts=True):
            if import_addresses:
                self.import_address('Customer', old_customer_dict)
            if auto_create_customer_contacts:
                self.create_contact(old_customer_dict, old_customer_dict.name)

        self.import_documents_having_childtables('Customer', after_insert=after_insert, before_insert=before_insert, \
            overwrite=overwrite, id=id, copy_child_table=False)

    def import_suppliers(self, overwrite=False, id=None):
        def before_insert(new_doc, old_supplier_dict):
            #Field Name Change in New Version
            setattr(new_doc, 'supplier_group', old_supplier_dict.get('supplier_type'))
            if not frappe.db.exists('Supplier Group', new_doc.supplier_group):
                new_doc.supplier_group = 'All Supplier Groups'
            delattr(new_doc, 'supplier_type')

        def after_insert(new_doc, old_supplier_dict, import_addresses=True):
            if import_addresses:
                self.import_address('Supplier', old_supplier_dict)        

        self.import_documents_having_childtables('Supplier', before_insert=before_insert, after_insert=after_insert, \
            overwrite=overwrite, id=id, copy_child_table=False)

    def import_user_groups(self):
        self.import_documents_having_childtables('User Group')

    def import_employee_branches(self):
        self.import_documents_having_childtables('Branch')

    def import_employee_designation(self):
        self.import_documents_having_childtables('Designation')

    def import_employees(self):
        def before_inserting(doc, old_doc):
            fn, mn, ln = self.split_name(old_doc.employee_name)
            doc.first_name = fn
            doc.middle_name = mn
            doc.last_name = ln

        self.import_documents_having_childtables(doctype='Employee', before_insert=before_inserting)

    def import_brands(self):
        self.import_documents_having_childtables('Brand')

    def import_warehouses(self):
        self.import_documents_having_childtables('Warehouse', order_by="lft")

    def import_itemgroups(self):
        self.import_documents_having_childtables('Item Group', order_by="lft")
    
    def import_uom(self):
        self.import_documents_having_childtables('UOM')

    def import_cost_center(self):
        self.import_documents_having_childtables('Cost Center', order_by="lft")

    def import_fiscal_years(self):
        self.import_documents_having_childtables('Fiscal Year')

    def import_terms_conditions(self):
        self.import_documents_having_childtables('Terms and Conditions')
    
    def import_hypthecation(self):
        self.import_documents_having_childtables("Hypothecation Company")

    def import_finance_charges(self):
        self.import_documents_having_childtables("Finance Charges")

    def import_special_payment(self):
        self.import_documents_having_childtables("Special Payment")

    def import_special_invoice(self):
        self.import_documents_having_childtables("Special Invoicing")

    def import_salary_components(self):
        def remove_depends_on_payment_days(doc, old_doc):
            if doc.type=='Deduction':
                doc.depends_on_payment_days = 0

        self.import_documents_having_childtables('Salary Component', overwrite=True, before_insert=remove_depends_on_payment_days)

    def import_asset_category(self):
        self.import_documents_having_childtables('Asset Category')

    def import_mode_of_payment(self):
        self.import_documents_having_childtables('Mode of Payment')

    def import_salutation(self):
        self.import_documents_having_childtables('Salutation')

    def import_tax_and_charges_template(self):
        for docs in ['Purchase Taxes and Charges Template','Sales Taxes and Charges Template']:
            self.import_documents_having_childtables(docs)

    def import_item_tax_templates(self):
        def before_inserting(new_doc, old_doc):
            new_doc.title = old_doc.name
            for i in new_doc.taxes:
                i.doctype = 'Item Tax Template Detail'                

        self.import_documents_having_childtables('Item Taxes Template', new_doctype='Item Tax Template',before_insert=before_inserting, overwrite=True)

    def import_items(self, id=None):
        def before_insert(new_doc, old_item_dict):
            if old_item_dict.get('expense_account') or old_item_dict.get('income_account'):
                item_defaults = new_doc.append('item_defaults')
                item_defaults.company = get_default_company()
                item_defaults.expense_account = old_item_dict.get('expense_account')
                item_defaults.income_account = old_item_dict.get('income_account')
            if old_item_dict.get('taxes_template'):
                taxes = new_doc.append('taxes')
                taxes.item_tax_template = old_item_dict.taxes_template

        self.import_documents_having_childtables('Item', before_insert=before_insert, id=id, copy_child_table=False)

    def import_holiday_lists(self):
        self.import_documents_having_childtables('Holiday List')

    def import_loan_types(self):
        def before_inserting(new_doc, old_doc):
            #New Fields in New Version
            new_doc.is_term_loan = 1
            new_doc.mode_of_payment = "Cash"
            new_doc.company = get_default_company()
            new_doc.payment_account = frappe.db.get_value("Account", filters=dict(name=("like", "Cash -%")))            
            new_doc.loan_account = frappe.db.get_value("Account", filters=dict(name=("like", "Salary Advance %")))
            new_doc.interest_income_account = frappe.db.get_value("Account", filters=dict(name=("like", "Interest Received %")))
            new_doc.penalty_income_account = frappe.db.get_value("Account", filters=dict(name=("like", "Interest Received %")))

        self.import_documents_having_childtables('Loan Type', before_insert=before_inserting, submit=True)            

    def import_salary_structures(self):
        def new_name(old_doc):
            return old_doc.name.split('-')[0].strip()

        def before_salary_structure(new_doc, old_doc):
            self.copy_child_table_attr(old_doc, new_doc, 'earnings')
            self.copy_child_table_attr(old_doc, new_doc, 'deductions')
            new_doc.flags.ignore_validate = True

        def after_salary_structute(new_doc, old_doc):
            for employees in old_doc.get('employees'):                
                if frappe.db.exists("Salary Structure Assignment", old_doc.name):
                    continue
                assign_structure = frappe.new_doc("Salary Structure Assignment")
                self.copy_attr(employees, assign_structure, copy_child_table=False)
                assign_structure.doctype = "Salary Structure Assignment"
                assign_structure.salary_structure = old_doc['name'] if assign_structure.employee_name.lower() in old_doc['name'].lower() \
                                                    else (old_doc['name']+' '+assign_structure.employee_name)
                assign_structure.flags.ignore_validate = True
                self.insert_doc(assign_structure, new_name=old_doc.name, submit=True)

        self.import_documents_having_childtables('Salary Structure', before_insert=before_salary_structure, after_insert=after_salary_structute, \
                                    copy_child_table=False, fetch_with_children=True, submit=True)

    def import_employee_loans(self):
        def before_inserting(doc, old_doc):
            doc.applicant_type = 'Employee'
            doc.applicant = doc.employee
            doc.applicant_name = doc.employee_name
            doc.loan_account = doc.employee_loan_account
            doc.penalty_income_account = doc.interest_income_account
            if doc.status == 'Fully Disbursed':
                doc.status = 'Disbursed'
            doc.flags.ignore_validate = True

        self.import_documents_having_childtables('Employee Loan', new_doctype='Loan', before_insert=before_inserting)

    def import_employee_salary_slips(self):
        def before_inserting(new_doc, old_doc):                
            if old_doc.get('loan_deduction_detail'):
                for idx, l in enumerate(new_doc.loans):
                    l.loan = old_doc.loan_deduction_detail[idx].get('loan_reference')
                    l.doctype = 'Salary Slip Loan'
            new_doc.flags.ignore_validate = True
            new_doc.flags.ignore_links = True

        self.import_documents_having_childtables('Salary Slip', child_table_name_map={'loan_deduction_detail':'loans'}, before_insert=before_inserting)

    def import_stock_transactions(self,from_date=None, to_date=None, non_sle_entries=False):
        print ('Importing Stock Transactions')
        batchdata = FetchData(self.remoteDBClient, self.parent_module, day_interval=5)
        if not non_sle_entries:
            batchdata.init_stock_transactions(from_date=from_date, to_date=to_date)
        else:
            batchdata.init_non_stock_transactions(from_date=from_date, to_date=to_date)    
        while batchdata.has_more_records():
            entries = batchdata.get_next_batch()
            if not entries or len(entries)<=0:
                break
            #--DEBUG-- print ("Testing", len(entries))    
            self.import_transactions(entries)

    def import_transactions(self, entries):
        def before_inserting(new_doc, old_doc):
            new_doc.flags.ignore_validate = True
            new_doc.amended_from = None
            if old_doc.doctype == 'Stock Entry':
                new_doc.stock_entry_type = old_doc.purpose
                if new_doc.total_incoming_value == 0 and new_doc.total_outgoing_value == 0:
                    for i in new_doc.items:
                        i.allow_zero_valuation_rate = 1
            if old_doc.doctype == 'Purchase Invoice':
                pass
            if old_doc.doctype == 'Sales Invoice':
                new_doc.invoice_copy = 'Original for Recipient'
                new_doc.delayed_payment_remarks = old_doc.get('special_remarks')
                new_doc.notes = old_doc.get('reference_details')
                new_doc.advances = None
            #--DEBUG-- print (new_doc.doctype, new_doc.name, new_doc.posting_date, new_doc.posting_time)

        if not entries or len(entries)<=0:
            return
        negative_stock = frappe.db.get_value("Stock Settings", None, "allow_negative_stock")
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", 1)        
        total_list_length = len(entries)
        #Initialize Progress Bar
        printProgressBar('Transactions', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, s in enumerate(entries):
            #Update Progress Bar                                    
            printProgressBar('Transactions', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
            s = frappe._dict(s)            
            self.import_documents_having_childtables(s.doctype, old_doc_dict=s, before_insert=before_inserting, suppress_msg=True, \
                                        in_batches=False, reset_batch=False)            
            if idx % self.COMMIT_DELAY == 0:
                frappe.db.commit()
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", negative_stock)
        frappe.db.commit()
        
    def import_payment_entries(self, from_date=None, to_date=None):
        def before_inserting(new_doc, old_doc):
            #if e['docstatus'] == 2:
            #    raise SkipRecordException('Skip Cancelled Record')
            new_doc.flags.ignore_validate = True
            #Dont Copy Sales Invoice Reference
            new_doc.references = None
            new_doc.base_total_allocated_amount = None
            new_doc.total_allocated_amount = None
            new_doc.allocate_payment_amount = None
            new_doc.amended_from = None
            new_doc.unallocated_amount = new_doc.paid_amount

        self.do_batch_import('Payment Entry', from_date=from_date, to_date=to_date, before_insert=before_inserting)

    def import_journal_entries(self, from_date=None, to_date=None, id=None):
        def before_inserting(new_doc, old_doc):
            if old_doc['docstatus'] == 2:
                raise SkipRecordException('Skip Cancelled Record')
            new_doc.flags.ignore_validate = True
            for row in new_doc.accounts:
                row.reference_name = None
                row.reference_type = None
            new_doc.amended_from = None

        monkey_patch_journal_entry_temporarily()        
        self.do_batch_import('Journal Entry', from_date=from_date, to_date=to_date, before_insert=before_inserting)

    def import_single_jv(self, id):
        doc = self.remoteDBClient.get_doc('Journal Entry',id)
        if doc and not frappe.db.exists('Journal Entry', doc['name']):
            self.import_journal_entry(frappe._dict(doc))
            frappe.db.commit()     

    def import_period_closing_vouchers(self):
        self.import_documents_having_childtables('Period Closing Voucher', order_by='transaction_date')

    def import_address(self, doctype, old_doc_dict):
        def before_insert(new_doc, old_doc):
            if new_doc.get('email_id') and not validate_email_address(new_doc.email_id):
                    delattr(new_doc, 'email_id')

            if new_doc.get('state') and new_doc.state.lower() == 'chattisgarh':
                    new_doc.state = 'Chhattisgarh'
            if new_doc.get('gst_state') and new_doc.gst_state.lower() == 'chattisgarh':
                    new_doc.gst_state = 'Chhattisgarh'

            if new_doc.get('gst_state') and new_doc.gst_state.lower() == 'dadra and nagar haveli':
                    new_doc.gst_state = 'Dadra and Nagar Haveli and Daman and Diu'                    
            if new_doc.get('state') and new_doc.state.lower() == 'dadra and nagar haveli':
                    new_doc.state = 'Dadra and Nagar Haveli and Daman and Diu'                    

            new_doc.flags.ignore_validate = True
            if new_doc.is_new():
                new_doc.append('links', dict(link_doctype=doctype, link_name=old_doc_dict.name))

        self.import_documents_having_childtables('Address', before_insert=before_insert, doc_list=old_doc_dict.addresses, \
                        overwrite=True, suppress_msg=True, fetch_with_children=False, in_batches=False, reset_batch=False)
    
    def create_contact(self, old_doc, new_doc_name):
        contact_nos = self.get_contact_nos(old_doc)
        if not contact_nos:
            return

        contact_nos = contact_nos.split(',')
        fn, mn, ln = self.split_name(old_doc.customer_name)        

        new_doc = None
        generated_name = self.generate_contact_name(fn, ln, new_doc_name)        
        save_doc = False
        if frappe.db.exists('Contact', generated_name):
            new_doc = frappe.get_doc('Contact', generated_name)
        else:
            new_doc = frappe.new_doc('Contact')
            new_doc.first_name, new_doc.middle_name, new_doc.last_name = fn, mn, ln
            new_doc.append('links', dict(link_doctype='Customer', link_name=new_doc_name))            
        for c in contact_nos:
            if validate_phone_number(c):
                new_doc.add_phone(c, is_primary_mobile_no=0)
                save_doc = True
        if old_doc.get('primary_email'):
            if validate_email_address(old_doc.email_id):
                new_doc.add_email(email_id=old_doc.primary_email, is_primary=1)
                save_doc = True
        if save_doc:
            self.save_doc(new_doc)

    def split_name(self, customer_name):
        names = customer_name.strip().split(' ')
        fn = (' '.join(names[0:len(names)-2]) if len(names) >= 3 else names[0])
        ln = names[-1]
        mn = (names[-2] if len(names) >= 3 else None)
        return fn, mn, ln        

    def get_contact_nos(self, old_doc):
        if not old_doc.get('primary_contact_no'):
            return None
        contact_nos = old_doc.primary_contact_no
        if old_doc.get('secondary_contact_no'):
            contact_nos = contact_nos + ',' + old_doc.get('secondary_contact_no')
        return contact_nos

    def generate_contact_name(self, first_name, last_name, old_customer_name):
        # copied from autoname in Contact Doctype
        contact_name = " ".join(filter(None,
            [cstr(f).strip() for f in [first_name, last_name]]))
        contact_name = contact_name + '-' + old_customer_name.strip()
        return contact_name

    def do_batch_import(self, doctype, from_date=None, to_date=None, before_insert=None, after_insert=None):
        batchdata = FetchData(self.remoteDBClient, self.parent_module, day_interval=5)
        batchdata.init_transactional_entries(doctype, from_date=from_date, to_date=to_date)
        while batchdata.has_more_records():
            entries = batchdata.get_next_batch()
            if not entries or len(entries)<=0:
                break
            #--DEBUG--print ("Testing", len(entries))        
        self.import_documents_having_childtables(self, doctype, before_insert=before_inserting, doc_list=entries) 
        frappe.db.commit()

    def remove_child_rows(self,new_doc, child_table):
        if (new_doc.get(child_table) and not new_doc.is_new()): #Child Not Empty  and new_doc.docstatus == 0
            child_doctype = new_doc.get(child_table)[0].doctype
            remove_rows = []
            for row in new_doc.get(child_table):
                remove_rows.append(row)
            for row in remove_rows:            
                new_doc.remove(row)
            flag = new_doc.flags.ignore_mandatory
            new_doc.flags.ignore_mandatory = True
            new_doc.save()
            new_doc.flags.ignore_mandatory = flag
    
    def copy_attr(self, old_doc, new_doc, copy_child_table=False, doctype_different=False, child_table_name_map=None):
        for k in old_doc.keys():            
            if isinstance(old_doc[k], dict) or isinstance(old_doc[k], list):
                if copy_child_table:
                    child_table_field_name = k 
                    if child_table_name_map:
                        child_table_field_name = child_table_name_map.get(k)
                    self.remove_child_rows(new_doc, child_table_field_name)
                    self.copy_child_table_attr(old_doc, new_doc, old_child_fieldname=k, new_child_fieldname=child_table_field_name)
                continue
            if (k == 'modified'):
                continue
            if doctype_different and k == 'doctype':
                continue
            setattr(new_doc, k, old_doc[k])

    def copy_child_table_attr(self, old_doc, new_doc, old_child_fieldname, new_child_fieldname=None):
        from frappe.core.doctype.dynamic_link.dynamic_link import DynamicLink
        if not old_doc.get(old_child_fieldname):
            return

        if not new_child_fieldname:
            new_child_fieldname = old_child_fieldname

        old_table = old_doc.get(old_child_fieldname)
        if isinstance(old_table, list):
            for i in old_table:
                if isinstance(i, DynamicLink):
                    continue
                new_table = new_doc.append(new_child_fieldname)
                for k in i.keys():
                    #'modified' interferes while saving document, gives the following error
                    #"Document has been modified after you have opened it"
                    if (k == 'modified'):
                        continue
                    if old_child_fieldname != new_child_fieldname and k =='parentfield':
                        setattr(new_table,k,new_child_fieldname)
                        continue
                    if old_child_fieldname != new_child_fieldname and k =='doctype':
                        setattr(new_table,k,None)
                        continue
                    setattr(new_table,k,i[k])
        else:
            new_table = new_doc.append(new_child_fieldname)
            for k in old_table.keys():
                setattr(new_table,k,old_table[k])
    
    def _import_document(self, old_doc_dict, doctype, different_doctype=False, before_insert=None, submit=False, \
                    overwrite=False, after_insert=None, copy_child_table=True, child_table_name_map=None, get_new_name=None, \
                    continue_on_error=False):
            doc = frappe._dict(old_doc_dict)
            new_doc = None
            if not frappe.db.exists(doctype, doc.name):
                new_doc = frappe.new_doc(doctype)
            elif overwrite:
                new_doc = frappe.get_doc(doctype, doc.name)
            if not new_doc:
                return
            if not new_doc.is_new() and new_doc.docstatus == 1: # Dont Touch Submitted Documents
                return
            self.copy_attr(doc, new_doc, copy_child_table=copy_child_table, doctype_different=different_doctype, child_table_name_map=child_table_name_map)
            if before_insert:
                try:
                    before_insert(new_doc, doc)
                except SkipRecordException:
                    return
            logging.info('Importing Doctype {0} with Name {1}'.format(doctype, doc.name))
            if new_doc.is_new():
                if get_new_name:
                    new_name = get_new_name(doc)
                self.insert_doc(new_doc, new_name=doc.name, continue_on_error=continue_on_error)
            elif overwrite:
                self.save_doc(new_doc)
            if after_insert:
                after_insert(new_doc, doc)

    def import_documents_having_childtables(self, doctype, new_doctype=None, id=None, old_doc_dict=None, overwrite=False, \
                        before_insert=None, submit=False, child_table_name_map=None, after_insert=None, copy_child_table=True, \
                        fetch_with_children=True, doc_list=None, fetch_filters=None, get_new_name=None, suppress_msg=False, \
                        in_batches=True, order_by=None, reset_batch=True, continue_on_error=False):

        if reset_batch and in_batches:
            self.batchdata = FetchData(self.remoteDBClient, self.parent_module, records_per_batch=1000)

        while True:
            fetched_doc_list = self.fetch_data(doctype, id=id, doc_list=doc_list, old_doc_dict=old_doc_dict, order_by=order_by, \
                            filters=fetch_filters, fetch_with_children=fetch_with_children, in_batches=in_batches)        

            if not fetched_doc_list or len(fetched_doc_list)<=0:
                break

            #--DEBUG-- print (fetched_doc_list)
            #--DEBUG-- print ("Testing", len(fetched_doc_list))
            #--DEBUG-- print (fetched_doc_list[0].get('name'), fetched_doc_list[-1].get('name'))
            
            self.start_import_process(doctype, fetched_doc_list, new_doctype=new_doctype, overwrite=overwrite, before_insert=before_insert, \
                        submit=submit, child_table_name_map=child_table_name_map, after_insert=after_insert, copy_child_table=copy_child_table, \
                        get_new_name=get_new_name, suppress_msg=suppress_msg, in_batches=in_batches, continue_on_error=continue_on_error)

            if not (in_batches and self.batchdata.has_more_records()):
                break            

    def start_import_process(self, doctype, doc_list, new_doctype=None, overwrite=False, \
                        before_insert=None, submit=False, child_table_name_map=None, after_insert=None, copy_child_table=True, \
                        get_new_name=None, suppress_msg=False, in_batches=True, continue_on_error=False):

        total_list_length = len(doc_list)
        if not new_doctype:
            new_doctype = doctype
        #Initialize Progress Bar
        if not suppress_msg:
            printProgressBar(doctype, 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)        
        for i, doc in enumerate(doc_list):     
            self._import_document(doc, new_doctype, different_doctype=True if new_doctype!=doctype else False, \
                            before_insert=before_insert, submit=submit, overwrite=overwrite, after_insert=after_insert, \
                            child_table_name_map=child_table_name_map,get_new_name=get_new_name, copy_child_table=copy_child_table, \
                            continue_on_error=continue_on_error)
            #Update Progress Bar
            if not suppress_msg:
                printProgressBar(doctype, i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
            if i % self.COMMIT_DELAY == 0:
                frappe.db.commit()
        frappe.db.commit()        

    def fetch_data(self, doctype, id=None, doc_list=None, old_doc_dict=None, filters=None, \
                            order_by=None, fetch_with_children=True, in_batches=True):

        if in_batches and not id and not old_doc_dict and not doc_list:                  
            if self.batchdata and not self.batchdata.has_data():
                self.batchdata.init_base_documents_list(doctype, filters=filters, order_by=order_by, fetch_with_children=fetch_with_children, in_batches=in_batches)
            return self.batchdata.get_next_batch()

        if id != None:
            return [frappe._dict(self.remoteDBClient.get_doc(doctype=doctype, name=id))]
        elif old_doc_dict != None:
            return [frappe._dict(old_doc_dict)]
        elif doc_list != None:
            return doc_list
        
        if fetch_with_children:
            return get_documents_with_childtables(self.remoteDBClient, self.parent_module, doctype, filters=filters, from_record=0, \
                            page_length=500, order_by=order_by)
        else:
            return get_documents_without_childtables(self.remoteDBClient, doctype, client_db_api_path=self.parent_module, filters=fitlers, \
                            from_record=0,page_length=500, order_by=order_by)

    def insert_doc(self, new_doc, new_name=None, submit=False, ignore_mandatory=None, ignore_if_duplicate=True, continue_on_error=False):
        new_doc.ignore_validate_hook = True
        try:
            new_doc.insert(ignore_permissions=True, set_name=new_name, ignore_if_duplicate=ignore_if_duplicate, ignore_mandatory=ignore_mandatory)
            if submit:
                new_doc.submit()
        except Exception as e:
            if not continue_on_error:
                raise 
            else:
                print ('#'*50)
                print ('Error Creating {0} Name:{1}'.format(new_doc.doctype, new_doc.name))
                print (str(e))
                print ('#'*50)
            
    def save_doc(self, new_doc, submit=False, continue_on_error=False):
        new_doc.ignore_validate_hook = True
        try:
            new_doc.save(ignore_permissions=True)
            if submit:
                new_doc.submit()      
        except Exception as e:
            if not continue_on_error:
                raise 
            else:
                print ('#'*50)
                print ('Error Updating {0} Name:{1}'.format(new_doc.doctype, new_doc.name))
                print (str(e))
                print ('#'*50)

# Print iterations progress
def printProgressBar (doctype, iteration, total, prefix = '', suffix = '', decimals = 1, length = 100, fill = '█', printEnd = "\r"):
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
    print(f'\r{prefix} |{bar}| {percent}% {suffix}', end = printEnd)
    # Print New Line on Complete
    if iteration == total: 
        print()
        print ("Imported:", doctype, "Total Records:", total, 'Completed At:',datetime.datetime.utcnow())

def make_gl_entries(self, cancel=0, adv_adj=0):
	from erpnext.accounts.general_ledger import make_gl_entries

	gl_map = []
	for d in self.get("accounts"):
		if d.debit or d.credit:
			r = [d.user_remark, self.remark]
			r = [x for x in r if x]
			remarks = "\n".join(r)

			gl_map.append(
				self.get_gl_dict({
					"account": d.account,
					"party_type": d.party_type,
					"due_date": self.due_date,
					"party": d.party,
					"against": d.against_account,
					"debit": flt(d.debit, d.precision("debit")),
					"credit": flt(d.credit, d.precision("credit")),
					"account_currency": d.account_currency,
					"debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
					"credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
					"against_voucher_type": d.reference_type,
					"against_voucher": d.reference_name,
					"remarks": remarks,
					"voucher_detail_no": d.reference_detail_no,
					"cost_center": d.cost_center,
					"project": d.project,
					"finance_book": self.finance_book
				}, item=d)
			)

	if self.voucher_type in ('Deferred Revenue', 'Deferred Expense'):
		update_outstanding = 'No'
	else:
		update_outstanding = 'Yes'

	if gl_map:
        #monkey here
		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, update_outstanding=update_outstanding,from_repost=True)

def monkey_patch_journal_entry_temporarily():
    from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
    JournalEntry.make_gl_entries = make_gl_entries