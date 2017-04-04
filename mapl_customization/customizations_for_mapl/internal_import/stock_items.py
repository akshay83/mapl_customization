import frappe

class InternalImportStockItems:
	def __init__(self, value, bc):
		self.process_node = value
		self.brand_category = bc
		self.process()        

	def process(self):
		#print "DEBUG: PROCESSING: STOCK_ITEM:"+self.process_node.item_name
		if self.brand_category:
			if self.process_node.category.upper() not in self.brand_category.upper():
				return

		if not frappe.db.exists({"doctype":"Item","item_code": self.process_node.item_name}):
			item_doc = frappe.new_doc('Item')
			item_doc.item_code = self.process_node.item_name
			item_doc.item_name = self.process_node.item_name
			item_doc.item_group = self.process_node.stock_group
			item_doc.brand = self.process_node.category            
			item_doc.has_serial_no = self.process_node.batch_on
			item_doc.description = self.process_node.description
			item_doc.is_stock_item = 1
			if self.process_node.vat_rate:
				template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%%%s%%' % self.process_node.vat_rate)))
				if template:
					item_doc.taxes_template = template
				else:
					item_doc.taxes_template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%15%')))
			else:
				item_doc.taxes_template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%15%')))
			item_doc.save(ignore_permissions=True)     
		#print "DEBUG: INSERTED: STOCK_ITEM:"+self.process_node.item_name 
