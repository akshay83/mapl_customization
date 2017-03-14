import frappe
import json


def before_save_salesinvoice(doc, method):
	old_values = frappe.db.sql("""select workflow_state,grand_total from `tabSales Invoice` where name=%(name)s""",{'name':doc.name},as_dict=1)

	if old_values:
		if old_values[0].workflow_state in ["Draft","Pending","Approved"]:
			if doc.workflow_state in ["Rejected","Approved"]:
				return
		elif old_values[0].workflow_state not in ["Rejected"]:
			return
		elif doc.workflow_state in ["Rejected"] and old_values[0].grand_total==doc.grand_total:
			return

	validate_undercut_salesinvoice(doc)

def validate_undercut_salesinvoice(doc):
	validate_price_list_undercut_salesinvoice(doc)
	validate_avg_undercut_salesinvoice(doc)

def validate_price_list_undercut_salesinvoice(doc):	
	check_price = frappe.db.get_single_value("Selling Settings", "check_price")
	if  check_price != 'Both' and check_price != 'Check for Price List Price':
		return

	modify_workflow = False
	for i in doc.items:
		if i.price_list_rate > 0:
			if i.price_list_rate > i.rate:
				modify_workflow = True
				break

	if modify_workflow:
		doc.db_set("workflow_state", "Pending")
	else:
		doc.db_set("workflow_state", "Draft")



def validate_avg_undercut_salesinvoice(doc):
	check_price = frappe.db.get_single_value("Selling Settings", "check_price")
	if  check_price != 'Both' and check_price != 'Check for Avg Price':
		return

	total_selling_rate = 0
	total_avg_rate = 0
	for i in doc.items:
		total_selling_rate = total_selling_rate+i.net_amount
		item_rate = frappe.db.sql("""select ifnull(sum(incoming_rate)/sum(actual_qty),0) as avg_rate 
				from `tabStock Ledger Entry` where item_code = %(item)s""", {'item':i.item_code}, as_dict=1)
		total_avg_rate = total_avg_rate+(item_rate[0].avg_rate*i.qty)

	if (total_selling_rate < total_avg_rate):
		doc.db_set("workflow_state", "Pending")
	else:
		doc.db_set("workflow_state", "Draft")

def on_update_selling_settings(doc, method):
	if not frappe.db.exists({"doctype":"Workflow","workflow_name": 'Sales Invoice Undercut'}):
		return

	workdoc = frappe.get_doc("Workflow", "Sales Invoice Undercut")
	workdoc.is_active = True if doc.check_price else False
	workdoc.save()
