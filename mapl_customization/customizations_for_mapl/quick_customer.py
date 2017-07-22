import frappe
import json
from erpnext.regional.india.utils import validate_gstin_for_india

@frappe.whitelist()
def do_quick_entry(args):
	if isinstance(args, basestring):
		args = json.loads(args)

	if not args:
		frappe.throw("Please specify Arguments")

	customer = make_customer(args)
	enter_billing_address (args,customer)
	enter_shipping_address (args, customer)
	return customer

def validate(args):
	customer_keys = args.keys()

	if "customer_type" not in customer_keys:
		frappe.throw("Need Customer Type")

	if "customer_group" not in customer_keys:
		frappe.throw("Need Customer Group")

	if "customer_name" not in customer_keys:
		frappe.throw("Need Customer Name")

	if "territory" not in customer_keys:
		frappe.throw("Need Customer Territory")

	if "primary_contact_no" not in customer_keys:
		frappe.throw("Need Primary Contact No")

	if "billing_address_1" not in customer_keys:
		frappe.throw("Need Billing Address")

	if "billing_city" not in customer_keys:
		frappe.throw("Need Billing City")

	validate_gstid(args)


def validate_gstid(args):
	customer_keys = args.keys()

	if "billing_gstid" in customer_keys:
		if "billing_gst_state" not in customer_keys:
			frappe.throw("Select Billing GST State")

		validate_gstin_for_india({
				"gstin":args["billing_gstid"], 
				"gst_state":args["billing_gst_state"]
			},None)

	if "shipping_address_1" in customer_keys:
		if "shipping_gstid" in customer_keys:
			if "shipping_gst_state" not in customer_keys:
				frappe.throw("Select Shipping GST State")

			validate_gstin_for_india({
					"gstin":args["shipping_gstid"], 
					"gst_state":args["shipping_gst_state"]
				},None)


def make_customer(args):
	validate(args)
	customer_keys = args.keys()
	customer_doc = frappe.new_doc("Customer")
	customer_doc.salutation = args["salutation"] if "salutation" in customer_keys else None
	customer_doc.customer_name = args["customer_name"]
	customer_doc.customer_group = args["customer_group"]
	customer_doc.territory = args["territory"]
	customer_doc.customer_type = args["customer_type"]
	customer_doc.tax_id = args["tax_id"] if "tax_id" in customer_keys else None
	customer_doc.pan_no = args["pan_no"] if "pan_no" in customer_keys else None
	customer_doc.primary_contact_no = args["primary_contact_no"]
	customer_doc.secondary_contact_no = args["secondary_contact_no"] if "secondary_contact_no" in customer_keys else None
	customer_doc.company_name = args["company_name"] if "company_name" in customer_keys else None
	customer_doc.vehicle_no = args["vehicle_no"] if "vehicle_no" in customer_keys else None
	customer_doc.save()
	return customer_doc

def enter_billing_address(args, customer):
	address_keys = args.keys()
	address_doc = frappe.new_doc("Address")
	address_doc.is_primary_address = 1
	address_doc.address_type = "Billing"
	address_doc.address_line1 = args["billing_address_1"]
	address_doc.address_line2 = args["billing_address_2"] if "billing_address_2" in address_keys else None
	address_doc.city = args["billing_city"]
	address_doc.state = args["billing_state"] if "billing_state" in address_keys else None
	address_doc.country = args["billing_country"] if "billing_country" in address_keys else None
	address_doc.fax = args["billing_fax"] if "billing_fax" in address_keys else None
	address_doc.phone = args["billing_phone"] if "billing_phone" in address_keys else None
	address_doc.email_id = args["billing_email_id"] if "billing_email_id" in address_keys else None
	address_doc.gstin = args["billing_gst_id"] if "billing_gst_id" in address_keys else None
	address_doc.gst_state = args["billing_gst_state"] if "billing_gst_state" in address_keys else None
	address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
	address_doc.autoname()
	address_doc.save()

def enter_shipping_address(args, customer):
	address_keys = args.keys()
	if ("shipping_address_1" not in address_keys) and ("shipping_address_2" not in address_keys):
		return

	address_doc = frappe.new_doc("Address")
	address_doc.is_shipping_address = 1 if "shipping_preferred" in address_keys else 0
	address_doc.address_type = "Shipping"
	address_doc.address_line1 = args["shipping_address_1"] if "shipping_address_1" in address_keys else None
	address_doc.address_line2 = args["shipping_address_2"] if "shipping_address_2" in address_keys else None
	address_doc.city = args["shipping_city"] if "shipping_city" in address_keys else None
	address_doc.state = args["shipping_state"] if "shipping_state" in address_keys else None
	address_doc.country = args["shipping_country"] if "shipping_country" in address_keys else None
	address_doc.fax = args["shipping_fax"] if "shipping_fax" in address_keys else None
	address_doc.phone = args["shipping_phone"] if "shipping_phone" in address_keys else None
	address_doc.email_id = args["shipping_email_id"] if "shipping_email_id" in address_keys else None
	address_doc.gstin = args["shipping_gst_id"] if "shipping_gst_id" in address_keys else None
	address_doc.gst_state = args["shipping_gst_state"] if "shipping_gst_state" in address_keys else None
	address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
	address_doc.autoname()
	address_doc.save()
