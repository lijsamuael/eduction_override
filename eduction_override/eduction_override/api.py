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


@frappe.whitelist()
def get_students_by_guardian(guardian):
	"""Get all students that have the specified guardian
	
	:param guardian: Guardian name
	:return: List of students with their details
	"""
	if not guardian:
		return []
	
	# Get all Student Guardian records where guardian matches and parenttype is "Student"
	student_guardians = frappe.get_all(
		"Student Guardian",
		filters={"guardian": guardian, "parenttype": "Student"},
		fields=["parent"]
	)
	
	if not student_guardians:
		return []
	
	# Get unique student names
	student_names = list(set([sg.parent for sg in student_guardians]))
	
	# Get student details
	students = frappe.get_all(
		"Student",
		filters={"name": ["in", student_names]},
		fields=["name", "student_name", "date_of_birth", "gender"]
	)
	
	# Get program details for each student from Program Enrollment
	result = []
	for student in students:
		# Get current program enrollment if available
		program = frappe.db.get_value(
			"Program Enrollment",
			{"student": student.name, "docstatus": 1},
			"program",
			order_by="creation desc"
		)
		
		result.append({
			"student": student.name,
			"full_name": student.student_name,
			"date_of_birth": student.date_of_birth,
			"gender": student.gender,
			"program": program or ""
		})
	
	return result


@frappe.whitelist(allow_guest=False)
def get_siblings_for_current_student():
	"""Get all students with user accounts (no filters for demo purposes)
	
	:return: List of all students with their details including user email
	"""
	email = frappe.session.user
	if email == "Administrator":
		return []
	
	try:
		# Get all students
		all_students = frappe.get_all(
			"Student",
			fields=["name", "student_name", "user", "date_of_birth", "gender", "image"]
		)
		
		if not all_students:
			frappe.logger().debug("No students found")
			return []
		
		# Filter to only include students with user accounts (required for switching)
		students = [s for s in all_students if s.user]
		
		if not students:
			frappe.logger().debug("No students with user accounts found")
			return []
		
		# Build result list
		result = []
		for student in students:
			result.append({
				"student": student.name,
				"student_name": student.student_name,
				"user": student.user,
				"date_of_birth": student.date_of_birth,
				"gender": student.gender,
				"image": student.image or ""
			})
		
		frappe.logger().debug(f"Found {len(result)} students with user accounts")
		return result
		
	except Exception as e:
		frappe.logger().error(f"Error getting students: {str(e)}")
		frappe.logger().error(frappe.get_traceback())
		return []


@frappe.whitelist(allow_guest=False, methods=["POST"])
def switch_to_sibling(sibling_user):
	"""Switch/impersonate to a sibling user
	
	:param sibling_user: User email of the sibling to switch to
	:return: Success message
	"""
	current_user = frappe.session.user
	if current_user == "Administrator":
		frappe.throw(_("Administrator cannot use sibling switching"))
	
	# Get original user - check if we have it stored, otherwise use impersonated_by or current user
	original_user = frappe.session.data.get("original_sibling_user")
	if not original_user:
		# Check if we're already impersonated
		impersonated_by = frappe.session.data.get("impersonated_by")
		if impersonated_by:
			original_user = impersonated_by
			# Store it for future reference
			frappe.local.session_obj.data.data.original_sibling_user = original_user
		else:
			# First time switching, current user is the original
			original_user = current_user
			# Store it in session for future reference
			frappe.local.session_obj.data.data.original_sibling_user = original_user
	
	# Check if switching back to original user
	if sibling_user == original_user:
		# Switching back to original user - clear impersonation
		# Clear the impersonation flags
		frappe.local.session_obj.data.data.impersonated_by = None
		frappe.local.session_obj.data.data.original_sibling_user = None
		
		# Get session data before clearing
		session_data = frappe.local.session_obj.data.data
		
		# Update session to clear impersonation flags
		frappe.local.session_obj.update(force=True)
		
		# Use login_as to switch back to original user (this properly clears impersonation)
		frappe.local.login_manager.login_as(
			original_user,
			session_end=session_data.session_end,
			audit_user=session_data.audit_user
		)
		
		# Log the switch back
		frappe.get_doc(
			{
				"doctype": "Activity Log",
				"user": original_user,
				"status": "Success",
				"subject": _("User {0} switched back from {1}").format(original_user, current_user),
				"operation": "Impersonate",
			}
		).insert(ignore_permissions=True, ignore_links=True)
		
		frappe.local.response["message"] = _("Switched back to {0}").format(original_user)
		return
	
	# Verify the sibling user exists and is enabled
	user_doc = frappe.get_doc("User", sibling_user)
	if not user_doc.enabled:
		frappe.throw(_("The selected user account is disabled"))
	
	# Log the switch (using Impersonate operation since we're using impersonation mechanism)
	frappe.get_doc(
		{
			"doctype": "Activity Log",
			"user": sibling_user,
			"status": "Success",
			"subject": _("User {0} switched to sibling {1}").format(original_user, sibling_user),
			"operation": "Impersonate",
		}
	).insert(ignore_permissions=True, ignore_links=True)
	
	# Store original user before impersonating (impersonate will overwrite impersonated_by)
	frappe.local.session_obj.data.data.original_sibling_user = original_user
	
	# Impersonate the sibling user (this will set impersonated_by to current_user)
	frappe.local.login_manager.impersonate(sibling_user)
	
	frappe.local.response["message"] = _("Switched to {0}").format(sibling_user)
	return


@frappe.whitelist(allow_guest=False)
def get_original_user():
	"""Get the original user if currently impersonated
	
	:return: Original user email or current user if not impersonated
	"""
	# Check if we have stored original user
	original_user = frappe.session.data.get("original_sibling_user")
	if original_user:
		return original_user
	# If not stored, check impersonated_by (for backward compatibility)
	impersonated_by = frappe.session.data.get("impersonated_by")
	if impersonated_by:
		return impersonated_by
	# If not impersonated, return current user
	return frappe.session.user

