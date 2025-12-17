# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _
from frappe.www.list import get_context as get_standard_list_context


def get_context(context):
	"""Custom context for Student Applicant list - filters by current user's email"""
	doctype = "Student Applicant"
	
	# Get current user's email
	user_email = frappe.session.user
	
	# Set doctype in form_dict so list.py can process it
	if not hasattr(frappe.local, 'form_dict'):
		frappe.local.form_dict = frappe._dict()
	frappe.local.form_dict.doctype = doctype
	
	# Get standard list context - this handles all the list rendering
	# It reads doctype from form_dict
	get_standard_list_context(context)
	
	# Override filters to filter by student_email_id
	# The filters will be applied when get_list_data is called
	if not hasattr(context, 'filters') or not context.filters:
		context.filters = {}
	context.filters["student_email_id"] = user_email
	
	# Customize context
	context.title = _("Student Applicant")
	context.introduction = _("View and manage your student applications")
	context.show_create = False  # Don't show "New" button
	context.row_template = "eduction_override/templates/pages/student_applicant_row.html"
	context.no_result_message = _("No applications found. Please submit a new application using the webform.")
	
	return context

