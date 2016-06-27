import frappe
import json
import xmltodict
from mapl_customization.customizations_for_mapl.page.tally_import.import_modules.currency_items import TallyImportCurrencyItems

@frappe.whitelist()
def read_uploaded_file(ignore_encoding=False):
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from frappe.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()	

	xmlstr = xmltodict.parse(fcontent, item_depth=5, item_callback=process)

def process_dict(xmlstr):
    stock_dict = xmlstr
    stock_messages = sd['ENVELOPE']['BODY']['IMPORTDATA']['REQUESTDATA']['TALLYMESSAGE']

def process(path, item):
	if (isinstance(item, (dict, set))):	
		if (item.has_key('CURRENCY')):
			TallyImportCurrencyItems(item['CURRENCY'])

	return True

	
