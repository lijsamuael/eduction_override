import frappe
from frappe.utils import random_string
from education.education.doctype.student.student import Student


class CustomStudent(Student):
	def validate_user(self):
		"""Create a website user for student creation if not already exists
		Override to capture the generated password for webform response
		Note: If user was already created during Student Applicant submission,
		we'll just link it to the Student
		"""
		if not frappe.db.get_single_value(
			"Education Settings", "user_creation_skip"
		):
			# Check if user already exists (might have been created during Student Applicant submission)
			if frappe.db.exists("User", self.student_email_id):
				# User already exists, just link it
				self.user = self.student_email_id
			else:
				# Generate password before creating user
				generated_password = random_string(10)
				
				student_user = frappe.get_doc(
					{
						"doctype": "User",
						"first_name": self.first_name,
						"last_name": self.last_name,
						"email": self.student_email_id,
						"gender": self.gender,
						"send_welcome_email": 1,
						"user_type": "Website User",
						"new_password": generated_password,
					}
				)
				student_user.add_roles("Student")
				student_user.save(ignore_permissions=True)

				self.user = student_user.name
				
				# Store password in flags to retrieve later in webform response
				# This will be available when Student is created from Student Applicant
				frappe.flags.student_user_password = generated_password
				frappe.flags.student_username = student_user.name

