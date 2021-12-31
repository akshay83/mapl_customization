# -*- coding: utf-8 -*-
from __future__ import unicode_literals

app_name = "mapl_customization"
app_title = "Customizations for MAPL"
app_publisher = "Akshay Mehta"
app_description = "Customizations Done Specifically for Mehta Automobiles Pvt Ltd"
app_icon = "octicon octicon-file-directory"
app_color = "#589494"
app_email = "mehta.akshay@gmail.com"
app_version = "0.1.0"
app_license = "MIT"

cf_fields = [
		"Address-address_name",
		"Branch-cost_center",
		"Customer-company_name",
		"Customer-current_balance",
		"Customer-primary_email",
		"Customer-relation_name",
		"Customer-relation_to",
		"Customer-unique_idx",
		"Customer-vehicle_no",
		"Delivery Note Item-battery_serial_no",
		"Delivery Note Item-exchange_details",
		"Delivery Note Item-finance_serial_no",
		"Delivery Note Item-is_vehicle",
		"Delivery Note Item-service_book_no",
		"Delivery Note Item-staff_special_billing",
		"Delivery Note Item-under_exchange",
		"Delivery Note-column_break_ref",
		"Delivery Note-reference_details",
		"Delivery Note-references",
		"Delivery Note-referred_by",
		"Delivery Note-reporting_name",
		"Employee-bank_branch",
		"Employee-bank_details_verified",
		"Employee-ifsc_code",
		"Employee-no_pf_deduction",
		"Employee-uan_no",
		"Item-brand_details",
		"Item-cb",
		"Item-column_break_veh",
		"Item-engine_cc",
		"Item-fuel_used",
		"Item-gross_vehicle_weight",
		"Item-is_electric_vehicle",
		"Item-is_outdoor",
		"Item-is_vehicle",
		"Item-no_of_cylinders",
		"Item-regd_vehicle_name",
		"Item-seating_capacity",
		"Item-type_of_body",
		"Item-unleaden_weight",
		"Item-vehicle_details",
		"Item-wheel_base",
		"Journal Entry Account-party_name",
		"Journal Entry-cancel_reason",
		"Journal Entry-hypothecation_company",
		"Journal Entry-hypothecation_reference",
		"Journal Entry-reporting_name",
		"Lead-brand",
		"Lead-column_break",
		"Lead-creation_date",
		"Lead-interested_in",
		"Lead-item_group",
		"Lead-lead_type",
		"Lead-model",
		"Lead-sales_man",
		"Mode of Payment-base_mode",
		"Mode of Payment-column_break_1",
		"Payment Entry-address",
		"Payment Entry-base_amount",
		"Payment Entry-cheque_bank",
		"Payment Entry-in_words",
		"Payment Entry-party_account",
		"Payment Entry-party_address",
		"Payment Entry-payment_type_section",
		"Payment Entry-payments",
		"Payment Entry-receipts",
		"Payment Entry-reference_details",
		"Payment Entry-reporting_name",
		"Payment Entry-special_payment",
		"Payment Entry-type_column_break",
		"Purchase Invoice Item-color",
		"Purchase Invoice Item-engine_nos",
		"Purchase Invoice Item-gst_hsn_code",
		"Purchase Invoice Item-is_electric_vehicle",
		"Purchase Invoice Item-is_vehicle",
		"Purchase Invoice Item-key_nos",
		"Purchase Invoice Item-year_of_manufacture",
		"Purchase Invoice-reporting_name",
		"Purchase Invoice-supply_type",
		"Purchase Receipt Item-color",
		"Purchase Receipt Item-engine_nos",
		"Purchase Receipt Item-is_vehicle",
		"Purchase Receipt Item-key_nos",
		"Purchase Receipt Item-year_of_manufacture",
		"Purchase Receipt-reporting_name",
		"Quotation Item-description_section",
		"Quotation-bank",
		"Quotation-bank_details",
		"Quotation-bank_details_cb",
		"Quotation-closing_comments",
		"Quotation-closing_information",
		"Quotation-introduction",
		"Quotation-introductory_information",
		"Quotation-is_inclusive_of_taxes",
		"Quotation-reporting_name",
		"Quotation-show_bank_details",
		"Salary Detail-rounding",
		"Salary Slip-actual_salary",
		"Salary Slip-advance_deduction_details",
		"Salary Slip-bank_branch",
		"Salary Slip-calculate_actual_salary",
		"Salary Slip-ifsc_code",
		"Salary Slip-leave_availed",
		"Salary Slip-reporting_salary",
		"Salary Structure Assignment-actual_salary",
		"Salary Structure Assignment-no_pf_deduction",
		"Salary Structure Assignment-reported_salary",
		"Salary Structure-notes",
		"Sales Invoice Item-battery_serial_no",
		"Sales Invoice Item-charger_no",
		"Sales Invoice Item-column_break_rem",
		"Sales Invoice Item-exchange_details",
		"Sales Invoice Item-finance_serial_no",
		"Sales Invoice Item-is_electric_vehicle",
		"Sales Invoice Item-is_vehicle",
		"Sales Invoice Item-mop_rate",
		"Sales Invoice Item-remarks",
		"Sales Invoice Item-service_book_no",
		"Sales Invoice Item-staff_special_billing",
		"Sales Invoice Item-under_exchange",
		"Sales Invoice Payment-cheque_bank",
		"Sales Invoice Payment-cheque_reference_date",
		"Sales Invoice Payment-cheque_reference_no",
		"Sales Invoice-b2b_vehicles",
		"Sales Invoice-brand",
		"Sales Invoice-chassis_no",
		"Sales Invoice-column_break",
		"Sales Invoice-column_break_trans",
		"Sales Invoice-column_break_warehouse",
		"Sales Invoice-customer_vehicle_no",
		"Sales Invoice-date_time_of_supply",
		"Sales Invoice-delayed_payment",
		"Sales Invoice-delayed_payment_details",
		"Sales Invoice-dms_invoice_reference",
		"Sales Invoice-engine_no",
		"Sales Invoice-finance_charges",
		"Sales Invoice-finance_details",
		"Sales Invoice-finance_person",
		"Sales Invoice-finance_remarks",
		"Sales Invoice-finance_text",
		"Sales Invoice-hypothecation",
		"Sales Invoice-is_finance",
		"Sales Invoice-job_card_date",
		"Sales Invoice-job_card_no",
		"Sales Invoice-model",
		"Sales Invoice-payment_delayed_column_break",
		"Sales Invoice-place_of_supply",
		"Sales Invoice-reference",
		"Sales Invoice-notes",
		"Sales Invoice-referred_by",
		"Sales Invoice-reporting_name",
		"Sales Invoice-scheme",
		"Sales Invoice-service_detail_column_break",
		"Sales Invoice-service_details",
		"Sales Invoice-service_invoice",
		"Sales Invoice-special_invoice",
		"Sales Invoice-delayed_payment_remarks",
		"Sales Invoice-transportation_details",
		"Sales Invoice-vehicle_no",
		"Sales Invoice-warehouse_and_other_details",
		"Sales Order Item-exchange_details",
		"Sales Order Item-is_vehicle",
		"Sales Order Item-staff_special_billing",
		"Sales Order Item-under_exchange",
		"Sales Order-customer_account",
		"Sales Order-finance_charges",
		"Sales Order-finance_column",
		"Sales Order-finance_details",
		"Sales Order-finance_person",
		"Sales Order-finance_remarks",
		"Sales Order-finance_text",
		"Sales Order-hypothecation",
		"Sales Order-is_finance",
		"Sales Order-is_payment_received",
		"Sales Order-payment",
		"Sales Order-reference",
		"Sales Order-reporting_name",
		"Sales Order-scheme",
		"Serial No-chassis_no",
		"Serial No-color",
		"Serial No-column_101",
		"Serial No-column_break_custom_",
		"Serial No-engine_no",
		"Serial No-is_electric_vehicle",
		"Serial No-is_vehicle",
		"Serial No-key_no",
		"Serial No-warehouse_details",
		"Serial No-year_of_manufacture",
		"Stock Entry-reporting_name",
		"Supplier-current_balance",
		"User-user_group",
		"Salary Slip-bank_column_break",
		"Customer-aadhar_card_no",
		"Customer-signature"
]

