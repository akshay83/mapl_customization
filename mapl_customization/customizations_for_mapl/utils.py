import frappe
import json
import datetime
from frappe.utils import cint, getdate, today
from six import string_types


@frappe.whitelist()
def create_loan_disbursal_jv(doc):
	doc = json.loads(doc)
	doc = frappe._dict(doc)

	jv = frappe.new_doc("Journal Entry")
	jv.posting_date = doc.posting_date
	jv.company = doc.company
	employee_account = jv.append("accounts")
	employee_account.party_type = doc.applicant_type
	employee_account.party = doc.applicant
	employee_account.account = doc.loan_account
	employee_account.debit = (doc.loan_amount-doc.disbursed_amount)
	employee_account.debit_in_account_currency = (doc.loan_amount-doc.disbursed_amount)
	employee_account.reference_type = 'Loan'
	employee_account.reference_name = doc.name
	employee_account.party_name = doc.applicant_name
	payment_account = jv.append("accounts")
	payment_account.account = doc.payment_account
	payment_account.credit = (doc.loan_amount-doc.disbursed_amount)
	payment_account.credit_in_account_currency = (doc.loan_amount-doc.disbursed_amount)
	jv.user_remark = "Loan Against Loan No: " + doc.name
	return jv

def update_state_code(doctype='Customer', verbose=True):
	address_filters = [
                ["Dynamic Link", "link_doctype", "=", doctype],
                ["Dynamic Link", "parenttype", "=", "Address"]
	]
	address_list = frappe.get_list("Address", filters=address_filters)
	for a in address_list:
		doc = frappe.get_doc('Address', a.name)
		if verbose:
			print ('Checking:',a.name,'  State Code:', doc.gst_state_number)
		set_state_code(doc, verbose=verbose)
	frappe.db.commit()

def set_state_code(address_doc, save=True, verbose=False):
	from erpnext.regional.india import state_numbers, states
	if not address_doc.get('gst_state_number') or address_doc.get('gst_state_number') == '0':
		if not address_doc.get('gst_state') or address_doc.get('gst_state') == '':
			if (not address_doc.get('state')) or (address_doc.state == ''):
				address_doc.state = 'Madhya Pradesh' #Default State
			address_doc.gst_state = address_doc.state if address_doc.state.lower() in [x.lower() for x in states] else None                    
			if not address_doc.get('gst_state') or address_doc.get('gst_state') == '':
				address_doc.gst_state = 'Madhya Pradesh' #Default State
		try:
			address_doc.gst_state_number = state_numbers[address_doc.gst_state]
			if verbose:
				print ('Updated State Code For:', address_doc.name)
			if save:
				address_doc.flags.ignore_validate = True
				address_doc.save(ignore_permissions=True)
		except Exception as e:
				print ('Could Not Find GST State for:', address_doc.name)
				if verbose:
					print (str(e))

@frappe.whitelist()
def get_party_name(party, party_type):
	doc = frappe.get_doc(party_type, party)
	if (party_type == "Customer"):
		return doc.customer_name
	elif (party_type == "Supplier"):
		return doc.supplier_name
	elif (party_type == "Employee"):
		return doc.employee_name

@frappe.whitelist()
def get_primary_billing_address(party, party_type):
	from frappe.contacts.doctype.address.address import get_default_address
	return get_default_address(party_type.lower(), party)

@frappe.whitelist()
def fetch_address_details_payments_receipts(party_address):
	from frappe.contacts.doctype.address.address import get_address_display
	return get_address_display(party_address)

@frappe.whitelist()
def get_money_in_words(number):
	from frappe.utils import money_in_words
	return money_in_words(number)

@frappe.whitelist()
def get_average_purchase_rate_for_item(item,with_tax=True,as_value=0):
	query = """
				select
				   round(
				     avg(sle.valuation_rate){0}
				   ,2) as avg_rate
				from
				 `tabStock Ledger Entry` sle,
				 `tabItem Tax` it
				where
				 it.parent = sle.item_code
				 and (it.valid_from <= cast(now() as Date) or it.valid_from is null)
				 and sle.item_code = %s
				 and sle.is_cancelled = 0
				order by
				  it.valid_from desc
				limit 1
		""".format("*(1+((select max(tax_rate) from `tabItem Tax Template Detail` detail where detail.parent = it.item_tax_template))/100)" if with_tax else "")
	if not as_value:
		return frappe.db.sql(query, item)
	else:
		ar = frappe.db.sql(query, item, as_dict=1)[0].avg_rate
		if ar:
			return ar
	return 0

def check_average_purchase(doc):
	"""Returns 1 if CHECK is OK else 0"""
	total_sale_rate = 0
	total_purchase_rate = 0
	cumulative_check = False
	if cint(frappe.db.get_single_value("Accounts Settings", "check_rate_cumulatively")):
		cumulative_check = True
	threshold = frappe.db.get_single_value("Accounts Settings", "rate_check_threshold")
	for i in doc.get("items"):
		ar = get_average_purchase_rate_for_item(i.item_code, with_tax=False, as_value=1)
		if not cumulative_check:
			#--DEBUG--print ("Purchase:",(ar-(ar*threshold/100))," Sale:",i.net_rate)
			if i.net_rate < (ar-(ar*threshold/100)):
				return 0
		else:
			total_sale_rate += i.net_rate
			total_purchase_rate += ar
	if cumulative_check:
		if total_sale_rate < (total_purchase_rate-(total_purchase_rate*threshold/100)):
			return 0
	return 1	

