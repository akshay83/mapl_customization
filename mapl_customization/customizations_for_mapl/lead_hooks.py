import frappe
from erpnext.crm.doctype.lead.lead import Lead

def before_insert_lead(doc, method):
	if ("," in doc.mobile_no or len(doc.mobile_no.strip()) != 10):
		frappe.throw("Please Check Mobile No. Ensure that it is only one Number and of 10 Digits")

def on_save_lead(doc, method):
	from frappe.core.doctype.sms_settings.sms_settings import send_sms
	message = """Thankyou for Visiting CORAL ELECTRONICS.Hope you had a pleasant Experience.Should you have any further queries.Please call 08305181711"""
	receiver_list = []
	receiver_list.append(str(doc.mobile_no))
	send_sms(receiver_list, message)

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