print_fs = [
		"Vehicle Invoice",
		"Spares Invoice",
		"Sale Letter",
		"Custom Salary Slip",
		"Care of Problem",
		"Helmet Dummy Invoice",
		"Vehicle Receipt Format",
		"Receipt Print Format",
		"MOP Format",
		"ICICI Bank",
		"Credit Note",
		"Quotation Standard",
		"Sales Invoice Standard"
]

ps_fields = [
	"Sales Invoice-update_stock-default",
	"Sales Invoice-set_posting_time-default",
	"Customer-main-allow_rename",
	"Selling Settings-cust_master_name-default",
	"Accounts Settings-add_taxes_from_item_tax_template-default",
	"Buying Settings-supp_master_name-default"
]

fixtures = [	{
			"dt": "Custom Field",
			"filters": [["name", "in", cf_fields]]
		},
		{
			"dt": "Print Format",
			"filters": [["name", "in", print_fs]]
		}, 
		{
			"dt": "Property Setter",
			"filters": [["name", "in", ps_fields]]
		}, 
		"Letter Head", 
		"Custom SQL Queries"
]

doc_events = {
	"*" : {
		"autoname" : "mapl_customization.customizations_for_mapl.naming.set_auto_name",
		"validate" : "mapl_customization.customizations_for_mapl.naming.check_series"
	},
	"Sales Order": {
		"validate" : "mapl_customization.customizations_for_mapl.sales_order_validation.sales_order_validate",
		"before_cancel": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.before_cancel_sales_order",
		"on_submit": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.make_payment_entry_with_sales_order",
		"validate": "mapl_customization.customizations_for_mapl.sales_order_payment_entry.validate"
	},
	"Payment Entry": {
		"validate": "mapl_customization.customizations_for_mapl.payment_entry_validation.payment_entry_validate"
	},
	"Purchase Receipt" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.purchase_validation.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.purchase_validation.purchase_receipt_validate"
	},
	"Purchase Invoice" : {
		"on_submit" : "mapl_customization.customizations_for_mapl.purchase_validation.purchase_receipt_on_submit",
		"validate" : "mapl_customization.customizations_for_mapl.purchase_validation.purchase_receipt_validate",
		"before_submit": "mapl_customization.customizations_for_mapl.purchase_validation.purchase_receipt_before_submit"
	},
	"Sales Invoice" : {
		"validate" : "mapl_customization.customizations_for_mapl.sales_invoice_validation.sales_invoice_validate",
		"before_submit" : "mapl_customization.customizations_for_mapl.sales_invoice_validation.sales_on_submit_validation",
		"before_cancel":"mapl_customization.customizations_for_mapl.sales_invoice_hooks.before_cancel"
	},
        "Stock Entry" : {
                "validate": "mapl_customization.customizations_for_mapl.sales_invoice_validation.validate_stock_entry_serial_no"
        },
	"Salary Slip" : {
		"validate": "mapl_customization.customizations_for_mapl.salary_slip_utils.salary_slip_before_save"
	},
	"Customer" : {
		"before_insert": "mapl_customization.customizations_for_mapl.quick_customer.validate_customer_before_save",
		"validate": "mapl_customization.customizations_for_mapl.quick_customer.validate_customer"
	},
	"Lead" : {
		"after_insert": "mapl_customization.customizations_for_mapl.lead_hooks.on_save_lead",
		"before_insert": "mapl_customization.customizations_for_mapl.lead_hooks.before_insert_lead"
	},
	"Address": {
		"validate": "mapl_customization.customizations_for_mapl.quick_customer.validate_address"
	}
}

