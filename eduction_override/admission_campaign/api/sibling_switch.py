# Sibling Switch Functionality
# Allows students to switch between siblings without login/logout

import frappe
from frappe import _


@frappe.whitelist(allow_guest=False)
def get_siblings_for_current_student():
	"""Get siblings from Student Sibling table for the currently logged in student
	
	Logic:
	1. Get current user email -> find Student document (user field = email)
	2. Get all Student Sibling records where parent = current student -> get student IDs
	3. For those student IDs, get Student documents and check if they have user accounts
	4. Return siblings with user accounts
	
	:return: List of siblings with their details including user email
	"""
	email = frappe.session.user
	if email == "Administrator":
		return []
	
	try:
		# Use current logged-in user to get siblings (not original user)
		# This way, if user A switches to user B, we get siblings for user B (current user)
		current_logged_in_user = email
		
		frappe.logger().debug(f"Getting siblings for current user: {current_logged_in_user}")
		
		# Step 1: Get current student by user email (user field in Student document)
		student_doc = frappe.db.get_value(
			"Student",
			{"user": current_logged_in_user},
			"name"
		)
		
		if not student_doc:
			frappe.logger().debug(f"No student found for user: {current_logged_in_user}")
			return []
		
		current_student = student_doc
		frappe.logger().debug(f"Current student: {current_student}")
		
		# Step 2: Get siblings from Student Sibling table where parent = current_student
		# Use frappe.db.get_all to bypass permission checks for child table
		sibling_records = frappe.db.get_all(
			"Student Sibling",
			filters={
				"parent": current_student,
				"parenttype": "Student"
			},
			fields=["student"]
		)
		
		frappe.logger().debug(f"Found {len(sibling_records)} sibling records for student {current_student}")
		
		if not sibling_records:
			frappe.logger().debug(f"No siblings found in Student Sibling table for student: {current_student}")
			return []
		
		# Step 3: Get unique sibling student IDs (only those with student field filled)
		# The student field should contain Student IDs, but validate they exist
		sibling_student_ids_raw = [s.student for s in sibling_records if s.student]
		
		# Validate that these are actual Student IDs (not full names)
		# Check if they exist in Student doctype
		valid_student_ids = []
		for student_id in sibling_student_ids_raw:
			# Check if this is a valid Student ID
			student_exists = frappe.db.exists("Student", student_id)
			if student_exists:
				valid_student_ids.append(student_id)
			else:
				# If not found by ID, try to find by student_name (in case full name was stored)
				student_by_name = frappe.db.get_value(
					"Student",
					{"student_name": student_id},
					"name"
				)
				if student_by_name:
					valid_student_ids.append(student_by_name)
					frappe.logger().debug(f"Found student by name '{student_id}' -> ID: {student_by_name}")
		
		sibling_student_ids = list(set(valid_student_ids))
		
		frappe.logger().debug(f"Sibling student IDs (validated): {sibling_student_ids}")
		
		if not sibling_student_ids:
			frappe.logger().debug(f"No valid sibling student IDs found")
			return []
		
		# Step 4: Get student details for all sibling IDs
		# Use frappe.db.get_all to bypass permission checks
		students = frappe.db.get_all(
			"Student",
			filters={"name": ["in", sibling_student_ids]},
			fields=["name", "student_name", "user", "date_of_birth", "gender", "image"]
		)
		
		frappe.logger().debug(f"Found {len(students)} students for sibling IDs")
		
		# Step 5: Filter to only include students with user accounts (required for switching)
		students = [s for s in students if s.user]
		
		frappe.logger().debug(f"Found {len(students)} students with user accounts")
		
		if not students:
			frappe.logger().debug(f"No students with user accounts found in: {sibling_student_ids}")
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
		
		frappe.logger().debug(f"Found {len(result)} siblings for student {current_student}")
		
		# Ensure we return a list (not None)
		if not result:
			result = []
		
		return result
		
	except Exception as e:
		frappe.logger().error(f"Error getting siblings: {str(e)}")
		frappe.logger().error(frappe.get_traceback())
		# Return empty list instead of None
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

