import frappe

class InternalImportStockDetails:
	def __init__(self, value, od, bc):
		self.open_date = od
		self.process_node = value
		self.brand_category = bc
		self.process()        

	def process(self):
		#print "DEBUG: PROCESSING: STOCK_ITEM:"+self.process_node.item_name
		if self.brand_category:
			if self.process_node.category.upper() not in self.brand_category.upper():
				return

		if (self.process_node.qty<=0):
			return

		if not frappe.db.exists({"doctype":"Item","item_code": self.process_node.item_name}):
			return

		stockentry_doc = frappe.new_doc('Stock Entry')
		stockentry_doc.purpose = 'Material Receipt'
		stockentry_doc.difference_account = frappe.get_value("Account", dict(name=('like', '%%%s%%' % 'Temporary Opening')))
		stockentry_doc.posting_date = self.open_date

		item_detail = stockentry_doc.append("items")
		item_detail.item_code = self.process_node.item_name
		item_detail.t_warehouse = frappe.get_value("Warehouse",filters={"warehouse_name": self.process_node.warehouse})

		if self.process_node.batch and len(self.process_node.batch) > 0:
			item_detail.serial_no = self.process_node.batch        

		item_detail.qty = self.process_node.qty

		if self.process_node.value == 0:
			self.process_node.value = 1

		item_detail.basic_rate = self.process_node.value

		stockentry_doc.save(ignore_permissions=True)
		stockentry_doc.submit()

		import_doc = frappe.get_doc('Tally Stock Details', self.process_node.name)
		import_doc.imported = 1
		import_doc.save()		
		#print "DEBUG: INSERTED: STOCK_ITEM:"+self.process_node.item_name 