def check_for_workflow_approval(doc):
	"""
	Return 1: If everything is Ok
	Return 2: If Approval Required From Sales Manager (Rate < Purchase Rate && Not Delayed Payment)
	Return 3: If Approval Required From System Manager (Rate is Ok && Delayed Payment)
	"""
	if (doc.doctype != "Sales Invoice"):
		return
	from mapl_customization.customizations_for_mapl.sales_invoice_validation import negative_stock_validation
	#--DEBUG--print (check_average_purchase(doc))
	#--DEBUG--print (negative_stock_validation(doc, None, show_message=False))
	avg_pur_rate_check = 1
	negative_check = 1
	if cint(frappe.db.get_single_value("Accounts Settings", "check_purchase_rate_against_sale_rate")) and not check_average_purchase(doc):
		avg_pur_rate_check = 0
	if cint(frappe.db.get_single_value("Accounts Settings", "check_negative_stock")) and not negative_stock_validation(doc, None, show_message=False):
		negative_check = 0
	if not approval_required_for_delayed_payment(doc) and (cint(avg_pur_rate_check) and cint(negative_check)):
		return 1
	elif approval_required_for_delayed_payment(doc) and (cint(avg_pur_rate_check) and cint(negative_check)):
		return 3
	elif not approval_required_for_delayed_payment(doc) and (not cint(avg_pur_rate_check) or not cint(negative_check)):
		return 2
	return 1

def approval_required_for_delayed_payment(doc):
	if cint(doc.delayed_payment):
		if doc.delayed_payment_reason and doc.delayed_payment_reason.lower() in ["other", "reference"]:
			return 1
		else:
			return 0
		return 1
	return 0

@frappe.whitelist()
def get_party_balance(party, party_type, company):
	outstanding_amount = frappe.db.sql("""select sum(debit) - sum(credit)
			from `tabGL Entry` where party_type = %s and company=%s and is_cancelled=0
			and party = %s""", (party_type, company, party))
	return outstanding_amount

@frappe.whitelist()
def get_effective_stock_at_all_warehouse(item_code, date=None):
	query = """
			SELECT
			    NAME,
			    `OPENING STOCK`,
			    `IN QTY`,
			    `OUT QTY`,
			    (`OPENING STOCK`+`IN QTY`-`OUT QTY`) AS `CLOSING STOCK`,
			    `UNCONFIRMED`,
			    `UNDELIVERED`,
			    `DEFECTIVE`,
			    `OPEN ORDER`
			FROM (
			    SELECT OUTSTK.NAME,
			      IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			        ITEM_CODE=%(item_code)s AND IS_CANCELLED=0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE < %(date)s),0) AS `OPENING STOCK`,

			      IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			        ITEM_CODE=%(item_code)s AND IS_CANCELLED=0 AND ACTUAL_QTY > 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `IN QTY`,

			      IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
			        ITEM_CODE=%(item_code)s AND IS_CANCELLED=0 AND ACTUAL_QTY < 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `OUT QTY`,

			      IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabSales Invoice` INV, `tabSales Invoice Item` INV_ITEM WHERE
			        INV_ITEM.WAREHOUSE=OUTSTK.NAME AND INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=%(item_code)s
			        AND INV.POSTING_DATE<=%(date)s),0) AS `UNCONFIRMED`,

			      IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Invoice` INV,`tabSales Invoice Item` INV_ITEM
			        WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND INV_ITEM.WAREHOUSE=OUTSTK.NAME
			        AND INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV.UPDATE_STOCK=0 AND INV_ITEM.ITEM_CODE=%(item_code)s
			        AND INV.POSTING_DATE<=%(date)s),0) AS `UNDELIVERED`,

			      IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Order` INV, `tabSales Order Item` INV_ITEM
			        WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND INV_ITEM.WAREHOUSE=OUTSTK.NAME
			        AND INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV_ITEM.ITEM_CODE=%(item_code)s
			        AND INV.TRANSACTION_DATE<=%(date)s),0) AS `OPEN ORDER`,

			      IFNULL((SELECT COUNT(*) FROM `tabStock Problem` PROB WHERE PROB.item=%(item_code)s AND PROB.WAREHOUSE=OUTSTK.NAME
			        AND PROB.STATUS='Open'),0) AS `DEFECTIVE`

			      FROM `tabWarehouse` OUTSTK
			    ) DER GROUP BY NAME
		"""

	return frappe.db.sql(query, {
			'date': date if date else datetime.date.today().strftime('%Y-%m-%d'),
			'item_code': item_code },
			as_dict=1)

@frappe.whitelist()
def get_non_stock_sales_purchase(from_date, to_date):
	query = """
				select distinct voucher_no,voucher_type from `tabGL Entry` where voucher_type in ('Sales Invoice', 'Purchase Invoice') 
				and voucher_no not in (select distinct voucher_no from `tabStock Ledger Entry` 
				where voucher_type in ('Sales Invoice', 'Purchase Invoice')) and posting_date between '{0}' and '{1}'
			"""
	try:
		if frappe.db.has_column("GL Entry", "is_cancelled"):
			query = query + " and is_cancelled=0"
	except Exception:
		pass
	return frappe.db.sql(query.format(getdate(from_date),getdate(to_date)), as_dict=1)

@frappe.whitelist()
def get_non_stock_sales_purchase_count(from_date, to_date):
	query = """
				select count(distinct voucher_no,voucher_type) from `tabGL Entry` where voucher_type in ('Sales Invoice', 'Purchase Invoice') 
				and voucher_no not in (select distinct voucher_no from `tabStock Ledger Entry` 
				where voucher_type in ('Sales Invoice', 'Purchase Invoice')) and posting_date between '{0}' and '{1}'
			"""
	try:
		if frappe.db.has_column("GL Entry", "is_cancelled"):
			query = query + " and is_cancelled=0"
	except Exception:
		pass
	return frappe.db.sql(query.format(getdate(from_date),getdate(to_date)), as_list=1)	