import frappe
import json
import xmltodict
from xmltodict import ParsingInterrupted
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.currency_items import TallyImportCurrencyItems
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.godown_items import TallyImportGodownItems
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.stockgroup_items import TallyImportStockGroupItems
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.stockcategory_items import TallyImportStockCategoryItems

overwrite_existing = True
opening_date = None

@frappe.whitelist()
def read_uploaded_file(ignore_encoding=False,overwrite=False,opendate=None):
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from frappe.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()	

	global overwrite_existing
	overwrite_existing = overwrite

	global opening_date
	opening_date = opendate

	try:
		xmltodict.parse(fcontent, item_depth=5, item_callback=process)
	except ParsingInterrupted:
		frappe.db.rollback()
		return {"messages": ["There was a Problem Importing" + ": " + "HG"], "error": True}

	frappe.db.commit()
	return {"messages": "Import Successful", "error": False}


def process_dict(xmlstr):
    stock_dict = xmlstr
    #stock_messages = sd['ENVELOPE']['BODY']['IMPORTDATA']['REQUESTDATA']['TALLYMESSAGE']

def document_import(item):
	if (item.has_key('CURRENCY')):
		TallyImportCurrencyItems(value=item['CURRENCY'],ow=overwrite_existing)
	elif (item.has_key('GODOWN')):
		TallyImportGodownItems(value=item['GODOWN'],ow=overwrite_existing)
	elif (item.has_key('STOCKCATEGORY')):
		TallyImportStockCategoryItems(value=item['STOCKCATEGORY'],ow=overwrite_existing)	
	elif (item.has_key('STOCKGROUP')):
		TallyImportStockGroupItems(value=item['STOCKGROUP'],ow=overwrite_existing)
	else: 
		return 'Skipped'
	return 'Success'

def process(path, item):
	if (isinstance(item, (dict, set)) and len(item)>0):	

		test_item = item[item.keys()[0]]

		if (isinstance(test_item, dict) and test_item.has_key('@NAME')):
			message = document_description = item.keys()[0] + " <> " + test_item['@NAME']
		else:
			message = document_description = ''.join(test_item)

		try:
			status = document_import(item)
			if (status == 'Skipped'):				
				message = 'Skipped : ' + message
		except Exception, e:
			print e
			message = 'Failed to Import : ' + message
			frappe.publish_realtime("tally_import_progress", {
				"progress": [len(path), 100], 
				"message": message, 
				"error":True,
				"error_desc": e,
				}, user=frappe.session.user)
			return False

		if (message[:7] != 'Skipped'):
			message = 'Successfully Imported : ' + message

		frappe.publish_realtime("tally_import_progress", {
							"progress": [len(path), 100], 
							"message": message, 
							"document" : document_description
						}, user=frappe.session.user)

	return True

