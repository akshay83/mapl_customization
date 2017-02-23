import frappe

class TallyImportUnits:
    def __init__(self, value, ow):
        self.overwrite = ow
        self.process_node = value
        self.process()        

    def process(self):
	if not frappe.db.exists({"doctype":"UOM","uom_name": self.process_node['@NAME']}):
		uom_doc = frappe.new_doc('UOM')
		uom_doc.uom_name = self.process_node['@NAME']
		uom_doc.must_be_whole_number = 1 if self.process_node['ISSIMPLEUNIT'] == 'Yes' else 0
		uom_doc.save()
