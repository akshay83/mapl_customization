import json
import frappe

@frappe.whitelist()
def json_load(str):
	return json.loads(str)

def int_to_Roman(num):
	val = [
		1000, 900, 500, 400,
		100, 90, 50, 40,
		10, 9, 5, 4, 1
	]
	syb = [
		"M", "CM", "D", "CD",
		"C", "XC", "L", "XL",
		"X", "IX", "V", "IV",
		"I"
	]
	roman_num = ''
	i = 0
	while  num > 0:
		for _ in range(num // val[i]):
			roman_num += syb[i]
			num -= val[i]
		i += 1
	return roman_num

@frappe.whitelist()
def date_to_code(dt):
	if not dt:
		return

	code = ""
	if dt.day < 10:
		code = code + "0"
	code = code + str(dt.day)
	code = code + int_to_Roman(dt.month)
	code = code + str(dt.year%2000)
	return code

@frappe.whitelist()
def render_template(content, doc):
	return frappe.utils.jinja.render_template(content, {"doc":doc})

def table_exists(doctype):
	return frappe.db.table_exists(doctype)

def doc_exists(*args, **kwargs):
	return frappe.db.exists(*args, **kwargs)