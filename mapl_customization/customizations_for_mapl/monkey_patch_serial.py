from __future__ import unicode_literals
import frappe
import erpnext

from frappe.utils import cint, cstr, flt, add_days, nowdate, getdate
from frappe import _, ValidationError
from erpnext.stock.doctype.serial_no.serial_no import get_serial_nos

from erpnext.stock.doctype.serial_no.serial_no import  SerialNoCannotCreateDirectError,SerialNoCannotCannotChangeError,\
	SerialNoNotRequiredError,SerialNoRequiredError,SerialNoQtyError,SerialNoItemError,SerialNoWarehouseError,\
	SerialNoNotExistsError,SerialNoDuplicateError

def validate_serial_no(sle, item_det):
	if item_det.has_serial_no==0:
		if sle.serial_no:
			frappe.throw(_("Item {0} is not setup for Serial Nos. Column must be blank").format(sle.item_code),
				SerialNoNotRequiredError)
	else:
		if sle.serial_no:
			serial_nos = get_serial_nos(sle.serial_no)
			if cint(sle.actual_qty) != flt(sle.actual_qty):
				frappe.throw(_("Serial No {0} quantity {1} cannot be a fraction").format(sle.item_code, sle.actual_qty))

			if len(serial_nos) and len(serial_nos) != abs(cint(sle.actual_qty)):
				frappe.throw(_("{0} Serial Numbers required for Item {1}. You have provided {2}.").format(sle.actual_qty, sle.item_code, len(serial_nos)),
					SerialNoQtyError)

			if len(serial_nos) != len(set(serial_nos)):
				frappe.throw(_("Duplicate Serial No entered for Item {0}").format(sle.item_code), SerialNoDuplicateError)

			for serial_no in serial_nos:
				if frappe.db.exists("Serial No", serial_no):
					sr = frappe.get_doc("Serial No", serial_no)

					if sr.item_code!=sle.item_code:
						if not allow_serial_nos_with_different_item(serial_no, sle):
							frappe.throw(_("Serial No {0} does not belong to Item {1}").format(serial_no,
								sle.item_code), SerialNoItemError)

					#Following Code Disabled in Monkey Patch as It Creates Problem in Updating Purchase Invoice
					#After Submittion
					#if sr.warehouse and sle.actual_qty > 0:
					#	frappe.throw(_("Serial No {0} has already been received").format(serial_no),
					#		SerialNoDuplicateError)

					if sle.actual_qty < 0:
						#Following Code Disabled in Monkey Patch as It Creates Problem in Updating Purchase Invoice
						#After Submittion
						#if sr.warehouse!=sle.warehouse:
						#	frappe.throw(_("Serial No {0} does not belong to Warehouse {1}").format(serial_no,
						#		sle.warehouse), SerialNoWarehouseError)

						if sle.voucher_type in ("Delivery Note", "Sales Invoice") \
							and sle.is_cancelled=="No" and not sr.warehouse:
								frappe.throw(_("Serial No {0} does not belong to any Warehouse")
									.format(serial_no), SerialNoWarehouseError)

				elif sle.actual_qty < 0:
					# transfer out
					frappe.throw(_("Serial No {0} not in stock").format(serial_no), SerialNoNotExistsError)
		elif sle.actual_qty < 0 or not item_det.serial_no_series:
			frappe.throw(_("Serial Nos Required for Serialized Item {0}").format(sle.item_code),
				SerialNoRequiredError)

def set_purchase_details(self, purchase_sle):
	if purchase_sle:
		self.purchase_document_type = purchase_sle.voucher_type
		self.purchase_document_no = purchase_sle.voucher_no
		self.purchase_date = purchase_sle.posting_date
		self.purchase_time = purchase_sle.posting_time

		if not self.purchase_rate:
			self.purchase_rate = purchase_sle.incoming_rate

		if purchase_sle.voucher_type == "Purchase Receipt":
			self.supplier, self.supplier_name = \
				frappe.db.get_value("Purchase Receipt", purchase_sle.voucher_no,
						["supplier", "supplier_name"])
	else:
		for fieldname in ("purchase_document_type", "purchase_document_no",
			"purchase_date", "purchase_time", "purchase_rate", "supplier", "supplier_name"):
				self.set(fieldname, None)
