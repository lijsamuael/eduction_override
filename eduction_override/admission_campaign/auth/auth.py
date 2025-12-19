import frappe


def on_login(login_manager):
	"""Override redirect for Student role users to go to /student-portal"""
	user_roles = frappe.get_roles(login_manager.user)
	
	if "Student" in user_roles:
		frappe.local.flags.student_redirect = True
		frappe.logger().info(f"Student role detected for {login_manager.user}, will redirect to /student-portal")
		# Set home_page directly in response
		if hasattr(frappe.local, 'response'):
			frappe.local.response["home_page"] = "/student-portal"
			frappe.logger().info(f"✓ Set home_page to /student-portal for {login_manager.user}")


# Monkey-patch set_user_info to check for Student role
original_set_user_info = None

def patch_login_manager():
	"""Patch LoginManager.set_user_info to redirect Student role users"""
	global original_set_user_info
	from frappe.auth import LoginManager
	
	if original_set_user_info is None:
		original_set_user_info = LoginManager.set_user_info
		
		def patched_set_user_info(self, resume=False):
			# Call original method first
			original_set_user_info(self, resume)
			
			# Override for Student role users - check directly
			if not resume:
				try:
					user_roles = frappe.get_roles(self.user)
					if "Student" in user_roles:
						frappe.local.response["home_page"] = "/student-portal"
						frappe.logger().info(f"✓ Overriding home_page to /student-portal for {self.user} (roles: {user_roles})")
				except Exception as e:
					frappe.logger().error(f"Error in patched_set_user_info: {str(e)}")
		
		LoginManager.set_user_info = patched_set_user_info
		frappe.logger().info("LoginManager.set_user_info patched successfully")

# Apply patch when module is imported
try:
	patch_login_manager()
except Exception as e:
	frappe.logger().error(f"Error patching LoginManager: {str(e)}")
