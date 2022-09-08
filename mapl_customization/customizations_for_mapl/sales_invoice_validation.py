import frappe
import html
import json
from frappe.utils import cint, flt

def sales_invoice_validate(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	negative_stock_validation(doc, method)
	validate_hsn_code(doc, method)
	validate_stock_entry_serial_no(doc, method)
	validate_serial_no(doc, method)
	validate_gst_state(doc, method)
	validate_customer_balance(doc, method)

def sales_on_submit_validation(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	negative_stock_validation(doc, method, raise_error=True)
	vehicle_validation(doc, method)
	validate_hsn_code(doc, method, raise_error=True)
	taxes_and_charges_validation(doc, method)
	validate_grand_total(doc, method)
	
def validate_customer_balance(doc, method):
	def get_customer_invoice_total():
		filters = {
					"customer":doc.customer,
					"docstatus":('<',2)
		}
		if doc.name:
			filters.update({"name":('!=', doc.name)})
		invoices = frappe.get_all("Sales Invoice", filters = filters, fields=["grand_total"])
		total = 0
		for i in invoices:
			total = total + i.grand_total
		total = total + doc.grand_total
		return total

	def get_customer_credit_balance():
		filters = {
					"party":doc.customer,
					"party_type":"Customer",
					"voucher_type":("!=","Sales Invoice"),
					"is_cancelled":0
		}
		credits = frappe.get_all("GL Entry", filters = filters, fields=["credit", "debit"])
		total = 0
		for c in credits:
			total = total + c.credit - c.debit
		return total

	if not cint(frappe.db.get_single_value("Accounts Settings", "verify_party_balance")):
		return
	if (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
		return
	if cint(doc.delayed_payment) or cint(doc.is_finance):
		return
	balance = flt(get_customer_credit_balance())
	inv_total = flt(get_customer_invoice_total())
	if abs(balance)-abs(inv_total) < 0:
		frappe.throw("""Customer does not have Sufficient Balance. Please make sure that Payment has been Received and
					Payment Entry is Submitted or Select Delayed Payment Option.\n
					Current Customer Balance {0}, Required {1}""".format(balance, inv_total))

def validate_serial_no(doc, method):
	""" check if serial number is already used in other sales invoice """
	if (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()) or doc.docstatus == 2:
		return
	for item in doc.items:
		if not item.serial_no:
			continue
		#--DEBUG--print (item.serial_no)
		#--DEBUG--print (item.serial_no.split("\n"))
		for serial_no in item.serial_no.split("\n"):
			query = """
						select 
							max(if(qty>0,parent,null)) as parent,
							sum(if(qty>0,1,-1)) as rec_qty 
						from 
							`tabSales Invoice Item` 
						where 
							serial_no like '%{serial_no}%' 
							and docstatus <> 2 
							{docname} 
						having sum(rec_qty) > 0
					""".format(**{
						"serial_no": serial_no,
						"docname": "and parent <> '{0}'".format(doc.name) if doc.name else ""
					})
			#--DEBUG--print (query)
			#--DEBUG--print (frappe.db.sql(query, as_dict=1))
			for c in frappe.db.sql(query, as_dict=1):
				if c.parent:
					frappe.throw("Serial Number: {0} is already referenced in Sales Invoice: {1}".format(
						serial_no, c.parent
					))

def validate_gst_state(doc, method):
	ship_state = frappe.db.get_value("Address", doc.shipping_address_name, "gst_state")
	if not ship_state:
		frappe.throw("""Please update Correct GST State in Shipping Address and then Try Again""")

	bill_state = frappe.db.get_value("Address", doc.customer_address, "gst_state")
	if not bill_state:
		frappe.throw("""Please update Correct GST State in Billing Address and then Try Again""")

	from frappe.contacts.doctype.address.address import get_address_display
	da = get_address_display(doc.customer_address)
	if da != html.unescape(doc.address_display):
		frappe.throw("""Address has been changed after creating this document, 
					Please use <b>'Update Address</b> under Address to update the correct Billing Address in the Document""")

	da = get_address_display(doc.shipping_address_name)
	if da != html.unescape(doc.shipping_address):
		frappe.throw("""Address has been changed after creating this document, 
					Please use <b>Update Address</b> under Address to update the correct Shipping Address in the Document""")

	if doc.taxes_and_charges == 'Out of State GST' and ship_state == 'Madhya Pradesh':
		if doc.special_invoice and doc.special_invoice == 'SEZ Supply':
			return
		if doc.special_invoice and "bill-to-ship-to" in doc.special_invoice.lower():
			return
		frappe.throw("""Please Check Correct Shipping Address/Taxes""")

	if (doc.taxes_and_charges == 'In State GST' or not doc.taxes_and_charges or doc.taxes_and_charges == "") and ship_state != 'Madhya Pradesh':
		if doc.special_invoice and (doc.special_invoice == 'Insurance Claim' or "bill-to-ship-to" in doc.special_invoice.lower()):
			return
		frappe.throw("""Please Check Correct Shipping Address/Taxes""")

def vehicle_validation(doc, method):
	if cint(doc.b2b_vehicles):
		return

	for i in doc.items:
		if cint(i.is_vehicle) and len(doc.items)>1:
			frappe.throw("A Sales Invoice can have only Single Vehicle and No Other Item")

		if i.serial_no and cint(i.is_vehicle) and len(i.serial_no.strip(' \n').split('\n'))>1:
			frappe.throw("A Sales Invoice can have only ONE Vehicle")

def negative_stock_validation(doc, method, raise_error=False):
	from mapl_customization.customizations_for_mapl.utils import check_if_invoice_will_end_up_in_negative_stock
	if cint(doc.is_return):
		return
	negative_check = check_if_invoice_will_end_up_in_negative_stock(doc)
	if negative_check.result:
		if not raise_error:
			frappe.msgprint("Negative Stock for {0}, Please verify before Submitting".format(negative_check.item_code))
		else:
			frappe.throw("Negative Stock for {0}, Please verify before Submitting".format(negative_check.item_code))

def taxes_and_charges_validation(doc, method):
	if not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
		if doc.total_taxes_and_charges == 0:
			frappe.throw("No Taxes and Charges Applied, Please ensure if this is Ok!!")
		else:
			taxes_inclusive = False
			for i in doc.taxes:
				if cint(i.included_in_print_rate):
					taxes_inclusive = True
					break
			if taxes_inclusive:
				for i in doc.items:
					if i.net_rate == i.rate:
						frappe.throw("""Taxes Does not seems to be Applied on Item {0}, Please ensure if this is Ok!!""".format(i.item_code))

@frappe.whitelist()
def validate_hsn_code(doc, method, raise_error=False):
	if isinstance(doc, str):
		doc = json.loads(doc)
	length_check = frappe.db.get_single_value("Stock Settings", "check_hsn_code_length")
	for i in doc["items"]:
		if not i["gst_hsn_code"]:
			if raise_error:
				frappe.throw("HSN Code not found for {0}".format(i["item_code"]))
			else:
				frappe.msgprint("HSN Code not found for {0}".format(i["item_code"]))
			return 0
		if length_check > 0 and len(i["gst_hsn_code"]) < length_check:
			if raise_error:
				frappe.throw("HSN Code Needs to be at least {0} Digits for Item {1}".format(length_check, i["item_code"]))
			else:
				frappe.msgprint("HSN Code Needs to be at least {0} Digits for Item {1}".format(length_check, i["item_code"]))
			return 0
	return 1

def validate_grand_total(doc, method):
	if not doc.grand_total:
		frappe.throw("Invoice Total Should Be Non - Zero. Please Check Total Values")

def validate_stock_entry_serial_no(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	if doc.doctype.lower() != 'stock entry' and doc.is_return:
		return

	for i in doc.items:
		warehouse = None
		if doc.doctype.lower() != 'stock entry':
			warehouse = i.warehouse
		else:
			warehouse = i.s_warehouse

		if i.serial_no and warehouse:
			snos = i.serial_no.strip(' \n').split('\n')
			for s in snos:
				if warehouse != frappe.db.get_value("Serial No", s, "warehouse"):
					frappe.throw("""Item {0} with Serial No {1} Not in Warehouse {2}""".format(i.item_code, s, warehouse))
