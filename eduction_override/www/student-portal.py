# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe


def get_context(context):
	"""Add custom JavaScript to student-portal page"""
	# Get original context from education app
	try:
		from education.education.www.student_portal import get_context as get_original_context
		get_original_context(context)
	except:
		# Fallback if original doesn't exist
		abbr = frappe.db.get_single_value(
			"Education Settings", "school_college_name_abbreviation"
		)
		logo = frappe.db.get_single_value("Education Settings", "school_college_logo")
		context.abbr = abbr or "Frappe Education"
		context.logo = logo or "/favicon.png"
	
	# Add our custom script to body_include
	if not hasattr(context, 'body_include'):
		context.body_include = ""
	
	context.body_include += """
	<script src="/assets/eduction_override/js/student_portal_menu.js"></script>
	"""
	
	return context

