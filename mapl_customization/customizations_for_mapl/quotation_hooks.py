import frappe

def quotation_before_validate(doc, method):
    for i in doc.items:
        if not i.get('conversion_factor') or i.get('conversion_factor')==0:
            i.conversion_factor = 1