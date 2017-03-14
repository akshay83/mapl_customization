import frappe

class TallyImportGodownItems:
	def __init__(self, value, ow):
		self.overwrite = ow
		self.process_node = value
		self.process()        

	def process(self):
		print "DEBUG: PROCESSING: GODOWN:"+self.process_node['@NAME']
		if not frappe.db.exists({"doctype":"Warehouse","warehouse_name": self.process_node['@NAME']}):
			godown_doc = frappe.get_doc({"doctype":"Warehouse","warehouse_name": self.process_node['@NAME']})
			godown_doc.insert(ignore_permissions=True)
			print "DEBUG: INSERTED: GODOWN:"+self.process_node['@NAME']

