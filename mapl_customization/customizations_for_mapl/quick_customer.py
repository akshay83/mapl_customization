import frappe
import json
import requests
import re
from erpnext.regional.india.utils import validate_gstin_for_india
from frappe.utils import cint, getdate, today
from six import string_types

@frappe.whitelist()
def do_quick_entry(args):
	if isinstance(args, string_types):
		args = json.loads(args)

	if not args:
		frappe.throw("Please specify Arguments")

	customer = make_customer(args)
	contact = make_contact(args, customer)
	billing_add_name = enter_billing_address (args,customer)
	enter_shipping_address (args, customer)
	customer.db_set('customer_primary_contact', contact.name)
	customer.db_set('mobile_no', customer.primary_contact_no)
	customer.db_set('email_id', args.get("primary_email"))
	customer.db_set('customer_primary_address', billing_add_name)
	return customer

def validate(args):
	if not args.get("customer_type"):
		frappe.throw("Need Customer Type")

	if not args.get("customer_group"):
		frappe.throw("Need Customer Group")

	if not args.get("customer_name"):
		frappe.throw("Need Customer Name")

	if not args.get("territory"):
		frappe.throw("Need Customer Territory")

	if not args.get("primary_contact_no"):
		frappe.throw("Need Primary Contact No")

	if not args.get("billing_address_1"):
		frappe.throw("Need Billing Address")

	if not args.get("billing_city"):
		frappe.throw("Need Billing City")

	if args.get("primary_email"):
		if not is_valid_email(args.get("primary_email")):
			frappe.throw("Invalid Email Address")

	validate_pin_with_state(frappe._dict({
		"gst_state": args.get("billing_gst_state"),
		"state": args.get("billing_state"),
		"pincode": args.get("billing_pin")
	}), None, raise_error=True)
	if args.get("shipping_address_1") or args.get("shipping_address_2"):
		validate_pin_with_state(frappe._dict({
			"gst_state": args.get("shipping_gst_state"),
			"state": args.get("shipping_state"),
			"pincode": args.get("shipping_pin")
		}), None, raise_error=True)

	validate_gstid(args)

def is_valid_email(email):
	invalid_strings = ['nomail@nomail.com', 'no@no.com', 'nomail@no.com', 'no@nomail.com']
	if len(email) > 10 and email.lower() not in invalid_strings:
		if email.lower().startswith('nomail@'):
			return False
		return bool(re.match("^.+@(\[?)[a-zA-Z0-9-.]+.([a-zA-Z]{2,3}|[0-9]{1,3})(]?)$", email))
	return False

def validate_gstid(args):
	customer_keys = args.keys()

	if args.get("billing_gstid"):
		if not args.get("billing_gst_state"):
			frappe.throw("Select Billing GST State")

		validate_gstin_for_india({
				"gstin":args.get("billing_gstid"),
				"gst_state":args.get("billing_gst_state")
			},None)

	if args.get("shipping_address_1"):
		if args.get("shipping_gstid"):
			if not args.get("shipping_gst_state"):
				frappe.throw("Select Shipping GST State")

			validate_gstin_for_india({
					"gstin":args.get("shipping_gstid"),
					"gst_state":args.get("shipping_gst_state")
				},None)


def make_customer(args):
	validate(args)
	customer_keys = args.keys()
	customer_doc = frappe.new_doc("Customer")
	customer_doc.salutation = args.get("salutation")
	customer_doc.customer_name = args.get("customer_name").strip()
	customer_doc.customer_group = args.get("customer_group")
	customer_doc.territory = args.get("territory")
	customer_doc.customer_type = args.get("customer_type")
	customer_doc.tax_id = args.get("tax_id")
	customer_doc.pan = args.get("pan_no")
	customer_doc.aadhar_card_no = args.get("aadhar_card_no")
	customer_doc.company_name = args.get("company_name")
	customer_doc.vehicle_no = args.get("vehicle_no")
	customer_doc.relation_to = args.get("relation_to")
	customer_doc.relation_name = args.get("relation_name")
	customer_doc.primary_contact_no = args.get("primary_contact_no") #To Validate In Before Insert Hook
	customer_doc.secondary_contact_no = args.get("secondary_contact_no") #To Validate In Before Insert Hook
	validate_contact_nos(customer_doc)
	customer_doc.save()
	return customer_doc

def make_contact(args, customer):
	names = args.get("customer_name").strip().split(' ')
	args["primary_contact_no"] = args["primary_contact_no"].replace("-","").replace("/",",").replace(" ","").strip(",/\\ ")
	if args.get("secondary_contact_no"):
		args["secondary_contact_no"] = args["secondary_contact_no"].replace("-","").replace("/",",").replace(" ","").strip(",/\\ ")

	contact = frappe.get_doc({
		'doctype': 'Contact',
		'first_name': ' '.join(names[0:len(names)-2]) if len(names) >= 3 else names[0],
		'last_name' : names[-1],
		'middle_name' : names[-2] if len(names) >= 3 else None,
		'is_primary_contact': 1,
		'links': [{
			'link_doctype': 'Customer',
			'link_name': customer.name
		}]
	})
	if args.get('primary_email'):
		contact.add_email(args.get('primary_email'), is_primary=True)
	if args.get('primary_contact_no'):
		contact.add_phone(args.get('primary_contact_no'), is_primary_mobile_no=True)
	if args.get('secondary_contact_no'):
		contact.add_phone(args.get('secondary_contact_no'), is_primary_mobile_no=False)
	contact.insert()

	return contact

