import frappe
import json
import datetime
from frappe.utils import cint 

@frappe.whitelist()
def make_document_editable(doctype, doc_name):
	doc = frappe.get_doc(doctype, doc_name)
	if doc.docstatus != 2:
		frappe.throw("Document Not yet Cancelled or Still in Draft Mode, Cannot make in Editable")
		return

	doc.docstatus = 0
	doc.cancel_reason = None
	for d in doc.get_all_children():
		d.docstatus = 0
		d.db_update()

	doc.db_update()
	frappe.db.commit()

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

			if "color_"+rows not in serial_keys:
				frappe.throw("Check Color At Row "+rows)

		if is_vehicle==0:
			if "chassis_no_"+rows not in serial_keys:
				frappe.throw("Check Serial No At Row "+rows)

	return True

def purchase_receipt_on_submit(doc,method):
	validate_hsn_code(doc, method)
	for i in doc.items:
		if cint(i.is_vehicle):
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")
			color = i.color.split("\n")

			index = 0
			for serials in chassis_nos:
				serial_doc = frappe.get_doc("Serial No",serials)
				serial_doc.is_vehicle = 1
				serial_doc.chassis_no = serials
				serial_doc.engine_no = engine_nos[index]
				serial_doc.key_no = key_nos[index]
				serial_doc.color = color[index]
				serial_doc.year_of_manufacture = i.year_of_manufacture
				serial_doc.save()
				index = index+1

def purchase_receipt_validate(doc, method):
	for i in doc.items:
		if cint(i.is_vehicle):
			chassis_nos = i.serial_no.split("\n")
			engine_nos = i.engine_nos.split("\n")
			key_nos = i.key_nos.split("\n")
			color = i.color.split("\n")

			throw_error = False
			if len(chassis_nos) != len(engine_nos):
				throw_error = True
			if not throw_error and len(engine_nos) != len(key_nos):
				throw_error = True
			if not throw_error and len(key_nos) != len(color):
				throw_error = True

			if throw_error:
				frappe.throw("Check Entered Serial Nos Values")


def purchase_receipt_before_submit(doc, method):
	purchase_receipt_serial_no_validate_before_submit(doc, method)

def purchase_receipt_serial_no_validate_before_submit(doc, method):
	for i in doc.items:
		if not i.serial_no:
			continue

		snos = i.serial_no.strip(' \n').split('\n')
		snos = "|".join(snos)

		rows = frappe.db.sql("""select name from `tabSerial No` where name regexp '%s' and warehouse is not null and warehouse <> ''""" % snos)

		for r in rows:
			frappe.throw("""Atleast One of The Serial No(s) for Item {0} Already Exists. Please Verify""".format(i.item_code))



def validate_hsn_code(doc, method):
	for i in doc.items:
		if not i.gst_hsn_code:
			frappe.throw("HSN Code not found for {0}".format(i.item_code))



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
  	(`OPENING STOCK`+`IN QTY`-`OUT QTY`) AS `CLOSING STOCK`,`UNCONFIRMED`, `UNDELIVERED`,`DEFECTIVE`,`OPEN ORDER` FROM (
		
    SELECT OUTSTK.NAME, 
    
    IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE < %(date)s),0) AS `OPENING STOCK`,

	IFNULL((SELECT SUM(ACTUAL_QTY) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND ACTUAL_QTY > 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `IN QTY`,
		
    IFNULL((SELECT SUM(ABS(ACTUAL_QTY)) FROM `tabStock Ledger Entry` Stk WHERE
		ITEM_CODE=%(item_code)s AND ACTUAL_QTY < 0 AND WAREHOUSE=OUTSTK.NAME AND POSTING_DATE=%(date)s),0) AS `OUT QTY`,
	  
    IFNULL((SELECT SUM(INV_ITEM.QTY) FROM `tabSales Invoice` INV, `tabSales Invoice Item` INV_ITEM WHERE INV_ITEM.WAREHOUSE=OUTSTK.NAME AND
        INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS<1 AND INV_ITEM.ITEM_CODE=%(item_code)s AND INV.POSTING_DATE<=%(date)s),0) AS `UNCONFIRMED`,

    IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Invoice` INV, 
		`tabSales Invoice Item` INV_ITEM WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND INV_ITEM.WAREHOUSE=OUTSTK.NAME AND
		INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV.UPDATE_STOCK=0 AND INV_ITEM.ITEM_CODE=%(item_code)s AND INV.POSTING_DATE<=%(date)s),0) AS `UNDELIVERED`,

    IFNULL((SELECT SUM(INV_ITEM.QTY-INV_ITEM.DELIVERED_QTY) FROM `tabSales Order` INV, 
		`tabSales Order Item` INV_ITEM WHERE INV_ITEM.PARENT=INV.NAME AND INV.DOCSTATUS=1 AND INV_ITEM.WAREHOUSE=OUTSTK.NAME AND
		INV_ITEM.DELIVERED_QTY<>INV_ITEM.QTY AND INV_ITEM.ITEM_CODE=%(item_code)s AND INV.TRANSACTION_DATE<=%(date)s),0) AS `OPEN ORDER`,
		
    IFNULL((SELECT COUNT(*) FROM `tabStock Problem` PROB WHERE PROB.item=%(item_code)s AND PROB.WAREHOUSE=OUTSTK.NAME AND PROB.STATUS='Open'),0) AS `DEFECTIVE`
		
    FROM `tabWarehouse` OUTSTK 
		) DER GROUP BY NAME""", {
			'date': date if date else datetime.date.today().strftime('%Y-%m-%d'),
			'item_code': item_code }, as_dict=1)
