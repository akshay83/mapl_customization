import frappe

class InternalImportStockGroupItems:
	def __init__(self, value):
		self.process_node = value
		self.process()        

	def process(self):
		#print "DEBUG: PROCESSING: STOCK GROUP:"+self.process_node.stock_group
		if not frappe.db.exists({"doctype":"Item Group","item_group_name": self.process_node.stock_group}):
			doc = frappe.get_doc({"doctype":"Item Group","item_group_name": self.process_node.stock_group})
			doc.parent_item_group = 'All Item Groups'
			doc.is_group = 1
			doc.insert(ignore_permissions=True)
		#print "DEBUG: INSERTED: STOCK GROUP:"+self.process_node.stock_group
