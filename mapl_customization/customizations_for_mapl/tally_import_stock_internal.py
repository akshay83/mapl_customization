import frappe
import math
import json
from mapl_customization.customizations_for_mapl.internal_import.stock_details import InternalImportStockDetails
from mapl_customization.customizations_for_mapl.internal_import.stockgroup_items import InternalImportStockGroupItems
from mapl_customization.customizations_for_mapl.internal_import.stock_items import InternalImportStockItems
from mapl_customization.customizations_for_mapl.internal_import.godown_items import InternalImportGodownItems
from mapl_customization.customizations_for_mapl.internal_import.stockcategory_items import InternalImportStockCategoryItems


class TallyInternalStockImport:
	def __init__(self,od,bc):
		self.total_rows = 0
		self.total_batch_rows = 20.0
		self.current_batch = 0
		self.open_date = od
		self.brand_category = bc
		self.start_process()

	def get_stock_item_count(self, table):
		row_count = frappe.db.sql("""select ifnull(count(*),0) as rows from `tab{table}`
			where category in ('{category_names}')""".format(**{
			"table" : table,
			"category_names": ','.join(self.brand_category) if not isinstance(self.brand_category,basestring) else self.brand_category,
			}),as_dict=1)
		return row_count[0].rows if row_count else 0

	def get_next_batch(self, table):
		return frappe.db.sql("""select * from `tab{table}` where category in ('{category_names}') order by item_name 
	                limit {current_batch} offset {batch_offset}""".format(**{
			"table" : table,
			"category_names": ','.join(self.brand_category) if not isinstance(self.brand_category, basestring) else self.brand_category,
                        "current_batch" : int(self.total_batch_rows),
                        "batch_offset" : self.current_batch}), as_dict=1)

	def update_category_in_details(self):
		row_count = frappe.db.sql("""select ifnull(count(*),0) as rows from `tabTally Stock Details` where category is not null""",as_dict=1)
		if not row_count:
			self.update_categories()
		if (row_count and row_count[0].rows <= 0):
			self.update_categories()


	def update_categories(self):
		frappe.db.sql("""update `tabTally Stock Details` det set category=(select category from 
				`tabTally Stock Items` where item_name=det.item_name)""")

	def start_process(self):
		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Importing Categories</b></span>"""
                                        }, user=frappe.session.user)

		self.do_categories()

		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Importing Stock Groups</b></span>"""
                                        }, user=frappe.session.user)

		self.do_stock_groups()

		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Importing Warehouses</b></span>"""
                                        }, user=frappe.session.user)

		self.do_warehouse()
		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Updating Category/Brands in Details</b></span>"""
                                        }, user=frappe.session.user)
		
		self.update_category_in_details()
		frappe.db.commit()

		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Importing Stock Items</b></span>"""
                                        }, user=frappe.session.user)

		self.do_stock_items()

		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;"><b>Importing Stock Details</b></span>"""
                                        }, user=frappe.session.user)

		self.do_stock_details()
		frappe.db.commit()


	def do_stock_details(self):
		self.current_batch = 0
		self.total_batch_rows = 5.0
		self.total_rows = self.get_stock_item_count('Tally Stock Details')
		self.total_batches = math.ceil(self.total_rows / self.total_batch_rows)

		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;">Total Batches:"""+str(self.total_batches)+"</span>"
                                        }, user=frappe.session.user)

		for x in range(0,int(self.total_batches)):
			self.records = self.get_next_batch('Tally Stock Details')

			if not self.records:
				break

			self.current_batch = self.current_batch + len(self.records)

			for r in self.records:
				if not r.imported:
					frappe.publish_realtime("tally_import_progress", {
                                                "message": "Processing:"+rec.item_name+" Batch:"+rec.batch
                                        }, user=frappe.session.user)

					InternalImportStockDetails(value=r,od=self.open_date,bc=self.brand_category)

			frappe.publish_realtime("tally_import_progress", {
	                                         "message": """<span style="color:black;">Commiting Batch:"""+str(x)+"</span>"
                                        }, user=frappe.session.user)

			frappe.db.commit()



	def do_stock_items(self):
		self.current_batch = 0
		self.total_rows = self.get_stock_item_count('Tally Stock Items')
		self.total_batches = math.ceil(self.total_rows / self.total_batch_rows)
		frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;">Total Batches:"""+str(self.total_batches)+"</span>"
                                        }, user=frappe.session.user)

		for x in range(0,int(self.total_batches)):
			self.records = self.get_next_batch('Tally Stock Items')

			if not self.records:
				break

			self.current_batch = self.current_batch + len(self.records)

			for r in self.records:
				if r.closing_qty > 0:
					InternalImportStockItems(value=r,bc=self.brand_category)

			frappe.publish_realtime("tally_import_progress", {
                                                "message": """<span style="color:black;">Commiting Batch """+str(x)+"</span>"
                                        }, user=frappe.session.user)

			frappe.db.commit()


	def do_categories(self):
		categories = frappe.db.sql("""select distinct category from `tabTally Stock Items` order by category""",as_dict=1)
		for c in categories:
			InternalImportStockCategoryItems(value=c)

	def do_stock_groups(self):
		groups = frappe.db.sql("""select distinct stock_group from `tabTally Stock Items` order by stock_group""",as_dict=1)
		for g in groups:
			InternalImportStockGroupItems(value=g)			

	def do_warehouse(self):
		warehouse = frappe.db.sql("""select distinct warehouse from `tabTally Stock Details` order by warehouse""",as_dict=1)
		for w in warehouse:
			InternalImportGodownItems(value=w)			

@frappe.whitelist()
def process_import(open_date=None,brand=None):
	params = json.loads(frappe.form_dict.get("params") or '{}')

	if params.get("open_date"):
		open_date = params.get("open_date")

	if params.get("brand"):
		brand = params.get("brand")
		brand = brand.upper().rstrip(",").split(",")

	if not open_date:
		return

	TallyInternalStockImport(od=open_date,bc=brand)

	frappe.publish_realtime("tally_import_progress", {
                                                "message": "Import From Internal Table Successful"
                                        }, user=frappe.session.user)

	return {"messages": "Import Successful", "error": False}

