import frappe
import datetime
import logging
import json
from frappe import CharacterLengthExceededError
from .monkey_patch_import import *
from .common import *
from .frappeclient import FrappeClient
from .get_data import *
from frappe.utils import cstr, validate_email_address, validate_phone_number, flt, getdate, format_date, cint, add_to_date
from erpnext import get_default_company
from erpnext.regional.india import number_state_mapping, state_numbers, states
from mapl_customization.customizations_for_mapl.utils import set_state_code

class SkipRecordException(Exception):
    pass 

class ErrorInsertingRecord(Exception):
    pass

class InvalidStockEntries(Exception):
    pass

class ImportDB(object):
    def __init__(self, url, username, password, parent_module=None, log_test=False, overwrite_if_modified_after=None):
        self.remoteDBClient = FrappeClient(url, username=username, password=password)
        self.parent_module = parent_module
        self.log_test = log_test
        self.overwrite_if_modified_after = overwrite_if_modified_after        
        logging.basicConfig(filename="/home/frappe/import_log.log",filemode='w',level=logging.INFO)
        logging.info('Initialized Importing Instance at {0}'.format(datetime.datetime.utcnow()))
        self.COMMIT_DELAY = 500
        if not self.parent_module:
            self.parent_module = "mapl_customization.customizations_for_mapl"
        self.dates_map = [
            ["01-04-2017", "30-06-2017"],
            ["01-07-2017", "30-09-2017"],
            ["01-10-2017", "15-10-2017"], # 
            ["16-10-2017", "31-10-2017", 20], # To Avoid a Serial No Purchase on 30.10, Sold on 17.10, Day Interval=20
            ["01-11-2017", "31-03-2018"],
            ["01-04-2018", "07-05-2018"],
            ["08-05-2018", "31-05-2018"], # To Avoid a Serial No Purchase on 10.05, Sold on 08.05
            ["01-06-2018", "15-09-2018"], # 16.09 There was a problem serial no unupdated
            ["16-09-2018", "25-12-2018"],
            ["26-12-2018", "31-12-2018"], # MAPL/PINV-RET/VN/18-19/000010 purchase return has wrong serial no
            ["01-01-2019", "31-03-2019"],
            ["01-04-2019", "30-09-2019"],
            ["01-10-2019", "31-03-2020"],
            ["01-04-2020", "30-09-2020"],
            ["01-10-2020", "31-03-2021"],
            ["01-04-2021", "30-06-2021"],
            ["01-07-2021", "30-09-2021"],
            ["01-10-2021", "06-11-2021"],
            ["07-11-2021", "17-11-2021", 15], # To Avoid a Serial No Purchase on 15.11, Sold on 07.11 
            ["18-11-2021", "30-11-2021"],
            ["01-12-2021", "31-12-2021"],
            ["01-01-2022", "31-01-2022"],
            ["01-02-2022", "10-02-2022"]
        ]

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
        self.import_departments()
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
        self.import_manufacturers()
        self.make_battery_details()

    def import_entities(self, page_length=None):
        self.import_employees()
        self.import_customers() #30000
        self.import_suppliers()

    def import_salary_details(self):
        self.import_salary_structures()
        self.import_employee_loans()
        self.import_employee_salary_slips()
    
    def get_day_interval_from_date_map(self, dmap):
        interval = None
        try:
            interval = dmap[2]
        except IndexError:
            pass
        return interval

    def process(self, till_date=False, import_modules=None, dates_map=None, day_interval=10):
        if not dates_map:
            dates_map  = self.dates_map
        print ("Staring Process at",datetime.datetime.utcnow())
        log_info(logging, 'Started Process at {0}'.format(datetime.datetime.utcnow()))
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
        if not dates_map:
            dates_map = default_dates_map
        dt = format_date(getdate())        
        if not import_modules or "stock_transactions" in import_modules:
            for d in dates_map:
                self.import_stock_transactions(from_date=d[0],to_date=d[1], 
                        day_interval=self.get_day_interval_from_date_map(d) or day_interval)
            if till_date:
                self.import_stock_transactions(from_date="01-04-2021",to_date=dt)
        if not import_modules or "non_stock_transactions" in import_modules:
            for d in dates_map:
                self.import_stock_transactions(from_date=d[0],to_date=d[1], non_sle_entries=True, 
                        day_interval=self.get_day_interval_from_date_map(d) or day_interval)
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
        self.update_naming_series()
        print ("Completed Process at",datetime.datetime.utcnow())
        log_info(logging,'Completed Process at {0}'.format(datetime.datetime.utcnow()))

    def post_process(self, dates_map=None):
        if not dates_map:
            dates_map = self.dates_map
        self.import_draft_documents()
        set_loans_accured()
        self.import_biometric_details(dates_map=dates_map)
        self.update_naming_series()

    def import_accounts(self, overwrite=False):
        def before_inserting(new_doc, old_doc):
            new_doc.lft = None
            new_doc.rgt = None
            if not new_doc.get('parent_account'):
                new_doc.flags.ignore_mandatory = True
            if not new_doc.is_new() and not new_doc.get('parent_account'):
                raise SkipRecordException("Skiped Record {0}".format(new_doc.name))
            if not new_doc.is_new():
                frappe.local.flags.ignore_update_nsm = True

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
            if new_doc.supplier_type not in new_doc.meta.get_field('supplier_type').options.split('\n'):
                new_doc.supplier_type = 'Individual'

        def after_insert(new_doc, old_supplier_dict, import_addresses=True):
            if import_addresses:
                self.import_address('Supplier', old_supplier_dict)        

        self.import_documents_having_childtables('Supplier', before_insert=before_insert, after_insert=after_insert, \
            overwrite=overwrite, id=id, copy_child_table=False)

    def import_user_groups(self):
        self.import_documents_having_childtables('User Group')

    def import_employee_branches(self):
        self.import_documents_having_childtables('Branch')

    def import_departments(self):
        self.import_documents_having_childtables('Department')

    def import_employee_designation(self):
        self.import_documents_having_childtables('Designation')

    def import_employees(self):
        def before_inserting(doc, old_doc):
            fn, mn, ln = split_name(old_doc.employee_name)
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

        def before_insert(new_doc, old_doc):
            remove_depends_on_payment_days(new_doc, old_doc)
            for a in old_doc.get('accounts'):
                acc = new_doc.append('accounts')
                acc.company = a.get('company')
                acc.account = a.get('default_account')

        self.import_documents_having_childtables('Salary Component', overwrite=True, before_insert=before_insert, copy_child_table=False)

    def import_asset_category(self):
        self.import_documents_having_childtables('Asset Category')

    def import_mode_of_payment(self, overwrite=False):
        self.import_documents_having_childtables('Mode of Payment', overwrite=overwrite)

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

    def import_manufacturers(self):
        self.import_documents_having_childtables("Manufacturer")

    def make_battery_details(self):
        manufacturer_list = [("Trontek", "Trontek Electronics Pvt Ltd"), ("Akira", "Akira")]
        for m in manufacturer_list:
            manufacturer = frappe.new_doc("Manufacturer")
            manufacturer.short_name = m[0]
            manufacturer.full_name = m[1]
            manufacturer.insert(ignore_if_duplicate=True)        
        battery_type = frappe.new_doc("Battery Type")
        battery_type.type = "(2.9 KWh) 72V * 40 AH"
        battery_type.insert(ignore_if_duplicate=True)

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
            new_doc.disbursement_account = frappe.db.get_value("Account", filters=dict(name=("like", "Cash -%")))

        self.import_documents_having_childtables('Loan Type', before_insert=before_inserting, submit=True)            

    def import_salary_structures(self):
        def new_name(old_doc):
            return old_doc.name.split('-')[0].strip()

        def before_salary_structure(new_doc, old_doc):
            self.copy_child_table_attr(old_doc, new_doc, 'earnings')
            self.copy_child_table_attr(old_doc, new_doc, 'deductions')
            new_doc.flags.ignore_validate = True

        def after_salary_structure(new_doc, old_doc):
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

        self.import_documents_having_childtables('Salary Structure', before_insert=before_salary_structure, after_insert=after_salary_structure, \
                                    copy_child_table=False, fetch_with_children=True, submit=True)

    def import_employee_loans(self):
        def before_inserting(doc, old_doc):
            doc.applicant_type = 'Employee'
            doc.applicant = doc.employee
            doc.applicant_name = doc.employee_name
            doc.loan_account = doc.employee_loan_account
            doc.penalty_income_account = doc.interest_income_account
            doc.is_term_loan = 1
            doc.repay_from_salary = 1
            if doc.status == 'Fully Disbursed':
                doc.status = 'Disbursed'
            if doc.status == 'Repaid/Closed':
                doc.status = 'Closed'
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

        monkey_patch_salary_slip_temporarily()
        self.import_documents_having_childtables('Salary Slip', child_table_name_map={'loan_deduction_detail':'loans'}, before_insert=before_inserting)

    def import_stock_transactions(self,from_date=None, to_date=None, non_sle_entries=False, day_interval=5, id=None, overwrite=True):
        if id and (not isinstance(id, dict) or (not id.get('name') or not id.get('doctype'))):
            print ("ID Format Error")
            print ("Should be a Dictionary with name and doctype")
            return
        print ('Importing Stock Transactions')
        monkey_patch_sales_invoice_temporarily()
        monkey_patch_serial_no_temporarily()
        negative_stock = frappe.db.get_value("Stock Settings", None, "allow_negative_stock")
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", 1)
        self._import_stock_transactions(from_date=from_date, to_date=to_date, non_sle_entries=non_sle_entries, day_interval=day_interval, id=id, overwrite=overwrite)
        frappe.db.set_value("Stock Settings", None, "allow_negative_stock", negative_stock)
        self.commit()

    def _import_stock_transactions(self,from_date=None, to_date=None, non_sle_entries=False, day_interval=5, id=None, overwrite=True):
        def import_single_entry():
            entries = [frappe._dict(self.remoteDBClient.get_doc(doctype=id.get('doctype'), name=id.get('name')))]
            id_filters = {
                "voucher_no": id.get('name'),
                "voucher_type": id.get('doctype')
            }
            if not self.remoteDBClient.get_value('Stock Ledger Entry', filters=id_filters):
                non_sle_entries = True
            else:
                non_sle_entries = False
            if not entries or len(entries)<=0:
                print ('No Record Found')
                return
            self.import_transactions(entries, non_sle_entries=non_sle_entries, overwrite=overwrite)

        if id:
            import_single_entry()
            return
        batchdata = FetchData(self.remoteDBClient, self.parent_module, day_interval=day_interval)
        if not non_sle_entries:
            batchdata.init_stock_transactions(from_date=from_date, to_date=to_date)
        else:
            batchdata.init_non_stock_transactions(from_date=from_date, to_date=to_date)    
        while batchdata.has_more_records():
            entries = batchdata.get_next_batch()
            if not entries or len(entries)<=0:
                break
            #--DEBUG-- print ("Testing", len(entries))    
            self.import_transactions(entries, non_sle_entries=non_sle_entries, overwrite=overwrite)

    def import_transactions(self, entries, non_sle_entries=False, overwrite=True):
        from erpnext.stock.doctype.serial_no.serial_no import SerialNoNotExistsError, SerialNoWarehouseError
        from erpnext.stock.stock_ledger import NegativeStockError, SerialNoExistsInFutureTransaction

        def common_functions(new_doc, old_doc):
            for i in new_doc.items:
                if i.get('brand') and i.brand.lower() == 'jbl':
                    i.brand = 'JBL/HARMAN'
                # Exceptions for Wrong Serial No
                if old_doc.name == 'MAPL/PINV-RET/VN/18-19/000010':
                    if '211548100772368PRPEIL' in i.serial_no:
                        i.serial_no = i.serial_no.replace('211548100772368PRPEIL','21154810075608PRPEIL')
                if old_doc.name == 'MAPL/INV/VN/20-21/001595':
                    if '0D154DBN700796' in i.serial_no:
                        i.serial_no = i.serial_no.replace('0D154DBN700796','0D154DBN300065')
            if old_doc.doctype in ['Sales Invoice', 'Purchase Invoice']:
                new_doc.set_incoming_rate() #Set Incoming Rate - Specially when a SRN is Done

        def before_inserting(new_doc, old_doc):
            new_doc.flags.ignore_validate = True
            new_doc.amended_from = None
            if old_doc.doctype == 'Stock Entry':
                new_doc.stock_entry_type = old_doc.purpose
                if new_doc.total_incoming_value == 0 and new_doc.total_outgoing_value == 0:
                    for i in new_doc.items:
                        i.allow_zero_valuation_rate = 1
                if old_doc.purpose.lower() != 'material receipt':
                    new_doc.get_stock_and_rate() #Update Rate in Stock Entry, Don't Take Original Values from Old DB
            if old_doc.doctype == 'Purchase Invoice':
                for i in new_doc.items:
                    if i.amount == 0:
                        i.allow_zero_valuation_rate = 1

            if old_doc.doctype == 'Sales Invoice':
                new_doc.invoice_copy = 'Original for Recipient'
                new_doc.delayed_payment_remarks = old_doc.get('special_remarks')
                new_doc.notes = old_doc.get('reference_details')
                new_doc.advances = None
                if new_doc.get('vehicle_no'):
                    new_doc.vehicle_no = new_doc.vehicle_no.replace(" ","")
                    if len(new_doc.vehicle_no) > 10:
                        new_doc.vehicle_no = new_doc.vehicle_no[:10]
                for i in new_doc.items:
                    if cint(i.is_electric_vehicle) and i.battery_manufacturer:
                        if "tek" in i.battery_manufacturer.lower():
                            i.battery_manufacturer = "Trontek"
                            i.battery_type = "(2.9 KWh) 72V * 40 AH"
                        elif "akira" in i.battery_manufacturer.lower():
                            i.manufacturer = "Akira"
                if new_doc.get('workflow_state') and new_doc.workflow_state == 'Draft':
                    new_doc.workflow_state = 'Pending'
                #new_doc.update_current_stock()
            common_functions(new_doc, old_doc)                
            #--DEBUG-- print ("Old Doc:", old_doc.doctype, old_doc.name, old_doc.posting_date, old_doc.posting_time)                
            #--DEBUG-- print ("New Doc:", new_doc.doctype, new_doc.name, new_doc.posting_date, new_doc.posting_time)
            #--DEBUG-- raise SkipRecordException("testing")
        
        def after_inserting(new_doc, old_doc):
            if not self.log_test:
                return
            if non_sle_entries:
                return 
            if not validate_sle_entries(new_doc):
                raise InvalidStockEntries("Invalid Stock Entries for {0}, Aborting".format(new_doc.name))
            try:
                if not validate_sle_entries(frappe.get_doc("Stock Entry", "MAPL/VN/STE/2018/000045")):
                    raise InvalidStockEntries("Invalid Stock Entries for Problematic Stock Entry")
            except frappe.DoesNotExistError:
                pass
        
        def update_serial_no(error):
            if isinstance(error, SerialNoNotExistsError):
                error_split = str(error).split(" ")
                for element in error_split:
                    try:                                    
                        serial_no = frappe.get_doc("Serial No", element)
                    except frappe.DoesNotExistError:
                        continue
                    if serial_no and not serial_no.is_new():
                        serial_no.update_serial_no_reference()
                        serial_no.save()
                        break

        def do_queued(do_later):
            for idx, d in enumerate(do_later):
                log_info(logging, 'Retrying Doctype {0} with Name {1}'.format(d.doctype, d.name))
                d.posting_time = "23:55"
                retry = 0
                while True:
                    try:
                        save_point('QUEUED_IMPORT')
                        self.import_documents_having_childtables(d.doctype, old_doc_dict=d, before_insert=before_inserting, suppress_msg=True, \
                                        in_batches=False, reset_batch=False, auto_commit=False, after_insert=after_inserting, overwrite=overwrite)
                        retry = 0
                        release_savepoint('QUEUED_IMPORT')
                        break
                    except (SerialNoExistsInFutureTransaction, SerialNoWarehouseError, SerialNoNotExistsError) as e:
                        # Retry 15 Times with date + 1, Lots of Errors while using ERPNext for first 2 Years
                        rollback_to_savepoint('QUEUED_IMPORT')
                        if retry == 0:
                            update_serial_no(e)
                        retry = retry + 1
                        d.posting_date = add_to_date(getdate(d.posting_date),days=1)
                        log_info(logging, 'Retrying with +1 Date, Doctype {0} with Name {1}, new Date {2}'.format(d.doctype, d.name, d.posting_date))                    
                        if retry > 15:
                            retry = 0
                            raise            

        if not entries or len(entries)<=0:
            return

        total_list_length = len(entries)
        #Initialize Progress Bar
        printProgressBar('Transactions', 0, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50)
        do_later = []
        for idx, s in enumerate(entries):
            #Update Progress Bar                                    
            printProgressBar('Transactions', idx + 1, total_list_length, prefix = 'Progress:', suffix = 'Complete', length = 50, supplement_msg=s.get('posting_date') or "")
            s = frappe._dict(s) 
            try:
                save_point('DOC_IMPORT')
                self.import_documents_having_childtables(s.doctype, old_doc_dict=s, before_insert=before_inserting, suppress_msg=True, \
                                        in_batches=False, reset_batch=False, auto_commit=False, after_insert=after_inserting, overwrite=overwrite)
                release_savepoint('DOC_IMPORT')
            except (SerialNoNotExistsError, SerialNoWarehouseError) as n:
                log_info(logging, n, s)                
                do_later.append(s)
                rollback_to_savepoint('DOC_IMPORT')
            except NegativeStockError as n:
                #Repost & Retry
                log_info(logging, n, s)
                rollback_to_savepoint('DOC_IMPORT')
                self.repost(s, n)
                self.import_documents_having_childtables(s.doctype, old_doc_dict=s, before_insert=before_inserting, suppress_msg=True, \
                                        in_batches=False, reset_batch=False, auto_commit=False, after_insert=after_inserting, overwrite=overwrite)
        do_queued(do_later)
        self.commit()
    
    def repost(self, doc, error):
        warehouse = None
        for w in frappe.get_all("Warehouse", fields=['name']):
            if w['name'] in str(error):
                warehouse = w['name']
        for i in doc.get('items'):
            repost_entries(i['item_code'], warehouse)
        
    def import_payment_entries(self, from_date=None, to_date=None, overwrite=True):
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

        monkey_patch_payment_entry_temporarily()
        self.do_batch_import('Payment Entry', from_date=from_date, to_date=to_date, before_insert=before_inserting, overwrite=overwrite)

    def import_journal_entries(self, from_date=None, to_date=None, id=None, overwrite=True):
        def before_inserting(new_doc, old_doc):
            if old_doc['docstatus'] == 2:
                raise SkipRecordException('Skip Cancelled Record')
            new_doc.flags.ignore_validate = True
            for row in new_doc.accounts:
                row.reference_name = None
                row.reference_type = None
            new_doc.amended_from = None

        monkey_patch_journal_entry_temporarily()        
        self.do_batch_import('Journal Entry', from_date=from_date, to_date=to_date, before_insert=before_inserting, overwrite=overwrite)

    def import_period_closing_vouchers(self):
        self.import_documents_having_childtables('Period Closing Voucher', order_by='transaction_date')

    def update_naming_series(self):
        self.update_naming_series_transactions()
        self.update_naming_series_entities()

    def update_naming_series_transactions(self):
        docs = [
            "Sales Invoice",
            "Purchase Invoice",
            "Stock Entry",
            "Payment Entry",
            "Journal Entry",
            "Salary Slip"            
        ]
        for d in docs:
            series_list = self.get_transactions_series_list(d)
            for s in series_list:
                self.update_series(s.series_key, s.series_value)
        self.commit()

    def update_naming_series_entities(self):
        docs = [
            "Customer",
            "Supplier",
            "Employee"
        ]
        for d in docs:
            series_list = self.get_entities_series_list(d)
            for s in series_list:
                if (s.get('series_key') and s.series_key != ""):
                    self.update_series(s.series_key, s.series_value)
        self.commit()

    def get_transactions_series_list(self, doctype):
        query = """
                select  distinct substring(name, 1, length(name)-length(substring_index(name,'/',-1))) as series_key, 
                        max(substring_index(name,'/',-1)) as series_value from `tab{0}` 
                        group by substring(name, 1, length(name)-length(substring_index(name,'/',-1)))
                """
        return frappe.db.sql(query.format(doctype), as_dict=1)

    def get_entities_series_list(self, doc):
        query = """
                select  distinct substring(name, 1, length(name)-length(substring_index(name,'-',-1))) as series_key,
                        max(substring_index(name,'-',-1)) as series_value from `tab{0}`
                        group by substring(name, 1, length(name)-length(substring_index(name,'-',-1)))        
                """
        return frappe.db.sql(query.format(doc), as_dict=1)

    def update_series(self, key, value):
        check = frappe.db.sql("select * from `tabSeries` where name='{0}'".format(key), as_list=1)
        if check and len(check) > 0:
            frappe.db.sql("update `tabSeries` set current = {0} where name = '{1}'".format(value, key))
        else:
            frappe.db.sql("insert into `tabSeries` (current, name) values ({0},'{1}')".format(value, key))

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

            if new_doc.get('gstin') and len(new_doc.get('gstin')) > 15:
                setattr(new_doc, 'gstin', new_doc.get('gstin')[:15])                

            new_doc.flags.ignore_validate = True
            if new_doc.is_new():
                new_doc.append('links', dict(link_doctype=doctype, link_name=old_doc_dict.name))

            set_state_code(new_doc, save=False)

        def after_insert(new_doc, old_doc): 
            if new_doc.get('gstin'):
                gst_category = frappe.db.get_value(doctype, old_doc_dict.name, 'gst_category')
                if not gst_category or gst_category != 'Registered Regular':
                    frappe.db.set_value(doctype, old_doc_dict.name, "gst_category", "Registered Regular")
        
        if (not old_doc_dict.addresses):
            address_filters = [
                ["Dynamic Link", "link_doctype", "=", doctype],
                ["Dynamic Link", "link_name", "=", old_doc_dict.name],
                ["Dynamic Link", "parenttype", "=", "Address"],
            ]
            old_doc_dict.addresses = get_documents_without_childtables(self.remoteDBClient, 'Address', filters=address_filters)
            if not old_doc_dict.addresses or len(old_doc_dict.addresses) <= 0:
                return

        self.import_documents_having_childtables('Address', before_insert=before_insert, doc_list=old_doc_dict.addresses, \
                        after_insert=after_insert, overwrite=True, suppress_msg=True, fetch_with_children=False, in_batches=False, reset_batch=False)
    
    def create_contact(self, old_doc, new_doc_name):
        contact_nos = self.get_contact_nos(old_doc)
        if not contact_nos:
            return

        contact_nos = contact_nos.split(',')
        fn, mn, ln = split_name(old_doc.customer_name)        

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

    def do_batch_import(self, doctype, from_date=None, to_date=None, before_insert=None, after_insert=None, overwrite=True):
        batchdata = FetchData(self.remoteDBClient, self.parent_module, day_interval=5)
        batchdata.init_transactional_entries(doctype, from_date=from_date, to_date=to_date)
        entries = []
        while batchdata.has_more_records():
            entries = batchdata.get_next_batch()
            if not entries or len(entries)<=0:
                break
            #--DEBUG--print ("Testing", len(entries))        
            self.import_documents_having_childtables(doctype, before_insert=before_insert, doc_list=entries, reset_batch=False, overwrite=overwrite) 
        self.commit()

    def import_draft_documents(self, document_type=None, id=None):
        if id and not document_type:
            return
        elif id and document_type:
            doc = get_documents_with_childtables(self.remoteDBClient, self.parent_module, document_type, 
                                        filters = json.dumps([[document_type, "docstatus","=","0"],[document_type, "name","=",id]]), 
                                        page_length=100, order_by="name")
            
            self.import_transactions(doc, non_sle_entries=True)
            return
        documents = ["Sales Invoice", "Purchase Invoice", "Delivery Note"]        
        for d in documents:
            d_list = get_documents_with_childtables(self.remoteDBClient, self.parent_module, d, 
                                        filters = json.dumps([[d, "docstatus","=","0"]]), page_length=100, order_by="name")
            
            self.import_transactions(d_list, non_sle_entries=True)

    def remove_child_rows(self,new_doc, child_table):
        if (new_doc.get(child_table) and not new_doc.is_new()): #Child Not Empty  and new_doc.docstatus == 0
            child_doctype = new_doc.get(child_table)[0].doctype
            remove_rows = []
            for row in new_doc.get(child_table):
                remove_rows.append(row)
            for row in remove_rows:            
                new_doc.remove(row)
            #flag = new_doc.flags.ignore_mandatory
            #new_doc.flags.ignore_mandatory = True
            #new_doc.save()
            #new_doc.flags.ignore_mandatory = flag
    
    def copy_attr(self, old_doc, new_doc, copy_child_table=False, doctype_different=False, child_table_name_map=None, overwrite=False):
        for k in old_doc.keys():
            #--DEBUG-- print ("Key:",k)            
            if isinstance(old_doc[k], dict) or isinstance(old_doc[k], list):
                if copy_child_table:
                    child_table_field_name = k 
                    if child_table_name_map:
                        child_table_field_name = child_table_name_map.get(k)
                    self.remove_child_rows(new_doc, child_table_field_name)
                    #--DEBUG-- print ("Copying:",k,"  To:",child_table_field_name)
                    self.copy_child_table_attr(old_doc, new_doc, old_child_fieldname=k, new_child_fieldname=child_table_field_name)
                continue
            if (k == 'modified'):
                continue
            if doctype_different and k == 'doctype':
                continue
            if overwrite and k in ('creation', 'owner'):
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
                    #--DEBUG-- print ("Setting:",k," With:",i[k])
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
            if not overwrite and (self.overwrite_if_modified_after and getdate(old_doc_dict.modified)>getdate(self.overwrite_if_modified_after)):
                overwrite = True
            if not frappe.db.exists(doctype, doc.name):
                new_doc = frappe.new_doc(doctype)
            elif overwrite:
                new_doc = frappe.get_doc(doctype, doc.name)
            if not new_doc:
                log_info(logging, 'Skipping Doctype {0} with Name {1}, Already Exists and Overwrite Not Allowed'.format(doctype, doc.name))
                return
            is_doc_new = new_doc.is_new()                
            if not is_doc_new and new_doc.docstatus != 0: # Dont Touch Submitted Documents
                log_info(logging, 'Skipping Doctype {0} with Name {1}, Already Submitted'.format(doctype, doc.name))
                return
            log_info(logging, 'Importing Doctype {0} with Name {1}'.format(doctype, doc.name))
            if overwrite and not is_doc_new:
                frappe.flags.in_import = True
            self.copy_attr(doc, new_doc, copy_child_table=copy_child_table, doctype_different=different_doctype, \
                            child_table_name_map=child_table_name_map, overwrite=overwrite)
            if before_insert:
                try:
                    before_insert(new_doc, doc)
                except SkipRecordException:
                    return
            if is_doc_new:
                if get_new_name:
                    new_name = get_new_name(doc)
                self.insert_doc(new_doc, new_name=doc.name, continue_on_error=continue_on_error, submit=submit)
            elif overwrite:
                self.save_doc(new_doc)
            if (not overwrite and not is_doc_new):
                return
            if after_insert:
                after_insert(new_doc, doc)

    def import_documents_having_childtables(self, doctype, new_doctype=None, id=None, old_doc_dict=None, overwrite=False, \
                        before_insert=None, submit=False, child_table_name_map=None, after_insert=None, copy_child_table=True, \
                        fetch_with_children=True, doc_list=None, fetch_filters=None, get_new_name=None, suppress_msg=False, \
                        in_batches=True, order_by=None, reset_batch=True, continue_on_error=False, auto_commit=True):

        if reset_batch and in_batches and id == None:
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
                        get_new_name=get_new_name, suppress_msg=suppress_msg, in_batches=in_batches, continue_on_error=continue_on_error, auto_commit=auto_commit)

            if not (doc_list == None and old_doc_dict == None and id == None):
                break

            if hasattr(self,'batchdata') and not (in_batches and self.batchdata.has_more_records()):
                break        

    def start_import_process(self, doctype, doc_list, new_doctype=None, overwrite=False, \
                        before_insert=None, submit=False, child_table_name_map=None, after_insert=None, copy_child_table=True, \
                        get_new_name=None, suppress_msg=False, in_batches=True, continue_on_error=False, auto_commit=True):

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
            if i % self.COMMIT_DELAY == 0 and auto_commit:
                self.commit()
        if auto_commit:
            self.commit()        

    def fetch_data(self, doctype, id=None, doc_list=None, old_doc_dict=None, filters=None, \
                            order_by=None, fetch_with_children=True, in_batches=True):

        if in_batches and id == None and old_doc_dict == None and doc_list == None:                  
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
            return get_documents_without_childtables(self.remoteDBClient, doctype, client_db_api_path=self.parent_module, filters=filters, \
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
                log_info(logging, 'Error Creating {0} Name:{1}, Continuing...'.format(new_doc.doctype, new_doc.name))
            
    def save_doc(self, new_doc, continue_on_error=False):
        """
        No Submit Option, As save_doc is called if overwrite is enabled, and Submitted Documents are not Overwritten
        """
        new_doc.ignore_validate_hook = True
        try:
            new_doc.save(ignore_permissions=True)
        except Exception as e:
            if not continue_on_error:
                raise 
            else:
                log_info(logging, 'Error Updating {0} Name:{1}, Continuing...'.format(new_doc.doctype, new_doc.name))

    def commit(self):
        if not self.log_test:
            frappe.db.commit()

    def import_biometric_details(self, dates_map=None):
        try:
            if not self.remoteDBClient.get_doc("Biometric Machine"):
                return
        except Exception:
            return

        if not frappe.db.table_exists("Biometric Machine"):
            return
        
        filters=None
        if dates_map:
            from_date = dates_map[0][0]
            to_date = dates_map[-1][1]
            filters = json.dumps(build_date_time_filter('Biometric Attendance', from_date=from_date, to_date=to_date, \
                        from_column_name="timestamp", to_column_name="timestamp"))
        self.import_documents_having_childtables('Biometric Users')
        self.import_documents_having_childtables('Branch Settings')
        self.import_documents_having_childtables('Biometric Machine')
        self.import_documents_having_childtables('Biometric Attendance', fetch_filters=filters)
        
