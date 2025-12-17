# Copyright (c) 2025, Eduction Override and contributors
# License: MIT. See LICENSE

import frappe


def test_and_fix_all():
	"""Comprehensive test and fix for Student Applicant menu and redirect"""
	print("=" * 60)
	print("Testing and Fixing Student Applicant Menu and Redirect")
	print("=" * 60)
	
	# 1. Fix Portal Settings
	print("\n1. Fixing Portal Settings...")
	from eduction_override.eduction_override.fix_portal_menu import fix_student_applicant_menu
	result = fix_student_applicant_menu()
	print(f"   Portal Settings fixed: {result}")
	
	# 2. Verify menu item
	print("\n2. Verifying menu item...")
	ps = frappe.get_doc("Portal Settings", "Portal Settings")
	student_applicant_items = [item for item in ps.menu if item.title == "Student Applicant"]
	
	if not student_applicant_items:
		print("   ERROR: No Student Applicant menu item found!")
		print("   Adding menu item from hooks...")
		ps.sync_menu()
		ps.save(ignore_permissions=True)
		frappe.db.commit()
		student_applicant_items = [item for item in ps.menu if item.title == "Student Applicant"]
	
	if student_applicant_items:
		item = student_applicant_items[0]
		print(f"   ✓ Found menu item:")
		print(f"     - Title: {item.title}")
		print(f"     - Route: {item.route}")
		print(f"     - Role: {item.role}")
		print(f"     - Enabled: {item.enabled}")
		print(f"     - Reference: {item.reference_doctype}")
		
		# Ensure it's correct
		if item.route != "/app/student-applicant":
			print(f"   ⚠️  Route is wrong, fixing...")
			item.route = "/app/student-applicant"
			ps.save(ignore_permissions=True)
			frappe.db.commit()
			print(f"   ✓ Fixed route to /app/student-applicant")
		
		if not item.enabled:
			print(f"   ⚠️  Item is disabled, enabling...")
			item.enabled = 1
			ps.save(ignore_permissions=True)
			frappe.db.commit()
			print(f"   ✓ Enabled menu item")
	
	# 3. Clear all caches
	print("\n3. Clearing all caches...")
	frappe.clear_cache()
	ps.clear_cache()
	# Clear portal menu cache for all users
	frappe.cache().delete_value("portal_menu_items")
	print("   ✓ All caches cleared")
	
	# 4. Test redirect files exist
	print("\n4. Checking redirect files...")
	import os
	app_path = frappe.get_app_path("eduction_override")
	utils_file = os.path.join(app_path, "eduction_override", "eduction_override", "utils.py")
	www_file = os.path.join(app_path, "www", "student_applicant_list.py")
	
	if os.path.exists(utils_file):
		print(f"   ✓ utils.py exists")
	else:
		print(f"   ✗ utils.py missing!")
	
	if os.path.exists(www_file):
		print(f"   ✓ student_applicant_list.py exists")
	else:
		print(f"   ✗ student_applicant_list.py missing!")
	
	# 5. Test redirect function
	print("\n5. Testing redirect logic...")
	try:
		from eduction_override.eduction_override.utils import before_request
		print("   ✓ before_request function imported successfully")
	except Exception as e:
		print(f"   ✗ Error importing before_request: {e}")
	
	# 6. Check hooks
	print("\n6. Checking hooks configuration...")
	hooks = frappe.get_hooks("standard_portal_menu_items")
	student_hooks = [h for h in hooks if 'student' in h.get('title', '').lower() and 'applicant' in h.get('title', '').lower()]
	if student_hooks:
		print(f"   ✓ Found hook: {student_hooks[0]}")
	else:
		print(f"   ✗ No Student Applicant hook found!")
	
	before_request_hooks = frappe.get_hooks("before_request")
	if "eduction_override.eduction_override.utils.before_request" in before_request_hooks:
		print(f"   ✓ before_request hook configured")
	else:
		print(f"   ✗ before_request hook not configured!")
	
	# 7. Final sync
	print("\n7. Final menu sync...")
	ps.sync_menu()
	ps.save(ignore_permissions=True)
	frappe.db.commit()
	frappe.clear_cache()
	ps.clear_cache()
	print("   ✓ Menu synced and saved")
	
	print("\n" + "=" * 60)
	print("Test and Fix Complete!")
	print("=" * 60)
	print("\nNext steps:")
	print("1. Clear your browser cache (Ctrl+Shift+Delete)")
	print("2. Log out and log back in")
	print("3. Make sure you're logged in as a user with 'Student' role")
	print("4. Check the portal menu - Student Applicant should be visible")
	print("5. Click it - it should go to /app/student-applicant")
	print("=" * 60)

