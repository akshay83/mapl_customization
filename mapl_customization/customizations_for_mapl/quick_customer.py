import frappe
import json
import requests
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
	customer_doc.relation_to = args["relation_to"] if "relation_to" in customer_keys else None
	customer_doc.relation_name = args["relation_name"] if "relation_name" in customer_keys else None
	customer_doc.primary_email = args["primary_email"] if "primary_email" in customer_keys else None
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
	address_doc.pincode = args["billing_pin"] if "billing_pin" in address_keys else None
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
	address_doc.pincode = args["shipping_pin"] if "shipping_pin" in address_keys else None
	address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
	address_doc.autoname()
	address_doc.save()

def validate_pin_with_state(doc, method):
	if not doc.gst_state:
		frappe.throw("""Please Select GST State""")

	if not doc.state:
		frappe.throw("""Please Select State""")

	if not doc.pincode:
		frappe.throw("""Please Select Pin Code""")

	try:
		req = requests.get(url = 'https://api.postalpincode.in/pincode/'+doc.pincode, timeout = 5)
		#DEBUG print '-----------------------VALIDATE STATE-----------------------'
		data = req.json()
		#DEBUG print data
		#DEBUG print '=========================STRATE=================='
		#DEBUG print data[0]["PostOffice"][0]
		if data[0]["Status"] != "Success":
			if (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles()):
				frappe.msgprint("""<div>Could Not Find Pin Code</div><div>Continuing for Now</div>""")
				return
			else:
				frappe.throw("""Could Not Find Pin Code""")

		pincode_state = data[0]["PostOffice"][0]["State"]

		if pincode_state.lower() != doc.state.lower():
			frappe.throw("""<div> Please Select Correct Pincode along with Correct State. </br>Current State:<B>'{0}'</B> GST State:<B>'{1}'</B> State By Pincode:<B>'{2}'</B></div>""".format(doc.state, doc.gst_state, pincode_state))


		if pincode_state.lower() != doc.gst_state.lower():
			frappe.throw("""<div> Please Select Correct Pincode along with Correct GST State. </br>Current State:<B>'{0}'</B> GST State:<B>'{1}'</B> State By Pincode:<B>'{2}'</B></div>""".format(doc.state, doc.gst_state, pincode_state))

	except requests.ConnectionError:
		frappe.msgprint("""Unable to Verify Pincode with GST State. Continuing for Now""")
	except requests.Timeout:
		frappe.msgprint("""Unable to Verify Pincode with GST State. Continuing for Now""")

def strDistance(s1, s2):
    if len(s1) > len(s2):
        s1, s2 = s2, s1

    distances = range(len(s1) + 1)
    for i2, c2 in enumerate(s2):
        distances_ = [i2+1]
        for i1, c1 in enumerate(s1):
            if c1 == c2:
                distances_.append(distances[i1])
            else:
                distances_.append(1 + min((distances[i1], distances[i1 + 1], distances_[-1])))
        distances = distances_
    return distances[-1]
