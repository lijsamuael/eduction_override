import frappe
from frappe.utils import random_string
from education.education.doctype.student_applicant.student_applicant import StudentApplicant


class CustomStudentApplicant(StudentApplicant):
	def after_insert(self):
		"""Create user when Student Applicant is submitted via webform
		This allows us to return username and password immediately
		"""
		frappe.logger().info(f"CustomStudentApplicant.after_insert called for: {self.name}")
		
		# Only create user if email is provided and user doesn't exist
		if self.student_email_id and not frappe.db.exists("User", self.student_email_id):
			frappe.logger().info(f"Email provided: {self.student_email_id}, User doesn't exist")
			
			# Check if user creation should be skipped
			user_creation_skip = frappe.db.get_single_value("Education Settings", "user_creation_skip")
			frappe.logger().info(f"User creation skip setting: {user_creation_skip}")
			
			if not user_creation_skip:
				# Generate password
				generated_password = random_string(10)
				frappe.logger().info(f"Generated password: {generated_password}")
				
				try:
					# Create user
					student_user = frappe.get_doc(
						{
							"doctype": "User",
							"first_name": self.first_name,
							"last_name": self.last_name,
							"email": self.student_email_id,
							"gender": self.gender,
							"send_welcome_email": 0,  # Don't send email, we'll return password in response
							"user_type": "Website User",
							"new_password": generated_password,
						}
					)
					student_user.add_roles("Student")
					student_user.save(ignore_permissions=True)
					
					frappe.logger().info(f"User created successfully: {student_user.name}")
					
					# Store password and username in flags for webform response
					frappe.flags.student_applicant_user_password = generated_password
					frappe.flags.student_applicant_username = student_user.name
					
					frappe.logger().info(f"Flags set - username: {frappe.flags.student_applicant_username}, password set: {bool(frappe.flags.student_applicant_user_password)}")
				except Exception as e:
					frappe.logger().error(f"Error creating user: {str(e)}")
					frappe.log_exception()
			else:
				frappe.logger().info("User creation is skipped in Education Settings")
		else:
			if not self.student_email_id:
				frappe.logger().info("No email provided in Student Applicant")
			else:
				frappe.logger().info(f"User already exists: {self.student_email_id}")

