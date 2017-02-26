import frappe
import math
import json

class TallyInternalStockImport:
	def __init__(self,od):
		self.total_rows = 0
		self.total_batch_rows = 100.0
		self.current_batch = 0
		self.open_date = od
		self.start_process()

	def get_stock_item_count(self, table):
		row_count = frappe.db.sql("""select ifnull(count(*),0) as rows from `tab{table}`""".format(**{"table" : table}),as_dict=1)
		return row_count[0].rows if row_count else 0

	def get_next_batch(self, table):
		return frappe.db.sql("""select * from `tab{table}` order by item_name 
	                limit {current_batch} offset {batch_offset}""".format(**{
			"table" : table,
                        "current_batch" : int(self.total_batch_rows),
                        "batch_offset" : self.current_batch}), as_dict=1)

	def start_process(self):
		self.do_categories()
		self.do_stock_groups()
		self.do_warehouse()
		frappe.db.commit()
		self.do_stock_items()
		self.do_stock_details()
		frappe.db.commit()


	def do_stock_details(self):
		self.current_batch = 0
		self.total_rows = self.get_stock_item_count('Tally Stock Details')
		self.total_batches = math.ceil(self.total_rows / self.total_batch_rows)
		for x in range(0,int(self.total_batches)):
			self.records = self.get_next_batch('Tally Stock Details')
			if not self.records:
				break
			self.current_batch = self.current_batch + len(self.records)
			for r in self.records:
				self.process_stock_details(r)
			frappe.db.commit()



	def do_stock_items(self):
		self.current_batch = 0
		self.total_rows = self.get_stock_item_count('Tally Stock Items')
		self.total_batches = math.ceil(self.total_rows / self.total_batch_rows)
		for x in range(0,int(self.total_batches)):
			self.records = self.get_next_batch('Tally Stock Items')
			if not self.records:
				break
			self.current_batch = self.current_batch + len(self.records)
			for r in self.records:
				if r.closing_qty > 0:
					self.process_stock_items(r)
			frappe.db.commit()


	def process_stock_items(self,rec):
		if not frappe.db.exists({"doctype":"Item","item_code": rec.stock_item}):
			item_doc = frappe.new_doc('Item')
			item_doc.item_code = rec.item_name
			item_doc.item_name = rec.item_name
			item_doc.item_group = rec.stock_group
			item_doc.brand = rec.category            
			item_doc.has_serial_no = rec.batch_on
			item_doc.is_stock_item = 1
			if rec.vat_rate:
				template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%%%s%%' % rec.vat_rate)))
				if template:
					item_doc.taxes_template = template
				else:
					item_dic.taxes_template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%15%')))
			else:
				item_dic.taxes_template = frappe.db.get_value("Item Taxes Template", dict(name=('like', '%15%')))
			item_doc.save(ignore_permissions=True)


	def process_stock_details(self, rec):
		if (rec.qty<=0):
			return

		stockentry_doc = frappe.new_doc('Stock Entry')
		stockentry_doc.purpose = 'Material Receipt'
		stockentry_doc.difference_account = frappe.get_value("Account",filters={"account_name": 'Temporary Opening'})
		stockentry_doc.posting_date = self.open_date

		item_detail = stockentry_doc.append("items")
		item_detail.item_code = rec.item_name
		item_detail.t_warehouse = frappe.get_value("Warehouse",filters={"warehouse_name": rec.warehouse})

		if rec.batch != 'Primary Batch':
			item_detail.serial_no = rec.batch        

		item_detail.qty = rec.qty

		item_detail.basic_rate = rec.value

		stockentry_doc.save(ignore_permissions=True)
		stockentry_doc.submit()
			


	def do_categories(self):
		categories = frappe.db.sql("""select distinct category from `tabTally Stock Items` order by category""",as_dict=1)
		for c in categories:
			if not frappe.db.exists({"doctype":"Brand","brand": c.category}):
				doc = frappe.get_doc({"doctype":"Brand","brand": c.category})
				doc.insert(ignore_permissions=True)

	def do_stock_groups(self):
		groups = frappe.db.sql("""select distinct stock_group from `tabTally Stock Items` order by stock_group""",as_dict=1)
		for g in groups:
			if not frappe.db.exists({"doctype":"Item Group","item_group_name": g.stock_group}):
				doc = frappe.get_doc({"doctype":"Item Group","item_group_name": g.stock_group})
				doc.parent_item_group = 'All Item Groups'
				doc.is_group = 1
				doc.insert(ignore_permissions=True)

	def do_warehouse(self):
		warehouse = frappe.db.sql("""select distinct warehouse from `tabTally Stock Details` order by warehouse""",as_dict=1)
		for w in warehouse:
			if not frappe.db.exists({"doctype":"Warehouse","warehouse_name": w.warehouse}):
				godown_doc = frappe.get_doc({"doctype":"Warehouse","warehouse_name": w.warehouse})
				godown_doc.insert(ignore_permissions=True)

@frappe.whitelist()
def process_import(open_date=None):
	print '------------------------HELLO INTERNAL-------------------------'
	params = json.loads(frappe.form_dict.get("params") or '{}')

	if params.get("open_date"):
		open_date = params.get("open_date")

	if not open_date:
		return

	TallyInternalStockImport(od=open_date)

	frappe.publish_realtime("tally_import_progress", {
                                                "message": "Import From Internal Table Successful"
                                        }, user=frappe.session.user)

	return {"messages": "Import Successful", "error": False}

