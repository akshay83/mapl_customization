import frappe
import json
import time
from frappe.utils import today, getdate, date_diff
from frappe.utils import cstr, cint

def on_submit(doc, method):
	pass 

def month_diff(string_ed_date, string_st_date):
	ed_date = getdate(string_ed_date)
	st_date = getdate(string_st_date)
	return ed_date.month - st_date.month

def before_cancel(doc, method):
	# Check for Taxes
	docdate = getdate(doc.posting_date)
	# print abs(date_diff(docdate, getdate()))
	if getdate().day >= 10 and abs(month_diff(docdate, getdate())) > 0:
		if not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
			frappe.throw("""Bill Cancellation Not Allowed as Taxes Might Have Been Filed""")

def on_cancel(doc, method):
	if doc.irn and not cint(doc.irn_cancelled) and not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
		frappe.throw("""IRN Generated, Cannot Cancel""")
	
	if doc.ewaybill and not cint(doc.eway_bill_cancelled) and not (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
		frappe.throw("""Eway Bill Generated, Cannot Cancel""")
		
	if frappe.db.get_single_value('Accounts Settings', 'enable_common_party_accounting'):
		list = frappe.get_list("Journal Entry", filters=[
					["remark","like","%{0}%".format(doc.name)],
					["docstatus","=",1]
				],fields=["name"])
		for l in list:
			frappe.get_doc("Journal Entry", l.name).cancel()