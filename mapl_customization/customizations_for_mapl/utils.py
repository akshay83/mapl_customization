import frappe
import json


@frappe.whitelist()
def get_party_name(party, party_type):
	doc = frappe.get_doc(party_type, party)
	if (party_type == "Customer"):
		return doc.customer_name
	else:
		return doc.supplier_name

@frappe.whitelist()
def get_primary_billing_address(party, party_type):
	party_address = frappe.db.get_value("Address", { 
			party_type.lower(): party, 
			"is_primary_address":1,
			"address_type":"Billing"
			}, "name")
	return party_address

@frappe.whitelist()
def fetch_address_details_payments_receipts(party_address):
	from erpnext.utilities.doctype.address.address import get_address_display
	return get_address_display(party_address)
	

@frappe.whitelist()
def validate_input_serial(args,rows,is_vehicle=1):
	if isinstance(args, basestring):
		args = json.loads(args)

	serial_keys = args.keys()

	int_rows = int(float(rows))
	rows = str(int_rows)
	is_vehicle = int(float(is_vehicle))

	for i in range(1, int_rows):
		if is_vehicle==1:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Chassis No At Row "+rows)

			if "engine_no_"+rows not in serial_keys:
				frappe.throw("Check Engine No At Row "+rows)

			if "key_no_"+rows not in serial_keys:
				frappe.throw("Check Key No At Row "+rows)

		if is_vehicle==0:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Serial No At Row "+rows)

	return True

def purchase_receipt_on_submit(doc,method):
	for i in doc.items:
		if i.is_vehicle == 1:
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")

			index = 0
			for serials in chassis_nos:
				serial_doc = frappe.get_doc("Serial No",serials)
				serial_doc.is_vehicle = 1
				serial_doc.chassis_no = serials
				serial_doc.engine_no = engine_nos[index]
				serial_doc.key_no = key_nos[index]
				serial_doc.save()
				index = index+1

def purchase_receipt_validate(doc, method):
	for i in doc.items:
		if i.is_vehicle == 1:
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")

			if len(chassis_nos) != len(engine_nos) != len(key_nos):
				frappe.throw("Check Entered Serial Nos Values")

def check_receipt_in_journal_entry(doc, method):
	if (doc.receipt_link or doc.payment_link):
		frappe.throw("Cannot Cancel/Delete - Linked With a Receipt/Payments");

@frappe.whitelist()
def get_party_balance(party, party_type, company):
	outstanding_amount = frappe.db.sql("""select sum(debit) - sum(credit)
			from `tabGL Entry` where party_type = %s and company=%s
			and party = %s""", (party_type, company, party))
	return outstanding_amount

@frappe.whitelist()
def get_current_stock_at_all_warehouse(item_code, date=None):
	return frappe.db.sql("""SELECT WAREHOUSE, `OPENING STOCK`+`IN QTY`-`OUT QTY` AS `CLOSING STOCK` FROM 
	  (SELECT OUTSTK.ITEM_CODE, OUTSTK.WAREHOUSE,
	    IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
	    ITEM_CODE=OUTSTK.ITEM_CODE AND POSTING_DATE < %(date)s AND WAREHOUSE=OUTSTK.WAREHOUSE),0) AS `OPENING STOCK`,
	    IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
	    ITEM_CODE=OUTSTK.ITEM_CODE AND ACTUAL_QTY > 0 AND POSTING_DATE>=%(date)s AND WAREHOUSE=OUTSTK.WAREHOUSE),0) AS `IN QTY`,
	    IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
	    ITEM_CODE=OUTSTK.ITEM_CODE AND ACTUAL_QTY < 0 AND POSTING_DATE<=%(date)s AND WAREHOUSE=OUTSTK.WAREHOUSE),0) AS `OUT QTY`
	    FROM `tabStock Ledger Entry` OUTSTK, `tabWarehouse` WARE WHERE WARE.NAME=OUTSTK.WAREHOUSE AND OUTSTK.ITEM_CODE=%(item_code)s
	  ) DER GROUP BY ITEM_CODE, WAREHOUSE""", 
		{ 	'date': date if date else 'CURDATE()',
			'item_code': item_code },as_dict=1)

@frappe.whitelist()
def get_effective_stock_at_all_warehouse(item_code, date=None):
	return frappe.db.sql("""SELECT NAME,`OPENING STOCK`,`IN QTY`, `OUT QTY`,
  	(`OPENING STOCK`+`IN QTY`-`OUT QTY`) AS `CLOSING STOCK`,`UNCONFIRMED`, `UNDELIVERED`,`DEFECTIVE` FROM (
		
    SELECT OUTSTK.NAME, 
    
    IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE < %(date)s),0) AS `OPENING STOCK`,

	IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND ACTUAL_QTY > 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE>=%(date)s),0) AS `IN QTY`,
		
    IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND ACTUAL_QTY < 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE<=%(date)s),0) AS `OUT QTY`,
	  
    IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabSales Invoice` INV, `tabSales Invoice Item` INV_ITEM WHERE 
        INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=%(item_code)s AND INV.POSTING_DATE<=%(date)s),0) AS `UNCONFIRMED`,

    IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Invoice` INV, 
		`tabSales Invoice Item` INV_ITEM WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND 
		INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV.UPDATE_STOCK=0 AND INV_ITEM.ITEM_CODE=%(item_code)s AND INV.POSTING_DATE<=%(date)s),0) AS `UNDELIVERED`,
		
    IFNULL((SELECT COUNT(*) FROM `tabStock Problem` PROB WHERE PROB.item=%(item_code)s AND PROB.STATUS='Open'),0) AS `DEFECTIVE`
		
    FROM `tabWarehouse` OUTSTK 
		) DER GROUP BY NAME""", {
			'date': date if date else 'CURDATE()',
			'item_code': item_code }, as_dict=1)
