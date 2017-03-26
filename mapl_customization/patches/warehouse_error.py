import frappe

# Problem Occured when Default Warehouse was set Under User Permissions
# target_warehouse was also being set under Sales Invoice Item and therefore 
# Wrong Stock Ledger Entries were being done.

def execute():
	frappe.db.sql("""update `tabSales Invoice Item` set target_warehouse=null""")

	si_list = frappe.db.sql("""select distinct si.name, si.docstatus
		from `tabSales Invoice` si where si.docstatus = 1 and si.update_stock=1
		order by si.posting_date asc""", as_dict=1)

	for si in si_list:
		si_doc = frappe.get_doc("Sales Invoice", si.name)
		si_doc.docstatus = 2
		si_doc.update_stock_ledger()
		frappe.db.sql("""delete from `tabGL Entry` 
				where voucher_type='Sales Invoice' and voucher_no=%s""", si.name)
			
		si_doc = frappe.get_doc("Sales Invoice", si.name)
		si_doc.docstatus = 1
		si_doc.update_stock_ledger()
		si_doc.make_gl_entries()
