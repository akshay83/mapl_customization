import frappe
import json
import datetime
import HTMLParser
import re
from frappe.utils import cint


# Function to Repost Zero Value Invoices as They Dont Adjust Cost of Goods Sold
def repost_zero_value_sales():
	vouchers = frappe.db.sql("""select distinct name as voucher_no, 'Sales Invoice' as voucher_type from `tabSales Invoice` where docstatus = 1 and grand_total = 0""")
	rejected = []
	i = 0
	for voucher_no, voucher_type in vouchers:
		i+=1
		print (i, "/", len(vouchers), voucher_type, voucher_no)
		try:

			doc = frappe.get_doc(voucher_type, voucher_no)

			for dt in ["GL Entry"]:
				frappe.db.sql("""delete from `tab%s` where voucher_type=%s and voucher_no=%s"""%
					(dt,'%s',  '%s'), (voucher_type, voucher_no))

			#doc.update_stock_ledger()
			doc.make_gl_entries(repost_future_gle=False)
			frappe.db.commit()
		except Exception as e:
			print(frappe.get_traceback())
			rejected.append([voucher_type, voucher_no])
			frappe.db.rollback()

	print (rejected)


# Function to Repost all Stock Related Vouchers to Recalculate Valuation Rate and Stock Value Difference
def repost_all_stock_vouchers():
	vouchers = frappe.db.sql("""select distinct voucher_type,voucher_no from (
		(select distinct posting_date, posting_time, name as voucher_no, 'Sales Invoice' as voucher_type from `tabSales Invoice` where docstatus = 1)
			  union all
		(select distinct  posting_date, posting_time,name as voucher_no, 'Purchase Invoice' as voucher_type from `tabPurchase Invoice` where docstatus = 1)  
			  union all
		(select distinct  posting_date, posting_time,name as voucher_no, 'Stock Entry' as voucher_type from `tabStock Entry` where docstatus = 1)  
			  union all
		(select distinct  posting_date, posting_time,name as voucher_no, 'Delivery Note' as voucher_type from `tabDelivery Note` where docstatus = 1)  ) a order by posting_date, posting_time, voucher_no""")

	frappe.db.sql("""delete from `tabSerial No`""")
	frappe.db.sql("""delete from `tabStock Ledger Entry` where voucher_type in ('Sales Invoice', 'Purchase Invoice', 'Stock Entry', 'Delivery Note')""")
	frappe.db.sql("""delete from `tabGL Entry` where voucher_type in ('Sales Invoice', 'Purchase Invoice', 'Stock Entry', 'Delivery Note')""")
	frappe.db.sql("""create table if not exists `tabRepost` (voucher_type varchar(50), voucher_no varchar(100))""")
	frappe.db.sql("""delete from `tabRepost`""")

	rejected = []
	i = 0
	for voucher_type, voucher_no in vouchers:
		i+=1
		print(i, "/", len(vouchers), voucher_type, voucher_no)
		try:
			#for dt in ["Stock Ledger Entry", "GL Entry"]:
			#	frappe.db.sql("""delete from `tab%s` where voucher_type=%s and voucher_no=%s"""%
			#		(dt, '%s', '%s'), (voucher_type, voucher_no))

			doc = frappe.get_doc(voucher_type, voucher_no)
			if voucher_type=="Stock Entry":
				doc.calculate_rate_and_amount(force=1)

			doc.update_stock_ledger()
			doc.make_gl_entries(repost_future_gle=False)
			frappe.db.commit()
		except Exception as e:
			print(frappe.get_traceback())
			rejected.append([voucher_type, voucher_no])
			frappe.db.rollback()

	try:
		for voucher_type, voucher_no in rejected:
			frappe.db.sql("""insert into `tabRepost` values (%s, %s)""", (voucher_type, voucher_no))
		frappe.db.commit()
	except Exception as e:
		pass

	print(rejected)

#Custom from Forums
def repost():
	warehouse_name = ""
	account_name = ""

	vouchers = frappe.db.sql("""select distinct voucher_type, voucher_no
		from `tabStock Ledger Entry` sle
		where voucher_type != "Serial No"
		order by posting_date, posting_time, name""")

	rejected = []
	i = 0
	for voucher_type, voucher_no in vouchers:
		i+=1
		print i, "/", len(vouchers), voucher_type, voucher_no
		try:
			frappe.db.sql("""delete from `tabGL Entry` where voucher_type=%s and voucher_no=%s""",
				(voucher_type, voucher_no))

			doc = frappe.get_doc(voucher_type, voucher_no)
			if voucher_type=="Stock Entry":
				doc.calculate_rate_and_amount(force=1)

			doc.make_gl_entries(repost_future_gle=False)
			frappe.db.commit()
		except Exception, e:
			print frappe.get_traceback()
			rejected.append([voucher_type, voucher_no])
			frappe.db.rollback()

	if rejected:
		print rejected
