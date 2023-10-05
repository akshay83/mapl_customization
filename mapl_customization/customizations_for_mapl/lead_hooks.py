import frappe
from erpnext.crm.doctype.lead.lead import Lead

def before_insert_lead(doc, method):
	if ("," in doc.mobile_no or len(doc.mobile_no.strip()) != 10):
		frappe.throw("Please Check Mobile No. Ensure that it is only one Number and of 10 Digits")
	if doc.mobile_no.startswith("+"):
		doc.mobile_no = doc.mobile_no[1:]
	if not doc.mobile_no.startswith("91"):
		doc.mobile_no = "91"+doc.mobile_no

def send_message(message, phone_list):
	from frappe.core.doctype.sms_settings.sms_settings import send_sms
	if not isinstance(phone_list, list):
		phone_list = str(phone_list).split(",")
	send_sms(phone_list, message)

def on_save_lead(doc, method):
	message = """Thankyou for Visiting CORAL ELECTRONICS.Hope you had a pleasant Experience.Should you have any further queries.Please call 08305181711"""
	send_message(message, str(doc.mobile_no))
	send_follow_link(str(doc.mobile_no))

def send_follow_link(phone_list):
	message = """Follow the Coral Electronics Indore channel on WhatsApp: https://whatsapp.com/channel/0029Va9IYPsD38CWwmDtvG1V""" 
	send_message(message, phone_list)

class CustomLead(Lead):
	#Do Not Create Address & Contact
	def before_insert(self):
		pass

	def update_links(self):
		# update address links
		if hasattr(self, 'address_doc'):
			self.address_doc.append("links", {
				"link_doctype": "Lead",
				"link_name": self.name,
				"link_title": self.lead_name
			})
			self.address_doc.save()

		# update contact links
		if hasattr(self, 'contact_doc'):
			self.contact_doc.append("links", {
				"link_doctype": "Lead",
				"link_name": self.name,
				"link_title": self.lead_name
			})
			self.contact_doc.save()		