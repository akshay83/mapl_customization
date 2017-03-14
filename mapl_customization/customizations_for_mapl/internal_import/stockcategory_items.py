import frappe

class InternalImportStockCategoryItems:
	def __init__(self, value):
		self.process_node = value
		self.process()        

	def process(self):
		#print "DEBUG: PROCESSEING: CATEGORY:"+self.process_node.category
		if not frappe.db.exists({"doctype":"Brand","brand": self.process_node.category}):
			doc = frappe.get_doc({"doctype":"Brand","brand": self.process_node.category})
			doc.insert(ignore_permissions=True)
		#print "DEBUG: INSERTED: CATEGORY:"+self.process_node.category