def enter_billing_address(args, customer):
	address_keys = args.keys()
	address_doc = frappe.new_doc("Address")
	address_doc.is_primary_address = 1
	address_doc.address_type = "Billing"
	address_doc.address_line1 = args.get("billing_address_1")
	address_doc.address_line2 = args.get("billing_address_2")
	address_doc.city = args.get("billing_city")
	address_doc.state = args.get("billing_state")
	address_doc.country = args.get("billing_country")
	address_doc.fax = args.get("billing_fax")
	address_doc.phone = args.get("billing_phone")
	address_doc.email_id = args.get("billing_email_id")
	address_doc.gstin = args.get("billing_gst_id")
	address_doc.gst_state = args.get("billing_gst_state")
	address_doc.pincode = args.get("billing_pin")
	address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
	address_doc.autoname()
	address_doc.save()
	return address_doc.name

def enter_shipping_address(args, customer):
	address_keys = args.keys()
	if not args.get("shipping_address_1") and not args.get("shipping_address_2"):
		return

	address_doc = frappe.new_doc("Address")
	address_doc.is_shipping_address = 1 if "shipping_preferred" in address_keys else 0
	address_doc.address_type = "Shipping"
	address_doc.address_line1 = args.get("shipping_address_1")
	address_doc.address_line2 = args.get("shipping_address_2")
	address_doc.city = args.get("shipping_city")
	address_doc.state = args.get("shipping_state")
	address_doc.country = args.get("shipping_country")
	address_doc.fax = args.get("shipping_fax")
	address_doc.phone = args.get("shipping_phone")
	address_doc.email_id = args.get("shipping_email_id")
	address_doc.gstin = args.get("shipping_gst_id")
	address_doc.gst_state = args.get("shipping_gst_state")
	address_doc.pincode = args.get("shipping_pin")
	address_doc.append('links', dict(link_doctype='Customer', link_name=customer.name))
	address_doc.autoname()
	address_doc.save()

def validate_address(doc, method):
	if doc.get('ignore_validate_hook'):
		return	
	validate_pin_with_state(doc, method)
	validate_address_creation(doc, method)

def validate_pin_with_state(doc, method, raise_error=False):
	if not doc.gst_state:
		frappe.throw("""Please Select GST State""")

	if not doc.state:
		frappe.throw("""Please Select State""")

	if not doc.pincode:
		frappe.throw("""Please Select Pin Code""")

	try:
		req = requests.get(url = 'https://api.postalpincode.in/pincode/'+doc.pincode, timeout = 5, verify=False)
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

	except (requests.ConnectionError, requests.Timeout, ValueError):
		if raise_error:
			frappe.throw("""Unable to Verify Pincode with GST State""")
		else:
			frappe.msgprint("""Unable to Verify Pincode with GST State. Continuing for Now""")

def validate_address_creation(doc, method):
	if doc.is_new():
		return

	if (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles() or "Accounts Manager" in frappe.get_roles()):
		return

	existing = frappe.get_doc("Address", doc.name)

	if existing.address_line1.lower() == doc.address_line1.lower() \
		and existing.city.lower() == doc.city.lower():
		if (not existing.address_line2 and not doc.address_line2) \
			and (not existing.gstin and not doc.gstin):
				return

		if  (existing.address_line2 and doc.address_line2):
			if (existing.gstin and doc.gstin):
				if existing.address_line2.lower() == doc.address_line2.lower() \
					and existing.gstin.lower() == doc.gstin.lower():
					return
			else:
				if existing.address_line2.lower() == doc.address_line2.lower():
					return

		if (existing.gstin and doc.gstin):
			if existing.gstin.lower() == doc.gstin.lower():
				return

	check_creation_date(existing, "Address")
	check_freeze_date(existing, "Address")

def check_creation_date(existing, doc):
	if abs((getdate(today())-getdate(existing.creation)).days) >= 15:
		frappe.throw("""Change of {0} not Allowed""".format(doc))

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

def strip_contact_nos(primary_contact_no, secondary_contact_no):
	pcn = primary_contact_no.replace(" ", "")
	if pcn[-1:] in ("/", ","):
		pcn = pcn[:-1]
	pcn = pcn.replace("/", ",")
	pcn = pcn.replace("-", "")
	pcn = pcn.replace(",", "|")

	scn = None
	if secondary_contact_no:
		scn = secondary_contact_no.replace(" ", "")
		if scn[:1] in (",", "/"):
			scn = scn[1:]
		scn = scn.replace("/", ",")
		scn = scn.replace("-", "")
		scn = scn.replace(",", "|")

	return pcn, scn

