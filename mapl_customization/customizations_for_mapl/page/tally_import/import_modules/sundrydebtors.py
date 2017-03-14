import frappe
import re

class TallyImportSundryDebtors:
	def __init__(self, value, ow, od):
		self.overwrite = ow
		self.process_node = value
		self.open_date = od
		self.process()

	def process(self):
		if self.process_node.has_key('OPENINGBALANCE') and self.process_node.has_key('PARENT'):
			if self.process_node['PARENT'].lower() != 'sundry debtors':
				return

			open_balance = float(self.process_node['OPENINGBALANCE'])
			if open_balance == 0:
				return

			self.make_customer()

	def make_customer(self):
		customer_doc = frappe.new_doc("Customer")
		customer_doc.customer_name = self.process_node["@NAME"]
		customer_doc.customer_group = 'Individual'
		customer_doc.territory = 'India'
		customer_doc.customer_type = 'Individual'

		customer_address = ''
		if (self.process_node.has_key('ADDRESS.LIST') and self.process_node['ADDRESS.LIST']):
			for address_line in self.process_node['ADDRESS.LIST']['ADDRESS']:
				if not (re.match('[\d/-]+$', address_line[:5])):
					if len(customer_address) > 0:
						customer_address = customer_address + ',' + address_line
					else:
						customer_address = customer_address + address_line
				else:
					for token in address_line.split(','):
						if (re.match('[\d/-]+$', token)):
							customer_doc.primary_contact_no = token
							break
						
		customer_doc.tax_id = self.process_node['VATTINNUMBER'] if self.process_node.has_key('VATTINNUMBER') else None
		customer_doc.company_name = frappe.defaults.get_user_default("Company")
		customer_doc.autoname()
		customer_doc.db_insert()
		if len(customer_address) > 0:
			self.enter_billing_address(customer_address, customer_doc)
		self.post_journal_entry(customer_doc)
		

	def enter_billing_address(self, args, customer):
		address_doc = frappe.new_doc("Address")
		address_doc.is_primary_address = 1
		address_doc.address_type = "Billing"
		address_doc.address_line1 = args
		city_index = args.rfind(',')
		address_doc.city = args[((city_index+1) if city_index > 0 else -10):]
		address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
		address_doc.autoname()
		address_doc.save()

	def post_journal_entry(self, customer):
		open_balance = float(self.process_node['OPENINGBALANCE'])

		jv = frappe.new_doc("Journal Entry");
		jv.voucher_type = 'Opening Entry'
		jv.company = frappe.defaults.get_user_default("Company")
		jv.posting_date = self.open_date
		jv.user_remark = 'Customer Opening Balance'

		td1 = jv.append("accounts")
		from erpnext.accounts.party import get_party_account
		td1.account = get_party_account('Customer', customer.name, jv.company)
		td1.party = customer.name
		td1.party_type = 'Customer'
		if open_balance < 0:
			td1.set("debit_in_account_currency", abs(open_balance))
		else:
			td1.set("credit_in_account_currency", abs(open_balance))

		td2 = jv.append("accounts")
		td2.account = frappe.get_value("Account",filters={"account_name": 'Temporary Opening'})
		if open_balance < 0:
			td2.set("credit_in_account_currency", abs(open_balance))
		else:
			td2.set("debit_in_account_currency", abs(open_balance))

		jv.save()
		jv.submit()

