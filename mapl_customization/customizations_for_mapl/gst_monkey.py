import frappe
import re
from frappe.utils import getdate
from erpnext.regional.india.utils import GST_INVOICE_NUMBER_FORMAT,get_transport_details, get_item_list, get_address_details, validate_doc

#As if 1st Feb 2022 this Method is Same in both Version-13 Branches and Develop Branch
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

#As of 1st Feb 2022 This method is different in Vesion-13 Branch and Develop Branch
def get_ewb_data(dt, dn):

	ewaybills = []
	for doc_name in dn:
		doc = frappe.get_doc(dt, doc_name)

		validate_doc(doc)

		data = frappe._dict({
			"transporterId": "",
			"TotNonAdvolVal": 0,
		})

		data.userGstin = data.fromGstin = doc.company_gstin
		data.supplyType = 'O'

		if dt == 'Delivery Note':
			data.subSupplyType = 1
		#monkey here
		elif doc.gst_category in ['Registered Regular', 'SEZ', 'Unregistered', 'Consumer']:
			data.subSupplyType = 1
		elif doc.gst_category in ['Overseas', 'Deemed Export']:
			data.subSupplyType = 3
		else:
			frappe.throw(_('Unsupported GST Category for E-Way Bill JSON generation'))

		data.docType = 'INV'
		data.docDate = frappe.utils.formatdate(doc.posting_date, 'dd/mm/yyyy')

		company_address = frappe.get_doc('Address', doc.company_address)
		billing_address = frappe.get_doc('Address', doc.customer_address)

		#added dispatch address
		dispatch_address = frappe.get_doc('Address', doc.dispatch_address_name) if doc.dispatch_address_name else company_address
		shipping_address = frappe.get_doc('Address', doc.shipping_address_name)

		data = get_address_details(data, doc, company_address, billing_address, dispatch_address)

		data.itemList = []
		data.totalValue = doc.net_total

		data = get_item_list(data, doc, hsn_wise=True)

		disable_rounded = frappe.db.get_single_value('Global Defaults', 'disable_rounded_total')
		data.totInvValue = doc.grand_total if disable_rounded else doc.rounded_total

		data = get_transport_details(data, doc)

		fields = {
			"/. -": {				
				'docNo': doc.reporting_name, #monkey-here
				'fromTrdName': doc.company,
				'toTrdName': doc.customer_name,
				'transDocNo': doc.lr_no,
			},
			"@#/,&. -": {
				'fromAddr1': company_address.address_line1,
				'fromAddr2': company_address.address_line2,
				'fromPlace': company_address.city,
				'toAddr1': shipping_address.address_line1,
				'toAddr2': shipping_address.address_line2,
				'toPlace': shipping_address.city,
				'transporterName': doc.transporter_name
			}
		}

		for allowed_chars, field_map in fields.items():
			for key, value in field_map.items():
				if not value:
					data[key] = ''
				else:
					data[key] = re.sub(r'[^\w' + allowed_chars + ']', '', value)

		ewaybills.append(data)

	data = {
		'version': '1.0.0421',
		'billLists': ewaybills
	}

	return data		

def monkey_patch_ewb_data():
	from erpnext.regional.india import utils
	utils.get_ewb_data = get_ewb_data

def monkey_patch_gst_validate_document_name():
	from erpnext.regional.india import utils
	utils.validate_document_name = validate_document_name

def monkey_patch_gst():
	monkey_patch_gst_validate_document_name()
	monkey_patch_ewb_data()
