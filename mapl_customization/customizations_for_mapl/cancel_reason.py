import frappe
import json

@frappe.whitelist()
def update_reason(doc, reason):
	if isinstance(doc, basestring):
		doc = json.loads(doc)

	frappe.db.set_value(dt=doc['doctype'],
			dn=doc['name'],
			field="cancel_reason",
			val=reason)
	
