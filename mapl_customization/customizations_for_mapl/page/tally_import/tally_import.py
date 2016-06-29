import frappe
import json
import xmltodict
from xmltodict import ParsingInterrupted
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.currency_items import TallyImportCurrencyItems

@frappe.whitelist()
def read_uploaded_file(ignore_encoding=False):
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from frappe.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()	

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

def process(path, item):
	if (isinstance(item, (dict, set)) and len(item)>0):	

		test_item = item[item.keys()[0]]

		if (isinstance(test_item, dict) and test_item.has_key('@NAME')):
			message = item.keys()[0] + " <> " + test_item['@NAME']
		else:
			message = ''.join(test_item)

		try:
			if (item.has_key('CURRENCY')):
				TallyImportCurrencyItems(item['CURRENCY'])
		except Exception, e:
			message = 'Failed to Import : ' + message
			frappe.publish_realtime("tally_import_progress", {"progress": [len(path), 100], "message": message, "error":True})
			return False

		message = 'Successfully Imported : ' + message
		frappe.publish_realtime("tally_import_progress", {"progress": [len(path), 100], "message": message})

	return True

	
