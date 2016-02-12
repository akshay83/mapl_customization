# -*- coding: utf-8 -*-
# Copyright (c) 2015, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class Payments(Document):
	def validate(self):
		if (self.payment_amount <= 0):
			frappe.throw("Check Payment Amount");

		from frappe.utils import money_in_words
		self.in_words = money_in_words(self.payment_amount);

	def on_submit(self):
		self.post_journal_entry()

	def on_cancel(self):
		if (self.journal_reference):
			jv = frappe.get_doc("Journal Entry",self.journal_reference)
			jv.receipt_link = None
			jv.db_update();
			jv.cancel()

	def on_trash(self):
		if (self.journal_reference):
			jv = frappe.get_doc("Journal Entry",self.journal_reference)
			jv.receipt_link = None
			jv.db_update();			
			jv.delete()

	def post_journal_entry(self):
		jv = frappe.new_doc("Journal Entry");
		jv.voucher_type = 'Journal Entry'
		jv.company = self.company
		jv.posting_date = self.payment_date
		jv.user_remark = 'Formal Payment'
		jv.payment_link = self.name

		td1 = jv.append("accounts");
		td1.account = self.party_account
		td1.party = self.party
		td1.party_type = self.party_type
		td1.set("debit_in_account_currency", self.payment_amount)
		td1.set("is_advance", self.is_advance)

		td2 = jv.append("accounts")
		td2.account = self.payment_account
		td2.set('credit_in_account_currency', self.payment_amount)
		td2.set('is_advance', self.is_advance)

		jv.insert()
		jv.submit()

		self.journal_reference = jv.name
		self.db_update()
