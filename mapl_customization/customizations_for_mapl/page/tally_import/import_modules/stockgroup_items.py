import frappe

class TallyImportStockGroupItems:
	def __init__(self, value, ow):
		self.overwrite = ow
		self.process_node = value
		self.process()        

	def process(self):
		print "DEBUG: PROCESSING: STOCK GROUP:"+self.process_node['@NAME']
		if not frappe.db.exists({"doctype":"Item Group","item_group_name": self.process_node['@NAME']}):
			doc = frappe.get_doc({"doctype":"Item Group","item_group_name": self.process_node['@NAME']})
		if self.process_node['PARENT']:
			doc.parent_item_group = self.process_node['PARENT']
		else:
			doc.parent_item_group = 'All Item Groups'
		doc.is_group = 1
		doc.insert(ignore_permissions=True)
		print "DEBUG: INSERTED: STOCK GROUP:"+self.process_node['@NAME']
