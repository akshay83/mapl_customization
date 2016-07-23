import frappe

class TallyImportStockCategoryItems:
    def __init__(self, value, ow):
        self.overwrite = ow
        self.process_node = value
        self.process()        

    def process(self):
        print "----------------------------------------"
        print "DEBUG: PROCESSED: CATEGORY:"+self.process_node['@NAME']
        if not frappe.db.exists({"doctype":"Brand","brand": self.process_node['@NAME']}):
            doc = frappe.get_doc({"doctype":"Brand","brand": self.process_node['@NAME']})
            doc.insert(ignore_permissions=True)
            print "DEBUG: INSERTED: CATEGORY:"+self.process_node['@NAME']
        print "----------------------------------------"

