import frappe
import json
import xmltodict

@frappe.whitelist()
def read_uploaded_file(ignore_encoding=False):
	if getattr(frappe, "uploaded_file", None):
		with open(frappe.uploaded_file, "r") as upfile:
			fcontent = upfile.read()
	else:
		from frappe.utils.file_manager import get_uploaded_content
		fname, fcontent = get_uploaded_content()	

	xmlstr = xmltodict.parse(fcontent)
	return xmlstr

