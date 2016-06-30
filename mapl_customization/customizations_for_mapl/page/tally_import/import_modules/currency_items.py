import frappe

class TallyImportCurrencyItems:
    def __init__(self, value, ow):
        self.currency_table_map = { 'MAILINGNAME' : 'name',
                    'DECIMALSYMBOL' : 'fraction',
                    'ORIGINALNAME' : 'symbol'
                   }
        self.overwrite = ow
        self.process_node = value
        self.process()        

    def process(self):
        print "----------RESULT----------"
        print "PROCESSED:" + self.process_node['MAILINGNAME'] + " +++++ OW: " + str(self.overwrite)
        print "----------RESULT END----------"
        currency_doc = frappe.db.exists('Currency', self.process_node['MAILINGNAME'])
        if currency_doc == False:
            currency_doc = frappe.get_doc('Currency', self.process_node['MAILINGNAME'])
            currency_doc.fraction = process_node['DECIMALSYMBOL']
            currency_doc.symbol = process_node['ORIGINALNAME']            
            currency_doc.insert(ignore_permissions=True)
