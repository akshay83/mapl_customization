import frappe
from erpnext.stock.report.stock_and_account_value_comparison.stock_and_account_value_comparison import get_data
from erpnext import get_default_company
from frappe.utils import getdate
from erpnext.stock.stock_ledger import repost_future_sle
from erpnext.accounts.utils import update_gl_entries_after

def process():
    print ('Fetching Data')
    data = get_data(frappe._dict({'company':get_default_company(),'as_on_date':getdate()}))
    for d in data:
        print ('Processing Document:', d.voucher_type, d.voucher_no)
        repost_future_sle(voucher_type=d.voucher_type, voucher_no=d.voucher_no)        
        ref_doc = frappe.get_doc(d.voucher_type, d.voucher_no)
        items, warehouses = ref_doc.get_items_and_warehouses()
        update_gl_entries_after(ref_doc.posting_date, ref_doc.posting_time, warehouses, items, company=ref_doc.company)