import frappe

class InternalImportGodownItems:
	def __init__(self, value):
		self.process_node = value
		self.process()        

	def process(self):
		#print "DEBUG: PROCESSING: GODOWN:"+self.process_node.warehouse
		if not frappe.db.exists({"doctype":"Warehouse","warehouse_name": self.process_node.warehouse}):
			godown_doc = frappe.get_doc({"doctype":"Warehouse","warehouse_name": self.process_node.warehouse})
			godown_doc.insert(ignore_permissions=True)
		#print "DEBUG: INSERTED: GODOWN:"+self.process_node.warehouse

