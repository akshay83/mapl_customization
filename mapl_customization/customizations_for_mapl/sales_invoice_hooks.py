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
	pass