# -*- coding: utf-8 -*-
# Copyright (c) 2015, Akshay Mehta and contributors
# For license information, please see license.txt

from __future__ import unicode_literals
import frappe
from frappe.model.document import Document

class StockProblem(Document):
	def on_update(self):
		if (not self.serial_no):
			return

		serial_doc = frappe.get_doc("Serial No", self.serial_no)
		serial_doc.via_stock_ledger = True
		if (self.status == "Open"):
			self.move_to_temporary_warehouse(serial_doc)
			serial_doc.add_comment("Comment", "Damaged/Problematic Set")
		else:
			self.move_to_main_warehouse(serial_doc)
			serial_doc.add_comment("Comment", "Problem Resolved")

	def on_trash(self):
		if (self.serial_no):
			serial_doc = frappe.get_doc("Serial No", self.serial_no)
			self.move_to_main_warehouse(serial_doc)
			serial_doc.add_comment("Commant", "Problem Not Found")

	def move_to_temporary_warehouse(self,serial_doc):
		serial_doc.temporary_warehouse = serial_doc.warehouse
		serial_doc.warehouse = None
		serial_doc.problem = self.name
		serial_doc.save()

	def move_to_main_warehouse(self,serial_doc):
		serial_doc.warehouse = serial_doc.temporary_warehouse
		serial_doc.temporary_warehouse = None
		serial_doc.problem = None
		serial_doc.save()
