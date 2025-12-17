import frappe
from frappe import _


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

