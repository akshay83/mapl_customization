import frappe

class TallyImportGodownItems:
    def __init__(self, value, ow):
        self.overwrite = ow
        self.process_node = value
        self.process()        

    def process(self):
        if not frappe.db.exists({"doctype":"Warehouse","warehouse_name": self.process_node['@NAME']}):
            godown_doc = frappe.get_doc({"doctype":"Warehouse","warehouse_name": self.process_node['@NAME']})
            godown_doc.insert(ignore_permissions=True)
