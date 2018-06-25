import frappe
from frappe.model.naming import make_autoname
from erpnext.accounts.utils import get_fiscal_year
from frappe.utils import getdate, today

def set_auto_name(doc, method):
	#print "DEBUG -----------------------------AUTO NAME------------------------"

	dt_meta = frappe.get_meta(doc.doctype)

	location = "VN"

	docs = 	{
		"Sales Invoice" : "INV",
		"Purchase Invoice" : "PINV",
		"Payment Entry" : "REC",
		"Delivery Note" : "DN",
		"Stock Entry" : "STE",
		"Journal Entry" : "JV",
		"Sales Order" : "SO",
		"Purchase Receipt" : "PREC",
		"Quotation" : "QTN"
		}

	if doc.doctype in ("Sales Invoice", "Purchase Invoice", "Payment Entry", "Delivery Note", \
			"Stock Entry", "Journal Entry", "Sales Order", "Purchase Receipt", "Quotation"):

		if doc.doctype == "Journal Entry" and 'FIN' in doc.naming_series:
			return

		user = frappe.session.user
		user_group = frappe.db.get_value("User", user, "user_group")

		if user_group:
			if (user_group.lower() == "geeta bhawan"):
				location = "GB"
			elif (user_group.lower() == "ranjeet hanuman"):
				location = "RH"
		#print "DEBUG:"+location

		abbr = frappe.db.get_value("Company", doc.company, "abbr")

		docdt = doc.posting_date if doc.posting_date else today()
		if doc.doctype in ("Sales Order", "Purchase Receipt"):
			docdt = doc.transaction_date
		fiscal_year =  str(get_fiscal_year(date=docdt)[0])
		#print "DEBUG:"+fiscal_year

		short_fiscal_year = fiscal_year[2:4] + "-" + fiscal_year[7:9]

		dt = docs.get(doc.doctype,"")
		if doc.doctype not in ("Payment Entry", "Journal Entry", "Stock Entry", "Quotation", "Sales Order"):
			if doc.is_return:
				dt = dt+"-RET"
		elif doc.doctype == "Payment Entry":
			if doc.payment_type != "Receive":
				dt = "PAY"
		#print "DEBUG:"+dt

		nm = ""
		if getdate(docdt)<getdate("2018-04-01"):
			if doc.doctype != "Journal Entry":
				nm = make_autoname(key=abbr+"/"+location+"/"+dt+"/"+".YYYY."+"/"+".######", doctype=doc.doctype)
			else:
				nm = make_autoname(key=abbr+"/"+"JV"+"/"+".YYYY."+"/"+".######", doctype=doc.doctype)
		else:
			nm = make_autoname(key=abbr+"/"+dt+"/"+location+"/"+short_fiscal_year+"/"+".######", doctype=doc.doctype)

			if dt_meta.get_field("reporting_name"):
				#print "DEBUG:"+location+"/"+short_fiscal_year+"/"+nm[-6:]
				doc.reporting_name = ("R" if "-RET" in nm else "")+location+"/"+short_fiscal_year+"/"+nm[-6:]

		#print "DEBUG:"+nm
		doc.name = nm

	#print "DEBUG:-------------------------------------------------------------"
