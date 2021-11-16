import frappe
import json
import datetime
from .frappeclient import FrappeClient
from frappe.utils import cstr, validate_email_address, validate_phone_number, flt
from erpnext import get_default_company

class ImportDB(object):
    def __init__(self, url, username, password, parent_module=None):
        self.remoteDBClient = FrappeClient(url, username=username, password=password)
        self.parent_module = parent_module
        if not self.parent_module:
            parent_module = "mapl_customization.customizations_for_mapl"

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
        self.import_customer_group()
        self.import_price_list()
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
        self.import_special_payment()
        self.import_special_invoice()
        self.import_loan_types()
        self.import_salary_components()
        self.import_holiday_lists()

    def import_entities(self, page_length=None):
        self.import_employees(to_record=1000 if not page_length else page_length)
        self.import_customers(to_record=30000 if not page_length else page_length)
        self.import_suppliers(to_record=1000 if not page_length else page_length)

    def import_salary_details(self):
        self.import_salary_structures()
        self.import_employee_loans()

    def import_accounts(self, overwrite=False):
        chart_of_accounts = self.remoteDBClient.get_list('Account', fields=["*"], limit_page_length=1000, order_by="lft")
        total_list_length = len(chart_of_accounts)
        #Initialize Progress Bar
        printProgressBar('Account', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, account in enumerate(chart_of_accounts):
            account = frappe._dict(account)            
            new_doc = None
            if not frappe.db.exists("Account", account.name):
                new_doc = frappe.new_doc("Account")
            else:
                new_doc = frappe.get_doc("Account", account.name)
                if not new_doc.get('parent_account'):
                    continue
            self.copy_attr(account, new_doc)
            new_doc.lft = None
            new_doc.rgt = None
            if not new_doc.get('parent_account'):
                new_doc.flags.ignore_mandatory = True
            if new_doc.is_new():
                self.insert_doc(new_doc, new_name=account.name)
            elif overwrite:                
                self.save_doc(new_doc)
            #Update Progress Bar
            printProgressBar('Account', i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_customer_group(self):
        self.import_simple_documents('Customer Group')

    def import_price_list(self):
        self.import_simple_documents('Price List')        

    def import_customers(self, from_record=0, to_record=None, ignore_existing=True, overwrite=False, id=None):
        if id:
            import_single_customer(id, ignore_existing=ignore_existing)
            return        
        customer_list = self.get_customer_supplier_list(doctype='Customer', from_record=from_record, to_record=to_record)
        total_list_length = len(customer_list)
        #Initialize Progress Bar
        printProgressBar('Customer', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, customer in enumerate(customer_list):
            if ignore_existing and frappe.db.exists('Customer', customer['name']):
                continue
            customer = frappe._dict(customer)
            self.import_customer(customer, overwrite=overwrite)
            #Update Progress Bar
            printProgressBar('Customer', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
            if idx % 500 == 0:
                frappe.db.commit()
        frappe.db.commit()                         

    def import_single_customer(id, ignore_existing=False):
        customer = self.remoteDBClient.get_doc('Customer', id)
        if ignore_existing and frappe.db.exists('Customer', customer['name']):
            return
        customer = frappe._dict(customer)
        self.import_customer(customer)
        frappe.db.commit()

    def import_suppliers(self, from_record=0, to_record=None, ignore_existing=True, overwrite=False):
        supplier_list = self.get_customer_supplier_list(doctype='Supplier', from_record=from_record, to_record=to_record)
        total_list_length = len(supplier_list)
        #Initialize Progress Bar
        printProgressBar('Supplier', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, supplier in enumerate(supplier_list):
            if ignore_existing and frappe.db.exists('Supplier', supplier['name']):
                continue
            supplier = frappe._dict(supplier)
            self.import_supplier(supplier, overwrite=overwrite)
            #Update Progress Bar
            printProgressBar('Supplier', i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_employee_branches(self):
        self.import_simple_documents('Branch')

    def import_employee_designation(self):
        self.import_simple_documents('Designation')

    def import_employees(self, from_record=0, to_record=None):
        def before_inserting(doc, old_doc):
            fn, mn, ln = self.split_name(old_doc.employee_name)
            doc.first_name = fn
            doc.middle_name = mn
            doc.last_name = ln

        self.import_simple_documents(doctype='Employee', from_record=from_record, to_record=to_record, before_insert=before_inserting)

    def import_brands(self):
        self.import_simple_documents('Brand')

    def import_warehouses(self):
        self.import_simple_documents('Warehouse', order_by="lft")

    def import_itemgroups(self):
        self.import_simple_documents('Item Group', order_by="lft")
    
    def import_uom(self):
        self.import_simple_documents('UOM')

    def import_cost_center(self):
        self.import_simple_documents('Cost Center', order_by="lft")

    def import_fiscal_years(self):
        self.import_simple_documents('Fiscal Year')

    def import_terms_conditions(self):
        self.import_simple_documents('Terms and Conditions')
    
    def import_hypthecation(self):
        self.import_simple_documents("Hypothecation Company")

    def import_special_payment(self):
        self.import_simple_documents("Special Payment")

    def import_special_invoice(self):
        self.import_simple_documents("Special Invoicing")

    def import_salary_components(self):
        def remove_depends_on_payment_days(doc, old_doc):
            if doc.type=='Deduction':
                doc.depends_on_payment_days = 0

        self.import_documents_with_child_tables('Salary Component', overwrite_existing=True, before_insert=remove_depends_on_payment_days)

    def import_asset_category(self):
        self.import_documents_with_child_tables('Asset Category')

    def import_mode_of_payment(self):
        self.import_documents_with_child_tables('Mode of Payment')

    def import_tax_and_charges_template(self):
        for docs in ['Purchase Taxes and Charges Template','Sales Taxes and Charges Template']:
            self.import_documents_with_child_tables(docs)

    def import_item_tax_templates(self):
        def before_inserting(doc, old_doc):
            doc.title = old_doc.name

        self.import_documents_with_child_tables('Item Taxes Template', new_doctype='Item Tax Template',before_insert=before_inserting)

    def import_items(self,from_record=0, to_record=None):
        item_list = self.get_item_list(from_record, to_record)
        total_list_length = len(item_list)
        #Initialize Progress Bar
        printProgressBar('Item', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, item in enumerate(item_list):
            item = frappe._dict(item)            
            if not frappe.db.exists("Item", item.name):
                new_doc = frappe.new_doc("Item")
                new_doc = self.make_new_item_doc(item)
                self.insert_doc(new_doc, new_name=item.name)
            if idx % 500 == 0:
                frappe.db.commit()            
            #Update Progress Bar
            printProgressBar('Item', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_single_item(self, item_name):
        if frappe.db.exists("Item", item_name):
            return
        item = frappe._dict(self.remoteDBClient.get_doc('Item', item_name))
        new_doc = self.make_new_item_doc(item)
        self.insert_doc(new_doc, new_name=item.name)
        frappe.db.commit()
    
    def make_new_item_doc(self, old_item_dict):
        new_doc = frappe.new_doc("Item")
        self.copy_attr(old_item_dict, new_doc)
        if old_item_dict.get('expense_account') or old_item_dict.get('income_account'):
            item_defaults = new_doc.append('item_defaults')
            item_defaults.company = get_default_company()
            item_defaults.expense_account = old_item_dict.get('expense_account')
            item_defaults.income_account = old_item_dict.get('income_account')
        if old_item_dict.get('taxes_template'):
            taxes = new_doc.append('taxes')
            taxes.item_tax_template = self.get_substitute_tax_template(old_item_dict.taxes_template)
        return new_doc
    
    def get_substitute_tax_template(self, tax_template):
        #if tax_template == 'GST 28%':
        #    return 'GST 28% - MAPL'
        #if tax_template == 'GST 18%':
        #    return 'GST 18% - MAPL'
        #if tax_template == 'GST 12%':
        #    return 'GST 12% - MAPL'
        #if tax_template == 'GST 5%':
        #    return 'GST 5% - MAPL'
        return tax_template

    def import_holiday_lists(self):
        self.import_documents_with_child_tables('Holiday List')

    def import_loan_types(self):
        def before_inserting(new_doc, old_doc):
            #New Fields in New Version
            new_doc.is_term_loan = 1
            new_doc.mode_of_payment = "Cash"
            new_doc.payment_account = frappe.db.get_value("Account", filters=dict(name=("like", "Cash -%")))            
            new_doc.loan_account = frappe.db.get_value("Account", filters=dict(name=("like", "Salary Advance %")))
            new_doc.interest_income_account = frappe.db.get_value("Account", filters=dict(name=("like", "Interest Received %")))
            new_doc.penalty_income_account = frappe.db.get_value("Account", filters=dict(name=("like", "Interest Received %")))

        self.import_documents_with_child_tables('Loan Type', before_insert=before_inserting, submit=True)            

    def import_salary_structures(self):
        doc_list = self.get_doc_list('Salary Structure', filters="""[["Salary Structure", "is_active","=","Yes"]]""")
        if not doc_list or len(doc_list)<=0:
            return
        total_list_length = len(doc_list)
        #Initialize Progress Bar
        printProgressBar('Salary Structure', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, doc in enumerate(doc_list):
            if frappe.db.exists("Salary Structure",doc['name']):
                continue
            doc = frappe._dict(doc)
            new_structure = frappe.new_doc("Salary Structure")
            self.copy_attr(doc, new_structure, copy_child_table=False)
            self.copy_child_table_attr(doc, new_structure, 'earnings')
            self.copy_child_table_attr(doc, new_structure, 'deductions')
            new_doc_name = doc.name.split('-')[0].strip()
            new_structure.flags.ignore_validate = True
            self.insert_doc(new_structure, new_name=doc['name'], submit=True)
            for employees in doc.get('employees'):                
                if frappe.db.exists("Salary Structure Assignment", doc.name):
                    continue
                assign_structure = frappe.new_doc("Salary Structure Assignment")
                self.copy_attr(employees, assign_structure, copy_child_table=False)
                assign_structure.doctype = "Salary Structure Assignment"
                assign_structure.salary_structure = doc['name'] if assign_structure.employee_name.lower() in doc['name'].lower() \
                                                    else (doc['name']+' '+assign_structure.employee_name)
                assign_structure.flags.ignore_validate = True
                self.insert_doc(assign_structure, new_name=doc.name, submit=True)
            #Update Progress Bar
            printProgressBar('Salary Structure', i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()           

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

        self.import_documents_with_child_tables('Employee Loan', new_doctype='Loan', before_insert=before_inserting)

    def import_stock_transactions(self,from_date=None, to_date=None, page_length=None):
        #sl_ledger_entries = self.get_sl_entries(from_date=from_date, to_date=to_date, from_record=from_record, to_record=to_record)        
        sl_ledger_entries = self.get_transactions(from_date=from_date, to_date=to_date, page_length=page_length)
        print ('Importing Stock Transactions')
        self.import_transactions(sl_ledger_entries)
    
    def import_transactions(self, entries):
        if not entries or len(entries)<=0:
            return
        negative_stock = frappe.db.get_value("Stock Settings", None, "allow_negative_stock")
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", 1)
        total_list_length = len(entries)
        #Initialize Progress Bar
        printProgressBar('Transactions', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, s in enumerate(entries):
            if frappe.db.exists(s['doctype'], s['name']):
                continue
            s = frappe._dict(s)            
            if (s.doctype == 'Stock Entry'):
                self.import_stock_entry(s)
                #self.import_stock_entry(s.voucher_no)
            elif (s.doctype == 'Purchase Invoice'):
                self.import_purchase_invoice(s)
                #self.import_stock_entry(s.voucher_no)
            elif (s.doctype == 'Sales Invoice'):
                self.import_sales_invoice(s)
                #self.import_stock_entry(s.voucher_no)
            #Update Progress Bar
            printProgressBar('Transactions', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", negative_stock)
        frappe.db.commit()
    
    def import_non_stock_transactions(self, from_date=None, to_date=None, page_length=None):
        ledger_entries = self.get_transactions(from_date=from_date, to_date=to_date, page_length=page_length,non_stock=True)
        print ('Importing Non Stock Transactions')
        self.import_transactions(ledger_entries)
    
    def import_payment_entries(self, from_date=None, to_date=None, page_length=None):
        entries = self.get_entries('Payment Entry', from_date=from_date, to_date=to_date, page_length=page_length)
        if not entries or len(entries)<=0:
            return
        total_list_length = len(entries)
        printProgressBar('Payment Entries', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, e in enumerate(entries):
            if frappe.db.exists('Payment Entry', e['name']):
                continue
            if e['docstatus'] == 2:
                continue
            e = frappe._dict(e)
            self.import_payment_entry(e)
            #Update Progress Bar
            printProgressBar('Payment Entries', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_journal_entries(self, from_date=None, to_date=None, page_length=None, id=None):
        if id:
            self.import_single_jv(id)
            return

        entries = self.get_entries('Journal Entry', from_date=from_date, to_date=to_date, page_length=page_length)
        if not entries or len(entries)<=0:
            return
        total_list_length = len(entries)
        printProgressBar('Journal Entries', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for idx, e in enumerate(entries):
            if frappe.db.exists('Journal Entry', e['name']):
                continue
            if e['docstatus'] == 2:
                continue
            e = frappe._dict(e)
            self.import_journal_entry(e)
            #Update Progress Bar
            printProgressBar('Journal Entries', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_single_jv(self, id):
        doc = self.remoteDBClient.get_doc('Journal Entry',id)
        if doc and not frappe.db.exists('Journal Entry', doc['name']):
            self.import_journal_entry(frappe._dict(doc))
            frappe.db.commit()     

    def import_period_closing_vouchers(self):
        self.import_simple_documents('Period Closing Voucher', order_by='transaction_date')

    def get_entries(self, doctype, from_date=None, to_date=None, page_length=None):
        if not page_length and not to_date:
            page_length = 50
        else:
            page_length = 1000000 #Try and Get All Transactions Till The To Date Specified
        date_filters = "["
        if from_date:
            date_filters = date_filters+"""[\""""+doctype+"""\","posting_date",">=",\""""+from_date+"""\"]"""
        if to_date:
            if from_date:
                date_filters = date_filters + ","
            date_filters = date_filters+"""[\""""+doctype+"""\","posting_date","<=",\""""+to_date+"""\"]"""
        date_filters = date_filters + "]"
        if len(date_filters)<=2:
            date_filters = None
        return self.get_doc_list(doctype, filters=date_filters, 
                        to_record=page_length if page_length else 50,order_by="posting_date")

    def get_transactions(self, from_date=None, to_date=None, page_length=None, non_stock=False):
        if not page_length and not to_date:
            page_length = 50
        else:
            page_length = 1000000 #Try and Get All Transactions Till The To Date Specified
        if not from_date:
            from_date = '01-04-2017'
        if not to_date:
            to_date = '30-06-2017'
        return self.remoteDBClient.get_api(self.parent_module+'.rest_api.get_doc_list_as_per_transactions',
                            params={'transaction_doctype':'Stock Ledger Entry',
                                'from_date':from_date,
                                'to_date':to_date,
                                'page_length':page_length,
                                'non_stock':non_stock})
                
    def get_item_list(self, from_record=0, to_record=None):
        return self.remoteDBClient.get_list('Item', fields=["*"], 
                limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 50, order_by="name")

    def get_customer_supplier_list(self, doctype='Customer', from_record=0, to_record=None):
        return self.get_doc_list(doctype, from_record=from_record, to_record=to_record if to_record else 50,order_by="name")
        #return self.remoteDBClient.get_list(doctype, fields=["*"], 
        #        limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 50, order_by="name")                

    def get_address_list(self, doctype, docname, from_record=0, to_record=None):
        filters = [
            ["Dynamic Link", "link_doctype", "=", doctype],
            ["Dynamic Link", "link_name", "=", docname],
            ["Dynamic Link", "parenttype", "=", "Address"],
        ]
        return self.remoteDBClient.get_list("Address", fields=["*"], filters=filters,
                limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 500, order_by="name")                

    def import_stock_entry(self, old_doc):
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Stock Entry', name=voucher_no))
        new_doc = frappe.new_doc('Stock Entry')
        self.copy_attr(old_doc, new_doc, copy_child_table=True)
        #Fieldname Changed in New Version
        new_doc.stock_entry_type = old_doc.purpose
        new_doc.flags.ignore_validate = True
        new_doc.amended_from = None
        self.insert_doc(new_doc,new_name=old_doc.name)                

    def import_purchase_invoice(self, old_doc):
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Purchase Invoice', name=voucher_no))
        new_doc = frappe.new_doc('Purchase Invoice')
        self.copy_attr(old_doc, new_doc, copy_child_table=True)
        new_doc.flags.ignore_validate = True
        new_doc.amended_from = None
        self.insert_doc(new_doc, new_name=old_doc.name)

    def import_sales_invoice(self, old_doc):
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Sales Invoice', name=voucher_no))
        new_doc = frappe.new_doc('Sales Invoice')
        self.copy_attr(old_doc, new_doc, copy_child_table=True)
        new_doc.flags.ignore_validate = True
        new_doc.amended_from = None
        new_doc.invoice_copy = 'Original for Recipient'
        self.insert_doc(new_doc, new_name=old_doc.name)
        #frappe.db.commit() #For Testing Only

    def import_journal_entry(self, old_doc):
        monkey_patch_journal_entry_temporarily()
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Journal Entry', name=old_doc))
        new_doc = frappe.new_doc('Journal Entry')
        self.copy_attr(old_doc, new_doc, copy_child_table=True)
        new_doc.flags.ignore_validate = True
        for row in new_doc.accounts:
            row.reference_name = None
            row.reference_type = None
        new_doc.amended_from = None
        self.insert_doc(new_doc, new_name=old_doc.name)
        #frappe.db.commit() #For Testing Only

    def import_payment_entry(self, old_doc):
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Payment Entry', name=old_doc))
        new_doc = frappe.new_doc('Payment Entry')
        self.copy_attr(old_doc, new_doc, copy_child_table=True)
        new_doc.flags.ignore_validate = True
        #Dont Copy Sales Invoice Reference
        new_doc.references = None
        new_doc.base_total_allocated_amount = None
        new_doc.total_allocated_amount = None
        new_doc.allocate_payment_amount = None
        new_doc.amended_from = None
        new_doc.unallocated_amount = new_doc.paid_amount
        self.insert_doc(new_doc, new_name=old_doc.name)
        #frappe.db.commit() #For Testing Only

    def import_customer(self, old_customer_dict, import_addresses=True, auto_create_customer_contacts=True, overwrite=False):
        #old_doc = frappe._dict(self.remoteDBClient.get_doc(doctype='Customer', name=customer_name))
        new_doc = None
        if frappe.db.exists('Customer', old_customer_dict.name):
            new_doc = frappe.get_doc('Customer', old_customer_dict.name)
        else:
            new_doc = frappe.new_doc('Customer')
        self.copy_attr(old_customer_dict, new_doc, copy_child_table=True)
        if new_doc.is_new():
            self.insert_doc(new_doc, new_name=old_customer_dict.name)
        elif overwrite:
            self.save_doc(new_doc)
        if import_addresses:
            self.import_address('Customer', old_customer_dict.name)
        if auto_create_customer_contacts:
            self.create_contact(old_customer_dict, old_customer_dict.name)

    def import_supplier(self, old_supplier_dict, import_addresses=True, overwrite=False):
        new_doc = None
        if frappe.db.exists('Supplier', old_supplier_dict.name):
            new_doc = frappe.get_doc('Supplier', old_supplier_dict.name)
        else:
            new_doc = frappe.new_doc('Supplier')
        self.copy_attr(old_supplier_dict, new_doc, copy_child_table=True)
        #Field Name Change in New Version
        setattr(new_doc, 'supplier_group', old_supplier_dict.get('supplier_type'))
        if not frappe.db.exists('Supplier Group', new_doc.supplier_group):
            new_doc.supplier_group = 'All Supplier Groups'
        delattr(new_doc, 'supplier_type')
        if new_doc.is_new():
            self.insert_doc(new_doc, new_name=old_supplier_dict.name)
        elif overwrite:
            self.save_doc(new_doc)
        if import_addresses:
            self.import_address('Supplier', old_supplier_dict.name)

    def import_address(self, doctype, docname):
        address_list = self.get_address_list(doctype=doctype, docname=docname)
        for address in address_list:
            new_doc = None
            address = frappe._dict(address)
            if not frappe.db.exists("Address", address.name):
                new_doc = frappe.new_doc("Address")
            else:
                new_doc = frappe.get_doc("Address",address.name)
            self.copy_attr(address, new_doc, copy_child_table=True)
            if new_doc.get('email_id') and not validate_email_address(new_doc.email_id):
                    delattr(new_doc, 'email_id')
            if new_doc.get('state') and new_doc.state.lower() == 'chattisgarh':
                    new_doc.state = 'Chhattisgarh'
            if new_doc.get('gst_state') and new_doc.gst_state.lower() == 'chattisgarh':
                    new_doc.gst_state = 'Chhattisgarh'
            if new_doc.is_new():
                new_doc.append('links', dict(link_doctype=doctype, link_name=docname))
                self.insert_doc(new_doc, new_name=address.name, continue_on_error=1)
            else:
                self.save_doc(new_doc, continue_on_error=1)
    
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

    def get_doc_list(self,doctype,fields=None,filters=None,from_record=0,to_record=500,order_by=None):
        return self.remoteDBClient.get_api(self.parent_module+'.rest_api.get_doc_list',
                            params={'doctype':doctype,
                                'filters':filters,
                                'fields':fields,
                                'from_record':from_record,
                                'to_record':to_record,
                                'order_by':order_by})
    
    def remove_child_rows(self,new_doc, child_table):
        if (new_doc.get(child_table) and not new_doc.is_new() and new_doc.docstatus == 0): #Child Not Empty
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
    
    def copy_attr(self, old_doc, new_doc, copy_child_table=False, doctype_different=False):
        for k in old_doc.keys():            
            if isinstance(old_doc[k], dict) or isinstance(old_doc[k], list):
                if copy_child_table:
                    self.remove_child_rows(new_doc, k)
                    self.copy_child_table_attr(old_doc, new_doc, k)
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
                    setattr(new_table,k,i[k])
        else:
            new_table = new_doc.append(new_child_fieldname)
            for k in old_table.keys():
                setattr(new_table,k,old_table[k])
    
    def import_simple_documents(self, doctype, from_record=0, to_record=500, order_by=None, before_insert=None, submit=False, overwrite=False):
        doc_list = self.remoteDBClient.get_list(doctype, fields=["*"], limit_start=from_record, 
                            limit_page_length=to_record, order_by=order_by)
        if not doc_list or len(doc_list)<=0:
            return
        total_list_length = len(doc_list)
        #Initialize Progress Bar
        printProgressBar(doctype, 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, doc in enumerate(doc_list):
            doc = frappe._dict(doc)
            new_doc = None
            if not frappe.db.exists(doctype, doc.name):
                new_doc = frappe.new_doc(doctype)
            elif overwrite:
                new_doc = frappe.new_doc(doctype, doc.name)
            if not new_doc:
                continue
            self.copy_attr(doc, new_doc, copy_child_table=True)
            if before_insert:
                before_insert(new_doc, doc)
            if new_doc.is_new():
                self.insert_doc(new_doc, new_name=doc.name)
            elif overwrite:
                self.save_doc(new_doc)
            #Update Progress Bar
            printProgressBar(doctype, i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()

    def import_documents_with_child_tables(self, doctype, new_doctype=None, overwrite_existing=False, before_insert=None, submit=False):
        doc_list = self.get_doc_list(doctype)
        if not doc_list or len(doc_list)<=0:
            return
        total_list_length = len(doc_list)
        if not new_doctype:
            new_doctype = doctype
        printProgressBar(doctype, 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        for i, doc in enumerate(doc_list):
            new_doc = None
            if not frappe.db.exists(new_doctype, doc['name']) and not overwrite_existing:
                new_doc = frappe.new_doc(new_doctype)
            else:
                new_doc = frappe.get_doc(new_doctype, doc['name'])
            doc = frappe._dict(doc)
            #doc = frappe._dict(self.remoteDBClient.get_doc('Asset Category', doc['name']))
            self.copy_attr(doc, new_doc, copy_child_table=True, doctype_different=True if new_doctype!=doctype else False)
            if before_insert:
                before_insert(new_doc, doc)
            if new_doc.is_new():
                self.insert_doc(new_doc, new_name=doc.name, submit=submit)
            elif overwrite_existing:
                self.save_doc(new_doc, submit=submit)
            printProgressBar(doctype, i + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        frappe.db.commit()        

    def remove_base_fields(self, new_doc):
        new_doc.__dict__.pop('creation', None)
        new_doc.__dict__.pop('modified', None)
        new_doc.__dict__.pop('rgt', None)
        new_doc.__dict__.pop('lft', None)
        new_doc.__dict__.pop('modified_by', None)

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

    #Deprecated
    def get_sl_entries(self, from_date=None, to_date=None, from_record=0, to_record=None):
        sl_ledger_fields = [
            "voucher_type",
            "voucher_no",
            "posting_date"
        ]
        filters = []
        if from_date:
            filters.extend([
                ["posting_date", ">=", from_date]
            ])
        if to_date:
            filters.extend([
                ["posting_date", "<=", to_date]
            ])
        if len(filters>0):
            from_record = 0
            to_record = 10000 #Need to Check
        return self.remoteDBClient.get_list('Stock Ledger Entry', fields=sl_ledger_fields, filters=filters if len(filters)>0 else None,
                limit_start=from_record, limit_page_length=(to_record-from_record) if to_record else 50, order_by="posting_date")                

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