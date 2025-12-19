# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe


def before_request():
	"""Redirect student_applicant_list to /app/student-applicant"""
	try:
		if hasattr(frappe.local, 'request') and frappe.local.request:
			path = frappe.local.request.path
			
			# Normalize path - remove query string and fragments
			if '?' in path:
				path = path.split('?')[0]
			if '#' in path:
				path = path.split('#')[0]
			
			# If someone tries to access /student_applicant_list, redirect to /app/student-applicant
			if path == '/student_applicant_list' or path.startswith('/student_applicant_list/'):
				frappe.logger().info(f"Redirecting {path} to /app/student-applicant")
				frappe.flags.redirect_location = '/app/student-applicant'
				raise frappe.Redirect(302)
	except Exception as e:
		# Log but don't break if there's an error
		frappe.logger().error(f"Error in before_request redirect: {str(e)}")

