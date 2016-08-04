import frappe

from frappe import _
from frappe.core.doctype.doctype.doctype import validate_fields_for_doctype
from frappe.custom.doctype.customize_form.customize_form import docfield_properties

def save_customization(self):
	if not self.doc_type:
		return

	del docfield_properties['allow_on_submit']

	self.set_property_setters()
	self.set_allow_on_submit()
	self.update_custom_fields()
	validate_fields_for_doctype(self.doc_type)

	frappe.msgprint(_("Completed Updating {0}").format(_(self.doc_type)))
	frappe.clear_cache(doctype=self.doc_type)
	self.fetch_to_customize()

def set_allow_on_submit(self):
	meta = frappe.get_meta(self.doc_type)

	for df in self.get("fields"):
		if df.get("__islocal"):
			continue

		meta_df = meta.get("fields", {"fieldname": df.fieldname})

		if not meta_df or meta_df[0].get("is_custom_field"):
			continue    

		if df.get("allow_on_submit"):
				self.make_property_setter(property="allow_on_submit", value=df.get("allow_on_submit"),
					property_type="Check", fieldname=df.fieldname)

def monkey_patch_for_allow_on_submit():
	from frappe.custom.doctype.customize_form.customize_form import CustomizeForm
	CustomizeForm.set_allow_on_submit = set_allow_on_submit
	CustomizeForm.save_customization = save_customization
	
def do_monkey_patch():
	monkey_patch_for_allow_on_submit()
