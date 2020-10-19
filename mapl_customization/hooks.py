# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "mapl_customization"
app_title = "Customizations for MAPL"
app_publisher = "Akshay Mehta"
app_description = "Customizations Done Specifically for Mehta Automobiles Pvt Ltd"
app_icon = "octicon octicon-file-directory"
app_color = "#589494"
app_email = "mehta.akshay@gmail.com"
app_version = "0.0.1"
app_license = "MIT"

fixtures = ["Custom Field", "Property Setter", "Stock Settings", "Selling Settings","Buying Settings","Custom Script",
		 "Print Format", "Letter Head", "Workflow", "Workflow State", "Workflow Action", "Custom SQL Queries"]

doc_events = {
	"*" : {
		"autoname" : "mapl_customization.customizations_for_mapl.naming.set_auto_name",
		"validate" : "mapl_customization.customizations_for_mapl.naming.check_series"
	},
	"Item" : {
		"validate" : "mapl_customization.customizations_for_mapl.item_hooks.item_validate"
	},
	"Sales Order": {
		"validate" : "mapl_customization.customizations_for_mapl.sales_invoice_validation.sales_order_validate",
		"before_cancel": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.before_cancel_sales_order",
		"on_submit": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.make_payment_entry_with_sales_order",
		"validate": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.validate"
	},
	"Payment Entry": {
		"validate": "mapl_customization.customizations_for_mapl.payment_entry_validation.payment_entry_validate",
		"on_update_after_submit":"mapl_customization.customizations_for_mapl.payment_entry_hooks.payment_entry_on_update_after_submit"
	},
	"Purchase Receipt" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_validate"
	},
	"Purchase Invoice" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_validate",
		"before_update_after_submit": "mapl_customization.customizations_for_mapl.puchase_invoice_hooks.check_role",
		"on_update_after_submit":"mapl_customization.customizations_for_mapl.purchase_invoice_hooks.purchase_invoice_on_update_after_submit",
		"before_submit": "mapl_customization.customizations_for_mapl.utils.purchase_receipt_before_submit"
	},
	"Sales Invoice" : {
		"validate" : "mapl_customization.customizations_for_mapl.sales_invoice_validation.sales_invoice_validate",
		"before_submit" : "mapl_customization.customizations_for_mapl.sales_invoice_validation.sales_on_submit_validation",
		"before_save": "mapl_customization.customizations_for_mapl.workflow_hooks.before_save_salesinvoice",
		"before_update_after_submit":"mapl_customization.customizations_for_mapl.sales_invoice_hooks.check_role",
		"on_update_after_submit":"mapl_customization.customizations_for_mapl.sales_invoice_hooks.sales_invoice_on_update_after_submit"
	},
	"Selling Settings" : {
		"on_update": "mapl_customization.customizations_for_mapl.workflow_hooks.on_update_selling_settings"
	},
        "Stock Entry" : {
                "validate": "mapl_customization.customizations_for_mapl.sales_invoice_validation.validate_stock_entry_serial_no"
        },
	"Salary Slip" : {
		"before_save": "mapl_customization.customizations_for_mapl.salary_slip_hooks.salary_slip_before_save"
	},
	"Customer" : {
		"before_insert": "mapl_customization.customizations_for_mapl.quick_customer.validate_customer_before_save",
		"validate": "mapl_customization.customizations_for_mapl.quick_customer.validate_customer"
	},
	"Lead" : {
		"after_insert": "mapl_customization.customizations_for_mapl.utils.on_save_lead",
		"before_insert": "mapl_customization.customizations_for_mapl.utils.before_insert_lead"
	},
	"Address": {
		"validate": "mapl_customization.customizations_for_mapl.quick_customer.validate_address"
	}
}

after_install = "mapl_customization.customizations_for_mapl.install.after_install"

app_include_css = "/assets/mapl_customization/css/custom_css.css"
app_include_js = ["/assets/mapl_customization/js/side_bar.js",
				"/assets/mapl_customization/js/form_comments.js",
				"/assets/mapl_customization/js/core.js",
				"/assets/mapl_customization/js/lz-string.min.js",
				"/assets/mapl_customization/js/quick_customer.js",
				"/assets/mapl_customization/js/monkey_patch_list_view.js"
				]

doctype_list_js = {"Payment Entry" : "/public/js/payment_entry_list.js",
			"Sales Invoice" : "/public/js/sales_invoice_list.js"}

jenv_filter = [
    'json_load:mapl_customization.customizations_for_mapl.jinja.json_load',
    'date_to_code:mapl_customization.customizations_for_mapl.jinja.date_to_code'
]

#Monkey Patch
from mapl_customization.customizations_for_mapl.monkey_patch import do_monkey_patch
do_monkey_patch()

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/mapl_customization/css/mapl_customization.css"
# app_include_js = "/assets/mapl_customization/js/mapl_customization.js"

# include js, css files in header of web template
# web_include_css = "/assets/mapl_customization/css/mapl_customization.css"
# web_include_js = "/assets/mapl_customization/js/mapl_customization.js"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
#	"Role": "home_page"
# }

# Website user home page (by function)
# get_website_user_home_page = "mapl_customization.utils.get_home_page"

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# Installation
# ------------

# before_install = "mapl_customization.install.before_install"
# after_install = "mapl_customization.install.after_install"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "mapl_customization.notifications.get_notification_config"

# Permissions
# -----------
# Permissions evaluated in scripted ways

# permission_query_conditions = {
# 	"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions",
# }
#
# has_permission = {
# 	"Event": "frappe.desk.doctype.event.event.has_permission",
# }

# Document Events
# ---------------
# Hook on document methods and events

# doc_events = {
# 	"*": {
# 		"on_update": "method",
# 		"on_cancel": "method",
# 		"on_trash": "method"
#	}
# }

# Scheduled Tasks
# ---------------

# scheduler_events = {
# 	"all": [
# 		"mapl_customization.tasks.all"
# 	],
# 	"daily": [
# 		"mapl_customization.tasks.daily"
# 	],
# 	"hourly": [
# 		"mapl_customization.tasks.hourly"
# 	],
# 	"weekly": [
# 		"mapl_customization.tasks.weekly"
# 	]
# 	"monthly": [
# 		"mapl_customization.tasks.monthly"
# 	]
# }

# Testing
# -------

# before_tests = "mapl_customization.install.before_tests"

# Overriding Whitelisted Methods
# ------------------------------
#
# override_whitelisted_methods = {
# 	"frappe.desk.doctype.event.event.get_events": "mapl_customization.event.get_events"
# }