def get_all_contact_nos(party):
	query = """
		select
		  phone_numbers.phone
		from `tabCustomer` cust,
		  (select
		    link.link_name,
		    phone.phone,
		    phone.is_primary_mobile_no
		   from `tabContact` contact,
		    `tabContact Phone` phone,
		    `tabDynamic Link` link
		   where phone.parent = contact.name
		    and link.link_doctype = 'Customer'
		    and link.parent = contact.name) as phone_numbers
		where phone_numbers.link_name = cust.name
		  and cust.name = '{0}'
		""".format(party)

	return frappe.db.sql(query, as_dict=1)

def validate_customer(doc, method):
	#if doc.customer_group == 'Web User':
	#	return
	if doc.get('ignore_validate_hook'):
		return

	doc.customer_name = doc.customer_name.strip()
	if len(doc.customer_name) > 3:
		if (doc.customer_name.lower()[:3] in ("dr ","mr ","ms ","dr.","mr.","ms.") or \
			doc.customer_name.lower()[:4] in ("m/s ", "mrs ","m/s.","mrs.") or \
			doc.customer_name.lower()[:5] in ("miss ","miss.")):
			frappe.throw("Please Use Salutation instead of Prefixing Name with Mr, Mrs, Dr etc.")

		if any(item in doc.customer_name.lower() for item in ["s/o","d/o","w/o","s\o","d\o","w\o"]):
			frappe.throw("Please Use Relation To and Relation Name Fields instead of S/o, D/o etc")

		if any(item in doc.customer_name.lower() for item in ["c/o","c\o"]):
			frappe.throw("Please Use Company Name instead of C/o")

	#validate_duplicate_customer(doc, method)
	validate_customer_creation(doc, method)

def validate_contact_nos(doc):
	if re.findall('[^0-9,/-]', doc.primary_contact_no.replace(" ", "")):
		frappe.throw("""Check Primary Contact No""")

	if doc.secondary_contact_no and re.findall('[^0-9,/-]', doc.secondary_contact_no.replace(" ", "")):
		frappe.throw("""Check Secondary Contact No""")

def validate_customer_creation(doc, method):
	if doc.is_new():
		return

	if (frappe.session.user == "Administrator" or "System Manager" in frappe.get_roles() or "Accounts Manager" in frappe.get_roles()):
		return

	existing = frappe.get_doc("Customer", doc.name)

	if existing.customer_name.lower() == doc.customer_name.lower():
		return

	check_creation_date(existing, "Name")
	check_freeze_date(existing, "Customer")

def check_freeze_date(existing, doc):
	freeze_date = frappe.db.get_single_value("Accounts Settings", "acc_frozen_upto")
	if freeze_date and getdate(existing.creation)<getdate(freeze_date):
		throw("Accounts have been freezed till {0}, {1} cannot be Modified as it was created before this date".format(freeze_date, doc))

def validate_customer_before_save(doc, method):
	if doc.get('ignore_validate_hook'):
		return
	#if doc.customer_group == 'Web User':
	#	if not doc.primary_contact_no:
	#		return

	doc.customer_name = doc.customer_name.strip()
	if not hasattr(doc,"primary_contact_no"):
		return
	pcn, scn = strip_contact_nos(doc.primary_contact_no, doc.secondary_contact_no)

	query = """
		select
		  cust.name,
		  cust.customer_name,
		  phone_numbers.phone,
		  phone_numbers.is_primary_mobile_no
		from `tabCustomer` cust,
		  (select
		    link.link_name,
		    phone.phone,
		    phone.is_primary_mobile_no
		   from `tabContact` contact,
		    `tabContact Phone` phone,
		    `tabDynamic Link` link
		   where phone.parent = contact.name
		    and link.link_doctype = 'Customer'
		    and link.parent = contact.name) as phone_numbers
		where soundex(customer_name) = soundex('{0}')
		  and phone_numbers.link_name = cust.name
		  and ( {1} )
		""".format(doc.customer_name,
			"""replace('"""+pcn+"""',"-","") in (phone_numbers.phone) or replace('"""+scn+"""',"-","") in (phone_numbers.phone)""" \
					if scn else """replace('"""+pcn+"""',"-","") in (phone_numbers.phone)""")

	count = frappe.db.sql(query, as_dict=1)

	if count and len(count) > 0:
		name_list = """<div style="display:flex;flex-direction:column;">
				<div style="display:flex;flex-direction:row;padding-bottom:3px;padding-top:3px;">"""
		for c in count:
			record = """<div style="flex:1;padding-right:3px;">{0}</div>
				<div style="flex:1;padding-right:3px;">{1}</div>
				<div style="flex:1;padding-right:3px;">{2}</div>""".format(c.name,c.customer_name,c.phone)
			name_list = name_list+record
			name_list = name_list+"""</div><div style="display:flex;flex-direction:row;padding-bottom:3px;padding-top:3px;">"""
		name_list = name_list+"</div></div>"
		frappe.throw("""<div>Customer Exists, Please use a different Address if Required</div>"""+name_list)
