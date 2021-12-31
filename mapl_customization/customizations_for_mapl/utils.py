import frappe
import json
import datetime
from frappe.utils import cint, getdate, today
from six import string_types


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
			from `tabGL Entry` where party_type = %s and company=%s
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
			        ITEM_CODE=%(item_code)s AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE < %(date)s),0) AS `OPENING STOCK`,

			      IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
			        ITEM_CODE=%(item_code)s AND ACTUAL_QTY > 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `IN QTY`,

			      IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
			        ITEM_CODE=%(item_code)s AND ACTUAL_QTY < 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `OUT QTY`,

			      IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabSales Invoice` INV, `tabSales Invoice Item` INV_ITEM WHERE
			        INV_ITEM.WAREHOUSE=OUTSTK.NAME AND INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=%(item_code)s
			        AND INV.POSTING_DATE<=%(date)s),0) AS `UNCONFIRMED`,

			      IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Invoice` INV,`tabSales Invoice Item` INV_ITEM
			        WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AN INV_ITEM.WAREHOUSE=OUTSTK.NAME
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
			""".format(getdate(from_date),getdate(to_date))
	return frappe.db.sql(query, as_dict=1)

@frappe.whitelist()
def get_non_stock_sales_purchase_count(from_date, to_date):
	query = """
				select count(distinct voucher_no,voucher_type) from `tabGL Entry` where voucher_type in ('Sales Invoice', 'Purchase Invoice') 
				and voucher_no not in (select distinct voucher_no from `tabStock Ledger Entry` 
				where voucher_type in ('Sales Invoice', 'Purchase Invoice')) and posting_date between '{0}' and '{1}'
			""".format(getdate(from_date),getdate(to_date))
	return frappe.db.sql(query, as_list=1)	