# -*- coding: utf-8 -*-
# Copyright (c) 2015, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class ItemTaxesTemplate(Document):
	def validate(self):
		if not self.is_default and not frappe.get_all(self.doctype, filters = {"is_default":1}):
			self.is_default = 1

		if self.is_default == 1:
			frappe.db.sql("""update `tab{0}` set is_default=0
				where ifnull(is_default,0) = 1 and name != %s and company = %s""".format(self.doctype),
				(self.name, self.company))

