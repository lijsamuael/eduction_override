import frappe
from frappe import _
from education.education.api import get_current_enrollment, get_student_groups


@frappe.whitelist(allow_guest=False)
def get_student_portal_menu_items():
	"""Get custom menu items for student portal sidebar"""
	user_roles = frappe.get_roles()
	
	# Only return items for Student role
	if "Student" not in user_roles:
		return []
	
	# Get menu items from standard_portal_menu_items hook
	menu_items = []
	for item in frappe.get_hooks("standard_portal_menu_items"):
		if item.get("role") == "Student" or not item.get("role"):
			menu_items.append({
				"label": item.get("title"),
				"route": item.get("route"),
				"reference_doctype": item.get("reference_doctype"),
			})
	
	return menu_items


@frappe.whitelist()
def get_student_info():
	"""Override get_student_info to allow access even when Student doesn't exist yet"""
	email = frappe.session.user
	if email == "Administrator":
		return
	
	# Try to get student info
	student_list = frappe.db.get_list(
		"Student",
		fields=["*"],
		filters={"user": email},
	)
	
	# If student exists, return normal student info
	if student_list:
		student_info = student_list[0]
		current_program = get_current_enrollment(student_info.name)
		if current_program:
			student_groups = get_student_groups(student_info.name, current_program.program)
			student_info["student_groups"] = student_groups
			student_info["current_program"] = current_program
		return student_info
	
	# If student doesn't exist, return minimal info to allow portal access
	# This allows students to access portal even before admin creates Student record
	try:
		user_doc = frappe.get_doc("User", email)
		first_name = user_doc.first_name or ""
		last_name = user_doc.last_name or ""
		student_name = user_doc.full_name or email
	except Exception as e:
		frappe.logger().error(f"Error getting user info for {email}: {str(e)}")
		# Fallback to email-based info
		first_name = email.split("@")[0] if "@" in email else email
		last_name = ""
		student_name = email
	
	student_info = {
		"name": None,
		"user": email,
		"student_email_id": email,
		"first_name": first_name,
		"last_name": last_name,
		"student_name": student_name,
		"student_groups": [],
		"current_program": None,
	}
	
	frappe.logger().info(f"Student not found for user {email}, returning minimal info for portal access")
	return student_info


