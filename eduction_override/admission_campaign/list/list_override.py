# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe
from frappe.www.list import get as original_get
from frappe.utils import quoted


def _patch_set_route():
	"""Patch set_route function to force correct route for Student Applicant"""
	from frappe.www.list import set_route as original_set_route
	
	def set_route(context):
		"""Override set_route to force correct pathname for Student Applicant"""
		# If this is Student Applicant, force the route to /app/student-applicant/{name}
		if hasattr(context, 'doc') and context.doc:
			doc_doctype = getattr(context.doc, 'doctype', None)
			if doc_doctype == "Student Applicant":
				# Use absolute path starting with /app/
				context.pathname = "/app/student-applicant"
				context.route = f"/app/student-applicant/{quoted(context.doc.name)}"
				frappe.logger().info(f"Overriding route for Student Applicant: {context.route}")
				return
		
		# For other doctypes, use original function
		original_set_route(context)
	
	# Patch it
	frappe.www.list.set_route = set_route


# Apply patch when module is imported
_patch_set_route()


@frappe.whitelist(allow_guest=True)
def get(
	doctype: str,
	txt: str | None = None,
	limit_start: int = 0,
	limit: int = 20,
	pathname: str | None = None,
	**kwargs,
):
	"""Override list.get to force pathname for Student Applicant and add user filtering"""
	# If this is Student Applicant, ALWAYS force pathname to /app/student-applicant
	if doctype == "Student Applicant":
		pathname = "/app/student-applicant"
		frappe.logger().info(f"Overriding pathname for Student Applicant to: {pathname}")
		
		# Add filter to show only current user's applications (if not admin)
		user_email = frappe.session.user
		if user_email and user_email not in ("Administrator", "Guest"):
			# Add filter to kwargs if not already present
			if 'filters' not in kwargs:
				kwargs['filters'] = {}
			if isinstance(kwargs['filters'], dict):
				kwargs['filters']['student_email_id'] = user_email
			frappe.logger().info(f"Filtering Student Applicant list for user: {user_email}")
	
	# Call original function with overridden pathname
	return original_get(doctype, txt, limit_start, limit, pathname, **kwargs)

