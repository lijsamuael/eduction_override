# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe


def fix_student_applicant_menu():
	"""Fix Student Applicant menu item route in Portal Settings"""
	try:
		portal_settings = frappe.get_single("Portal Settings")
		updated = False
		
		# Remove duplicate Student Applicant items, keep only one enabled with correct route
		items_to_remove = []
		student_applicant_items = []
		
		for idx, item in enumerate(portal_settings.menu):
			if item.title == "Student Applicant":
				student_applicant_items.append((idx, item))
		
		# If we have Student Applicant items, fix them
		if student_applicant_items:
			# Keep the first one, remove the rest
			first_idx, first_item = student_applicant_items[0]
			# Fix the first one
			first_item.route = "/app/student-applicant"
			first_item.enabled = 1
			first_item.role = "Student"  # Ensure role is set
			first_item.reference_doctype = "Student Applicant"  # Ensure reference doctype is set
			updated = True
			
			# Mark others for removal
			for idx, item in student_applicant_items[1:]:
				items_to_remove.append(idx)
		
		# Remove duplicates (in reverse order to maintain indices)
		for idx in reversed(items_to_remove):
			portal_settings.menu.pop(idx)
			updated = True
		
		# If no Student Applicant item exists, add one from hooks
		if not student_applicant_items:
			# Sync menu to add items from hooks
			portal_settings.sync_menu()
			updated = True
		
		# Fix custom menu items
		for item in portal_settings.custom_menu:
			if item.title == "Student Applicant":
				item.route = "/app/student-applicant"
				item.enabled = 1
				updated = True
		
		if updated:
			portal_settings.save(ignore_permissions=True)
			frappe.db.commit()
			frappe.logger().info("Portal Settings menu updated")
			# Clear cache
			frappe.clear_cache()
			portal_settings.clear_cache()
		
		return updated
	except Exception as e:
		frappe.logger().error(f"Error fixing portal menu: {str(e)}")
		return False

