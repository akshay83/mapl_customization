import frappe

class TallyImportStockItems:
	def __init__(self, value, ow, od, bc):
		self.overwrite = ow
		self.process_node = value
		self.open_date = od
		self.brand_category = bc
		self.process()        

	def process(self):
		print "DEBUG: PROCESSING: STOCK_ITEM:"+self.process_node['@NAME']
		if not self.process_node['CATEGORY']:
			return

		if self.brand_category:
			if self.process_node['CATEGORY'].upper() not in self.brand_category:
				return

		if not frappe.db.exists({"doctype":"Item","item_code": self.process_node['@NAME']}):
			if self.process_node.has_key('OPENINGBALANCE'):
				uom_index = self.process_node['OPENINGBALANCE'].find(self.process_node['BASEUNITS'],0)
				open_qty = float(self.process_node['OPENINGBALANCE'][:uom_index])
				if open_qty<=0:
					return

			item_doc = frappe.new_doc('Item')
			item_doc.item_code = self.process_node['@NAME']
			item_doc.item_name = self.process_node['@NAME']
			if self.process_node['PARENT']:
				item_doc.item_group = self.process_node['PARENT']
			else:
				item_doc.item_group = 'All Item Groups'
			item_doc.brand = self.process_node['CATEGORY']            
			item_doc.has_serial_no = 1 if self.process_node['ISBATCHWISEON'] == 'Yes' else 0
			item_doc.stock_uom = self.process_node['BASEUNITS']       
			item_doc.is_stock_item = 1
			if self.process_node['RATEOFVAT']:
				template = frappe.db.get_value("Item Taxes Template", {"name": ("like %%%s%%" % self.process_node['RATEOFVAT'])})
				if template:
					item_doc.taxes_template = template
				else:
					item_doc.taxes_template = frappe.db.get_value("Item Taxes Template", {"name": ("like %14%")})
			item_doc.save(ignore_permissions=True)

			if self.process_node['BATCHALLOCATIONS.LIST']:
				if isinstance(self.process_node['BATCHALLOCATIONS.LIST'], list):
					for batch_allocations in self.process_node['BATCHALLOCATIONS.LIST']:
						self.process_batches(batch_allocations)
				elif isinstance(self.process_node['BATCHALLOCATIONS.LIST'], dict):
					self.process_batches(self.process_node['BATCHALLOCATIONS.LIST'])
			print "DEBUG: PROCESSING: STOCK_ITEM:"+self.process_node['@NAME']


	def process_batches(self, batch):
		stockentry_doc = frappe.new_doc('Stock Entry')
		stockentry_doc.purpose = 'Material Receipt'
		stockentry_doc.difference_account = frappe.get_value("Account",filters={"account_name": 'Temporary Opening'})
		stockentry_doc.posting_date = self.open_date

		item_detail = stockentry_doc.append("items")
		item_detail.item_code = self.process_node['@NAME']
		item_detail.t_warehouse = frappe.get_value("Warehouse",filters={"warehouse_name": batch['GODOWNNAME']})

		if self.process_node['ISBATCHWISEON'] == 'Yes':
			item_detail.serial_no = batch['BATCHNAME']        

		uom_index = batch['OPENINGBALANCE'].find(self.process_node['BASEUNITS'],0)
		if (float(batch['OPENINGBALANCE'][:uom_index])<=0):
			return
		item_detail.qty = float(batch['OPENINGBALANCE'][:uom_index])

		rate_per_index = batch['OPENINGRATE'].find("/",0)
		item_detail.basic_rate = float(batch['OPENINGRATE'][:rate_per_index])

		item_detail.uom = self.process_node['BASEUNITS']

		stockentry_doc.save(ignore_permissions=True)
		stockentry_doc.submit()
      