after_install = "mapl_customization.customizations_for_mapl.install.after_install"

app_include_css = "/assets/mapl_customization/css/custom_css.css"
app_include_js = ["/assets/mapl_customization/js/core.js",
		"/assets/mapl_customization/js/quick_customer.js"
		]

#doctype_list_js = {"Payment Entry" : "/public/js/payment_entry_list.js",
#			"Sales Invoice" : "/public/js/sales_invoice_list.js"}

#version-13 branch supports this
jenv = {
	"methods" : [],
	"filters": [
		"date_to_code:mapl_customization.customizations_for_mapl.jinja.date_to_code",
		"json_load:mapl_customization.customizations_for_mapl.jinja.json_load"
		]
}

#delevop branch supports this
jinja = {
	"methods" : [],
	"filters": [
		"mapl_customization.customizations_for_mapl.jinja.date_to_code",
		"mapl_customization.customizations_for_mapl.jinja.json_load"
		]
}

doctype_js = {
		"Sales Invoice": "/public/js/scripts/sales_invoice.js",
		"Sales Order": "/public/js/scripts/sales_order.js",
		"Purchase Invoice": "/public/js/scripts/purchase_invoice.js",
		"Purchase Receipt": "/public/js/scripts/purchase_receipt.js",
		"Item": "/public/js/scripts/item.js",
		"Address": "/public/js/scripts/address.js",
		"Customer": "/public/js/scripts/customer.js",
		"Delivery Note": "/public/js/scripts/delivery_note.js",
		"Journal Entry": "/public/js/scripts/journal_entry.js",
		"Payment Entry": "/public/js/scripts/payment_entry.js",
		"Quotation": "/public/js/scripts/quotation.js",
		"Supplier": "/public/js/scripts/supplier.js",
		"Salary Slip": "/public/js/scripts/salary_slip.js"
}

standard_queries = {
	"Customer": "mapl_customization.customizations_for_mapl.queries.mapl_customer_query"
}

workflow_safe_globals = {
	"mapl_customization.utils.check_average_purchase" : "mapl_customization.customizations_for_mapl.utils.check_average_purchase"
}

#Monkey Patch
#from mapl_customization.customizations_for_mapl.monkey_patch import do_monkey_patch
#do_monkey_patch()

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
