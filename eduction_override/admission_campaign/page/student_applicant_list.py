# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe
from frappe import _


def get_context(context):
	"""Redirect /student_applicant_list to /app/student-applicant"""
	# Always redirect to the correct Frappe list view route
	# Use HTTP 302 redirect
	frappe.flags.redirect_location = '/app/student-applicant'
	raise frappe.Redirect(302)

