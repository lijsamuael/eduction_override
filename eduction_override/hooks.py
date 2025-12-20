app_name = "eduction_override"
app_title = "Eduction Override"
app_publisher = "Samuael Ketema"
app_description = "Education Override"
app_email = "lijsamuael@gmail.com"
app_license = "mit"

# Apps
# ------------------

required_apps = ["education","erpnext"]

# Each item in the list will be shown as an app in the apps page
# add_to_apps_screen = [
# 	{
# 		"name": "eduction_override",
# 		"logo": "/assets/eduction_override/logo.png",
# 		"title": "Eduction Override",
# 		"route": "/eduction_override",
# 		"has_permission": "eduction_override.api.permission.has_app_permission"
# 	}
# ]

# Includes in <head>
# ------------------

# include js, css files in header of desk.html
# app_include_css = "/assets/eduction_override/css/eduction_override.css"
# app_include_js = "/assets/eduction_override/js/eduction_override.js"

# include js, css files in header of web template
# web_include_css = "/assets/eduction_override/css/eduction_override.css"
# web_include_js = "/assets/eduction_override/js/eduction_override.js"

# include custom scss in every website theme (without file extension ".scss")
# website_theme_scss = "eduction_override/public/scss/website"

# include js, css files in header of web form
# webform_include_js = {"doctype": "public/js/doctype.js"}
# webform_include_css = {"doctype": "public/css/doctype.css"}

# include js in page
# page_js = {"page" : "public/js/file.js"}

# include js in doctype views
# doctype_js = {"doctype" : "public/js/doctype.js"}
doctype_list_js = {"Sales Invoice" : "eduction_override.accounts.doctype.sales_invoice.sales_invoice_list"}
# doctype_tree_js = {"doctype" : "public/js/doctype_tree.js"}
# doctype_calendar_js = {"doctype" : "public/js/doctype_calendar.js"}

# Svg Icons
# ------------------
# include app icons in desk
# app_include_icons = "eduction_override/public/icons.svg"

# Home Pages
# ----------

# application home page (will override Website Settings)
# home_page = "login"

# website user home page (by Role)
# role_home_page = {
# 	"Role": "home_page"
# }

# Generators
# ----------

# automatically create page for each record of this doctype
# website_generators = ["Web Page"]

# automatically load and sync documents of this doctype from downstream apps
# importable_doctypes = [doctype_1]

# Jinja
# ----------

# add methods and filters to jinja environment
# jinja = {
# 	"methods": "eduction_override.utils.jinja_methods",
# 	"filters": "eduction_override.utils.jinja_filters"
# }

# Installation
# ------------

# before_install = "eduction_override.install.before_install"
# after_install = "eduction_override.install.after_install"

# Uninstallation
# ------------

# before_uninstall = "eduction_override.uninstall.before_uninstall"
# after_uninstall = "eduction_override.uninstall.after_uninstall"

# Integration Setup
# ------------------
# To set up dependencies/integrations with other apps
# Name of the app being installed is passed as an argument

# before_app_install = "eduction_override.utils.before_app_install"
# after_app_install = "eduction_override.utils.after_app_install"

# Integration Cleanup
# -------------------
# To clean up dependencies/integrations with other apps
# Name of the app being uninstalled is passed as an argument

# before_app_uninstall = "eduction_override.utils.before_app_uninstall"
# after_app_uninstall = "eduction_override.utils.after_app_uninstall"

# Desk Notifications
# ------------------
# See frappe.core.notifications.get_notification_config

# notification_config = "eduction_override.notifications.get_notification_config"

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
# 	}
# }

# Scheduled Tasks
# ---------------

scheduler_events = {
	"daily": [
		"eduction_override.fees.tasks.daily"
	]
}

# Testing
# -------

# before_tests = "eduction_override.install.before_tests"

extend_doctype_class = {
	"Fee Schedule": "eduction_override.eduction_override.fee_schedule.CustomFeeSchedule",
	"Sales Invoice": "eduction_override.accounts.sales_invoice_override.CustomSalesInvoice"
}

# Overriding Methods
# ------------------------------

# override_whitelisted_methods is not used for create_sales_invoice 
# because it's not a whitelisted method. We use monkey patching instead.
# The patch is applied in eduction_override.fees.__init__
#
# each overriding function accepts a `data` argument;
# generated from the base implementation of the doctype dashboard,
# along with any modifications made in other Frappe apps
# override_doctype_dashboards = {
# 	"Task": "eduction_override.task.get_dashboard_data"
# }

# exempt linked doctypes from being automatically cancelled
#
# auto_cancel_exempted_doctypes = ["Auto Repeat"]

# Ignore links to specified DocTypes when deleting documents
# -----------------------------------------------------------

# ignore_links_on_delete = ["Communication", "ToDo"]

# Request Events
# ----------------
# before_request = ["eduction_override.utils.before_request"]
# after_request = ["eduction_override.utils.after_request"]

# Job Events
# ----------
# before_job = ["eduction_override.utils.before_job"]
# after_job = ["eduction_override.utils.after_job"]

# User Data Protection
# --------------------

# user_data_fields = [
# 	{
# 		"doctype": "{doctype_1}",
# 		"filter_by": "{filter_by}",
# 		"redact_fields": ["{field_1}", "{field_2}"],
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_2}",
# 		"filter_by": "{filter_by}",
# 		"partial": 1,
# 	},
# 	{
# 		"doctype": "{doctype_3}",
# 		"strict": False,
# 	},
# 	{
# 		"doctype": "{doctype_4}"
# 	}
# ]

# Authentication and authorization
# --------------------------------

# auth_hooks = [
# 	"eduction_override.auth.validate"
# ]

# Automatically update python controller files with type annotations for this app.
# export_python_type_annotations = True

# default_log_clearing_doctypes = {
# 	"Logging DocType Name": 30  # days to retain logs
# }

# Translation
# ------------
# List of apps whose translatable strings should be excluded from this app's translations.
# ignore_translatable_strings_from = []

