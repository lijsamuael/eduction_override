import frappe
from frappe.utils import random_string, today
from education.education.doctype.student_applicant.student_applicant import StudentApplicant


class CustomStudentApplicant(StudentApplicant):
	def after_insert(self):
		"""Create user and Student when Student Applicant is submitted via webform
		This allows us to return username and password immediately
		"""
		frappe.logger().info(f"CustomStudentApplicant.after_insert called for: {self.name}")
		
		# Only create user if email is provided and user doesn't exist
		user_created = False
		if self.student_email_id and not frappe.db.exists("User", self.student_email_id):
			frappe.logger().info(f"Email provided: {self.student_email_id}, User doesn't exist")
			
			# Check if user creation should be skipped
			user_creation_skip = frappe.db.get_single_value("Education Settings", "user_creation_skip")
			frappe.logger().info(f"User creation skip setting: {user_creation_skip}")
			
			if not user_creation_skip:
				# Generate password
				generated_password = random_string(10)
				frappe.logger().info(f"Generated password: {generated_password}")
				
				# Temporarily switch to Administrator to create User
				original_user = frappe.session.user
				try:
					frappe.set_user("Administrator")
					frappe.flags.ignore_permissions = True
					
					# Create user using new_doc and insert
					student_user = frappe.new_doc("User")
					student_user.update({
						"first_name": self.first_name,
						"last_name": self.last_name,
						"email": self.student_email_id,
						"gender": self.gender,
						"send_welcome_email": 0,  # Don't send email, we'll return password in response
						"user_type": "Website User",
						"new_password": generated_password,
					})
					student_user.insert(ignore_permissions=True)
					student_user.add_roles("Student")
					student_user.save(ignore_permissions=True)
					
					frappe.logger().info(f"User created successfully: {student_user.name}")
					user_created = True
					
					# Store password and username in flags for webform response
					frappe.flags.student_applicant_user_password = generated_password
					frappe.flags.student_applicant_username = student_user.name
					
					frappe.logger().info(f"Flags set - username: {frappe.flags.student_applicant_username}, password set: {bool(frappe.flags.student_applicant_user_password)}")
				except Exception as e:
					frappe.logger().error(f"Error creating user: {str(e)}")
					frappe.log_error(f"Error creating user in Student Applicant: {str(e)}", frappe.get_traceback())
				finally:
					# Always restore original user and flags
					frappe.flags.ignore_permissions = False
					if frappe.session.user != original_user:
						frappe.set_user(original_user)
			else:
				frappe.logger().info("User creation is skipped in Education Settings")
		else:
			if not self.student_email_id:
				frappe.logger().info("No email provided in Student Applicant")
			else:
				frappe.logger().info(f"User already exists: {self.student_email_id}")
		
		# Create Student document from Student Applicant
		self.create_student_from_applicant()
	
	def create_student_from_applicant(self):
		"""Create a Student document from this Student Applicant"""
		# Check if Student already exists for this applicant
		if frappe.db.exists("Student", {"student_applicant": self.name}):
			frappe.logger().info(f"Student already exists for applicant: {self.name}")
			return
		
		# Check if Student already exists with same email
		if self.student_email_id and frappe.db.exists("Student", {"student_email_id": self.student_email_id}):
			frappe.logger().info(f"Student already exists with email: {self.student_email_id}")
			return
		
		# Temporarily switch to Administrator to create Student
		original_user = frappe.session.user
		try:
			frappe.set_user("Administrator")
			frappe.flags.ignore_permissions = True
			
			# Map fields from Student Applicant to Student
			student_data = {
				"doctype": "Student",
				"student_applicant": self.name,
				"first_name": self.first_name,
				"middle_name": self.middle_name or "",
				"last_name": self.last_name or "",
				"student_email_id": self.student_email_id,
				"student_mobile_number": self.student_mobile_number or "",
				"date_of_birth": self.date_of_birth,
				"gender": self.gender,
				"blood_group": self.blood_group or "",
				"nationality": self.nationality or "",
				"address_line_1": self.address_line_1 or "",
				"address_line_2": self.address_line_2 or "",
				"city": self.city or "",
				"state": self.state or "",
				"pincode": self.pincode or "",
				"country": self.country or "",
				"image": self.image or "",
				"joining_date": today(),  # Set joining date to today
			}
			
			# Set user if it exists
			if self.student_email_id and frappe.db.exists("User", self.student_email_id):
				student_data["user"] = self.student_email_id
			
			# Create Student document
			student = frappe.get_doc(student_data)
			
			# Copy guardians if they exist
			if hasattr(self, "guardians") and self.guardians:
				for guardian in self.guardians:
					student.append("guardians", {
						"guardian": guardian.guardian,
						"guardian_name": guardian.guardian_name,
						"relation": guardian.relation,
						"mobile_number": guardian.mobile_number,
						"email_address": guardian.email_address,
						"alternate_phone_number": guardian.alternate_phone_number,
						"occupation": guardian.occupation,
						"address": guardian.address,
					})
			
			# Copy siblings if they exist
			if hasattr(self, "siblings") and self.siblings:
				for sibling in self.siblings:
					student.append("siblings", {
						"first_name": sibling.first_name,
						"last_name": sibling.last_name,
						"gender": sibling.gender,
						"date_of_birth": sibling.date_of_birth,
					})
			
			student.save(ignore_permissions=True)
			
			frappe.logger().info(f"Student created successfully: {student.name} from applicant: {self.name}")
			
			# Update applicant status to Admitted
			frappe.db.set_value("Student Applicant", self.name, "application_status", "Admitted")
		except Exception as e:
			frappe.logger().error(f"Error creating Student from applicant: {str(e)}")
			frappe.log_error(f"Error creating Student from applicant: {str(e)}", frappe.get_traceback())
		finally:
			# Always restore original user and flags
			frappe.flags.ignore_permissions = False
			if frappe.session.user != original_user:
				frappe.set_user(original_user)

