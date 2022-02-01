import frappe
import json
import datetime
from frappe.utils import cint, getdate, today
from six import string_types

def make_jv_for_connected_accounts(doc, method):
	def assign_record(jv_record, connected_account, debit=0, credit=0):
		jv_record.account = connected_account.get("account")
		jv_record.party_type = connected_account.get("party_type")
		jv_record.party = connected_account.get("party")
		jv_record.party_name = connected_account.get("party_name")
		jv_record.debit = debit
		jv_record.credit = credit
		jv_record.debit_in_account_currency = debit
		jv_record.credit_in_account_currency = credit

	from erpnext.accounts.doctype.journal_entry.journal_entry import get_party_account_and_balance
	if doc.get('ignore_validate_hook'):
		return	
	if doc.doctype not in ("Sales Invoice", "Purchase Invoice"):
		return
	root_party_type = "Customer" if doc.doctype == "Sales Invoice" else "Supplier"
	connected_accounts = frappe.get_doc(root_party_type, doc.get("customer") or doc.get("supplier")).get("connected_accounts_list")
	if not connected_accounts:
		return
	for ca in connected_accounts:
		jv = frappe.new_doc("Journal Entry")
		jv.posting_date = doc.posting_date
		ac1 = jv.append("accounts")
		assign_record(ac1, ca, 
				debit=doc.grand_total if doc.doctype=="Sales Invoice" else 0,
				credit=doc.grand_total if doc.doctype=="Purchase Invoice" else 0)
		ac2 = jv.append("accounts")
		account = get_party_account_and_balance(doc.company, root_party_type, doc.get("customer") or doc.get("supplier"))
		assign_record(ac2, {
							"account":account.get("account"),
							"party_type":root_party_type,
							"party":doc.get("customer") or doc.get("supplier"),
							"party_name":doc.get("customer_name") or doc.get("supplier_name")
							}, 
				credit=doc.grand_total if doc.doctype=="Sales Invoice" else 0,
				debit=doc.grand_total if doc.doctype=="Purchase Invoice" else 0)
		jv.user_remark = "Automated Entry \n\n"+(ca.get("default_message") or "")+"\nAgainst "+doc.doctype+" No: "+doc.name
		jv.save()
		jv.submit()

def cancel_jv_for_connected_accounts(doc, method):
	query = """
				select name from `tabJournal Entry` where docstatus=1 and user_remark like 'Automated Entry %Against {0} No: {1}%' limit 1
			"""
	try:
		old_doc_name = doc.name[:doc.name.find('-CANC-')]
		name = frappe.db.sql(query.format(doc.doctype, old_doc_name))[0][0]
		frappe.get_doc("Journal Entry", name).cancel()
	except Exception:
		pass

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
def validate_input_serial(args,rows,is_vehicle=1, is_electric_vehicle=0):
	if isinstance(args, string_types):
		args = json.loads(args)

	serial_keys = args.keys()

	int_rows = cint(rows)
	rows = str(int_rows)
	is_vehicle = cint(is_vehicle)
	is_electric_vehicle = cint(is_electric_vehicle)

	for i in range(1, int_rows):
		if is_vehicle==1:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Chassis No At Row "+rows)

			if "color_"+rows not in serial_keys:
				frappe.throw("Check Color At Row "+rows)

			if is_electric_vehicle == 0:
				if "engine_no_"+rows not in serial_keys:
					frappe.throw("Check Engine No At Row "+rows)

				if "key_no_"+rows not in serial_keys:
					frappe.throw("Check Key No At Row "+rows)

		if is_vehicle==0:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Serial No At Row "+rows)

	return True

@frappe.whitelist()
def get_money_in_words(number):
	from frappe.utils import money_in_words
	return money_in_words(number)

@frappe.whitelist()
def get_average_purchase_rate_for_item(item,as_value=0):
	query = """
				select
				   round(
				     avg(sle.valuation_rate)*
				     (1+((select max(tax_rate) from `tabItem Tax Template Detail` detail where detail.parent = it.item_tax_template))/100)
				   ,2) as avg_rate
				from
				 `tabStock Ledger Entry` sle,
				 `tabItem Tax` it
				where
				 it.parent = sle.item_code
				 and it.valid_from <= cast(now() as Date)
				 and sle.item_code = %s
				 and sle.is_cancelled = 0
				order by
				  it.valid_from desc
				limit 1
		"""
	if not as_value:
		return frappe.db.sql(query, item)
	else:
		ar = frappe.db.sql(query, item, as_dict=1)[0].avg_rate
		if ar:
			return ar
	return 0

def check_average_purchase(doc):
	for i in doc.get("items"):
		ar = get_average_purchase_rate_for_item(i.item_code, as_value=1)
		if i.net_rate < ar:
			return 0
	return 1


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