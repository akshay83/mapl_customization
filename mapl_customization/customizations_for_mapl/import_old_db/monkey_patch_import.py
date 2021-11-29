import erpnext
from frappe.utils import cint, flt
from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries, process_gl_map

def si_make_gl_entries(self, gl_entries=None, from_repost=False):
	#monkey comment out as imported globally
	#from erpnext.accounts.general_ledger import make_gl_entries, make_reverse_gl_entries

	auto_accounting_for_stock = erpnext.is_perpetual_inventory_enabled(self.company)
	if not gl_entries:
		gl_entries = self.get_gl_entries()

	if gl_entries:
		# if POS and amount is written off, updating outstanding amt after posting all gl entries
		update_outstanding = "No" if (cint(self.is_pos) or self.write_off_account or
			cint(self.redeem_loyalty_points)) else "Yes"

		if self.docstatus == 1:
            #monkey-here
			make_gl_entries(gl_entries, update_outstanding=update_outstanding, merge_entries=False, from_repost=True)
		elif self.docstatus == 2:
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

		if update_outstanding == "No":
			from erpnext.accounts.doctype.gl_entry.gl_entry import update_outstanding_amt
			update_outstanding_amt(self.debit_to, "Customer", self.customer,
				self.doctype, self.return_against if cint(self.is_return) and self.return_against else self.name)

	elif self.docstatus == 2 and cint(self.update_stock) \
		and cint(auto_accounting_for_stock):
			make_reverse_gl_entries(voucher_type=self.doctype, voucher_no=self.name)

def pe_make_gl_entries(self, cancel=0, adv_adj=0):
	if self.payment_type in ("Receive", "Pay") and not self.get("party_account_field"):
		self.setup_party_account_field()

	gl_entries = []
	self.add_party_gl_entries(gl_entries)
	self.add_bank_gl_entries(gl_entries)
	self.add_deductions_gl_entries(gl_entries)
	self.add_tax_gl_entries(gl_entries)

	gl_entries = process_gl_map(gl_entries)
	#monkey-here
	make_gl_entries(gl_entries, cancel=cancel, adv_adj=adv_adj, from_repost=True)

def jv_make_gl_entries(self, cancel=0, adv_adj=0):
	#monkey comment out as imported globally
	#from erpnext.accounts.general_ledger import make_gl_entries

	gl_map = []
	for d in self.get("accounts"):
		if d.debit or d.credit:
			r = [d.user_remark, self.remark]
			r = [x for x in r if x]
			remarks = "\n".join(r)

			gl_map.append(
				self.get_gl_dict({
					"account": d.account,
					"party_type": d.party_type,
					"due_date": self.due_date,
					"party": d.party,
					"against": d.against_account,
					"debit": flt(d.debit, d.precision("debit")),
					"credit": flt(d.credit, d.precision("credit")),
					"account_currency": d.account_currency,
					"debit_in_account_currency": flt(d.debit_in_account_currency, d.precision("debit_in_account_currency")),
					"credit_in_account_currency": flt(d.credit_in_account_currency, d.precision("credit_in_account_currency")),
					"against_voucher_type": d.reference_type,
					"against_voucher": d.reference_name,
					"remarks": remarks,
					"voucher_detail_no": d.reference_detail_no,
					"cost_center": d.cost_center,
					"project": d.project,
					"finance_book": self.finance_book
				}, item=d)
			)

	if self.voucher_type in ('Deferred Revenue', 'Deferred Expense'):
		update_outstanding = 'No'
	else:
		update_outstanding = 'Yes'

	if gl_map:
        #monkey here
		make_gl_entries(gl_map, cancel=cancel, adv_adj=adv_adj, update_outstanding=update_outstanding,from_repost=True)

def monkey_patch_journal_entry_temporarily():
    from erpnext.accounts.doctype.journal_entry.journal_entry import JournalEntry
    JournalEntry.make_gl_entries = jv_make_gl_entries            

def monkey_patch_sales_invoice_temporarily():
    from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
    SalesInvoice.make_gl_entries = si_make_gl_entries                

def monkey_patch_payment_entry_temporarily():
    from erpnext.accounts.doctype.payment_entry.payment_entry import PaymentEntry
    PaymentEntry.make_gl_entries = pe_make_gl_entries                	