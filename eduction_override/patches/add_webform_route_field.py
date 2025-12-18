import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	"""Add web_form and webform_route custom fields to Student Admission doctype"""
	# Add Web Form Link field
	if not frappe.db.exists("Custom Field", {"dt": "Student Admission", "fieldname": "web_form"}):
		create_custom_field(
			"Student Admission",
			{
				"fieldname": "web_form",
				"label": "Web Form",
				"fieldtype": "Link",
				"options": "Web Form",
				"description": "Select the web form to use for this admission. The route will be automatically fetched.",
				"insert_after": "enable_admission_application",
			},
			ignore_validate=True,
		)
	
	# Add Web Form Route field (auto-fetched from Web Form)
	if not frappe.db.exists("Custom Field", {"dt": "Student Admission", "fieldname": "webform_route"}):
		create_custom_field(
			"Student Admission",
			{
				"fieldname": "webform_route",
				"label": "Web Form Route",
				"fieldtype": "Data",
				"fetch_from": "web_form.route",
				"fetch_if_empty": 1,
				"read_only": 1,
				"description": "Route of the web form (automatically fetched from selected Web Form). Leave empty to use default 'student-applicant'",
				"insert_after": "web_form",
			},
			ignore_validate=True,
		)
	
	frappe.clear_cache(doctype="Student Admission")

