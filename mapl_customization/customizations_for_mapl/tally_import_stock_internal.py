import frappe
import math

class TallyInternalStockImport():
    def __init__(self):
        self.total_rows = 0
        self.total_batch_rows = 100.0
        self.current_batch = 0

    def get_stock_item_count(self):
        row_cnt = frappe.db.sql("select count(*) from `tabTally Stock Items`)
        return row_cnt

    def get_next_batch(self):
        return frappe.db.sql("""select * from `tabTally Stock Items` order by item_name 
                limit {current_batch} offset {batch_offset}""".format(**{
                        "current_batch" : int(self.total_batch_rows),
                        "batch_offset" : self.current_batch}), as_dict=1)

    def start_import_stock_items(self):
        self.records = self.get_next_batch()
        if not self.records:
            return

        self.current_batch = self.current_batch + self.records.length


    def start_process(self):
        self.do_categories()
        self.do_stock_groups()
        frappe.commit()
        self.total_rows = self.get_stock_item_count()
        self.total_batches = math.ceil(self.total_rows / self.total_batch_rows)


    def do_categories(self):
        categories = frappe.db.sql("""select dictinct category from `tabTally Stock Items` order by category""",as_dict=1)
        for c in categories:
            if not frappe.db.exists({"doctype":"Brand","brand": c.category}):
                doc = frappe.get_doc({"doctype":"Brand","brand": c.category})
                doc.insert(ignore_permissions=True)

    def do_stock_groups(self):
        groups = frappe.db.sql("""select dictinct stock_group from `tabTally Stock Items` order by stock_group""",as_dict=1)
        for g in groups:
    		if not frappe.db.exists({"doctype":"Item Group","item_group_name": g.stock_group}):
	    		doc = frappe.get_doc({"doctype":"Item Group","item_group_name": g.stock_group})
	    		doc.parent_item_group = 'All Item Groups'
        		doc.is_group = 1
        		doc.insert(ignore_permissions=True)


