import frappe
from frappe import _


def get_list_context(context):
	"""Custom list context for Student Applicant - filters by current user's email"""
	context.title = _("Student Applicant")
	context.introduction = _("View and manage your student applications")
	
	# Get current user's email
	user_email = frappe.session.user
	
	# Filter by student_email_id matching current user
	context.filters = {
		"student_email_id": user_email
	}
	
	# Allow editing existing records
	context.show_create = False  # Don't show "New" button - they should use webform for new applications
	context.row_template = "eduction_override/templates/pages/student_applicant_row.html"
	context.no_result_message = _("No applications found. Please submit a new application using the webform.")
	
	return context

