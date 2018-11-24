import frappe
import erpnext
from frappe.utils import cint, flt
from erpnext.stock import get_warehouse_account_map
from erpnext.accounts.utils import get_account_currency, get_fiscal_year
from erpnext.accounts.doctype.purchase_invoice.purchase_invoice import PurchaseInvoice
from erpnext.accounts.general_ledger import  merge_similar_entries

def alternative_gl_entries(self,gl_entries=None):
	cost_of_goods_sold_account = self.get_company_default("default_expense_account")
	stock_items = self.get_stock_items()
	sle_entry = None

	try:
		sle_entry = super(PurchaseInvoice, self).get_gl_entries()
	except Exception as e:
		return

	if not sle_entry:
		return

	total_debit = 0

	for item in self.get("items"):
		if self.update_stock and self.auto_accounting_for_stock and item.item_code in stock_items:
			account_currency = get_account_currency(item.expense_account)

			for s in sle_entry:
				total_debit = s.debit
				s.credit = 0
				s.credit_in_account_currency = 0
				s.against = cost_of_goods_sold_account


			gl_entries.append(
				self.get_gl_dict({
					"account": cost_of_goods_sold_account,
					"against": item.expense_account,
					"credit": total_debit,
					"remarks": self.get("remarks") or _("Accounting Entry for Stock"),
					"cost_center": item.cost_center,
					"project": item.project
				}, account_currency)
			)
		gl_entries = gl_entries + sle_entry
		break

	if gl_entries:
		return gl_entries
		#update_outstanding = "No" if (cint(self.is_paid) or self.write_off_account) else "Yes"

		#make_gl_entries(gl_entries,  cancel=(self.docstatus == 2),
		#	update_outstanding=update_outstanding, merge_entries=False)

	return None



def purchase_inv_make_gl_entries(self, gl_entries=None, repost_future_gle=True, from_repost=False):
	from erpnext.accounts.general_ledger import make_gl_entries

	if not gl_entries:
		gl_entries = self.get_gl_entries()

	# Not Required
	#if not self.grand_total:
	#	return

	if gl_entries:
		update_outstanding = "No" if (cint(self.is_paid) or self.write_off_account) else "Yes"

		make_gl_entries(gl_entries,  cancel=(self.docstatus == 2),
			update_outstanding=update_outstanding, merge_entries=False)

		if update_outstanding == "No":
			update_outstanding_amt(self.credit_to, "Supplier", self.supplier,
				self.doctype, self.return_against if cint(self.is_return) else self.name)

		if repost_future_gle and cint(self.update_stock) and self.auto_accounting_for_stock:
			from erpnext.controllers.stock_controller import update_gl_entries_after
			items, warehouses = self.get_items_and_warehouses()
			update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)

	elif self.docstatus == 2 and cint(self.update_stock) and self.auto_accounting_for_stock:
		delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)



def sales_inv_make_gl_entries(self, gl_entries=None, repost_future_gle=True, from_repost=False):
	print '---------------------------------------------------------------------'
	print 'Entered Monkey Patch Sales GL Entry'
	print '---------------------------------------------------------------------'
	auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)

	#Not Required as Sales Invoice can Be 0
	#if not self.grand_total:
	#	return

	if not gl_entries:
		gl_entries = self.get_gl_entries()

	if gl_entries:
		from erpnext.accounts.general_ledger import make_gl_entries

		# if POS and amount is written off, updating outstanding amt after posting all gl entries
		update_outstanding = "No" if (cint(self.is_pos) or self.write_off_account) else "Yes"

		make_gl_entries(gl_entries, cancel=(self.docstatus == 2),
			update_outstanding=update_outstanding, merge_entries=False)

		if update_outstanding == "No":
			from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
			update_outstanding_amt(self.debit_to, "Customer", self.customer,
				self.doctype, self.return_against if cint(self.is_return) else self.name)

		if repost_future_gle and cint(self.update_stock) \
			and cint(auto_accounting_for_stock):
				items, warehouses = self.get_items_and_warehouses()
				from erpnext.controllers.stock_controller import update_gl_entries_after
				update_gl_entries_after(self.posting_date, self.posting_time, warehouses, items)
	elif self.docstatus == 2 and cint(self.update_stock) \
		and cint(auto_accounting_for_stock):
			from erpnext.accounts.general_ledger import delete_gl_entries
			delete_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

def purchase_inv_get_gl_entries(self, warehouse_account=None):
	self.auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)
	self.stock_received_but_not_billed = self.get_company_default("stock_received_but_not_billed")
	self.expenses_included_in_valuation = self.get_company_default("expenses_included_in_valuation")
	self.negative_expense_to_be_booked = 0.0
	gl_entries = []


	self.make_supplier_gl_entry(gl_entries)
	self.make_item_gl_entries(gl_entries)
	self.make_tax_gl_entries(gl_entries)

	gl_entries = merge_similar_entries(gl_entries)

	self.make_payment_gl_entries(gl_entries)
	self.make_write_off_gl_entry(gl_entries)

	print '--------------------PATCH---------------------------'
	print gl_entries
	if not gl_entries and not self.grand_total:
		gl_entries = self.alternative_gl_entries(gl_entries)
		print '--------------------AFTER-----------------------------'
		print gl_entries
		#frappe.throw("""This was a Test""")

	return gl_entries
