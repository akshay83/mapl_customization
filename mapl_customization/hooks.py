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
fixtures = ["Custom Field", "Property Setter", "Stock Settings", "Selling Settings","Buying Settings","Custom Script", "Print Format", "Letter Head"]
doc_events = {
	"Purchase Receipt" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_validate"
	},
	"Purchase Invoice" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.utils.purchase_receipt_validate"
	},
	"Journal Entry" : {
		"before_cancel" : "mapl_customization.customizations_for_mapl.utils.check_receipt_in_journal_entry"
	}
}

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
