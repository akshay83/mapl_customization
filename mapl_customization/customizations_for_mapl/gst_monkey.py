import frappe
from frappe.utils import getdate
from erpnext.regional.india.utils import GST_INVOICE_NUMBER_FORMAT

def validate_document_name(doc, method=None):
	"""Validate GST invoice number requirements."""

	country = frappe.get_cached_value("Company", doc.company, "country")

	# Date was chosen as start of next FY to avoid irritating current users.
	if country != "India" or getdate(doc.posting_date) < getdate("2021-04-01"):
		return

	#monkey-here
	#if len(doc.name) > 16:
	#	frappe.throw(_("Maximum length of document number should be 16 characters as per GST rules. Please change the naming series."))

	if not GST_INVOICE_NUMBER_FORMAT.match(doc.name):
		frappe.throw(_("Document name should only contain alphanumeric values, dash(-) and slash(/) characters as per GST rules. Please change the naming series."))

def monkey_patch_gst_validate_document_name():
	from erpnext.regional.india import utils
	utils.validate_document_name = validate_document_name
