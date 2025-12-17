import json
import frappe
from frappe import _
from frappe.rate_limiter import rate_limit
from frappe.utils import random_string, today
from frappe.website.doctype.web_form.web_form import accept as original_accept


@frappe.whitelist(allow_guest=True)
@rate_limit(key="web_form", limit=10, seconds=60)
def accept(web_form, data):
	"""Override webform accept to return username and password for Student Applicant submissions"""
	
	frappe.logger().info(f"Custom webform accept called for: {web_form}")
	
	# Check if this is a Student Applicant webform BEFORE calling original_accept
	web_form_doc = frappe.get_doc("Web Form", web_form)
	is_student_applicant = web_form_doc.doc_type == "Student Applicant"
	
	# Filter out 'company' field for Student Applicant webform
	# This field doesn't exist in Student Applicant doctype and causes validation errors
	# Reference: https://github.com/frappe/education/issues/316
	if is_student_applicant:
		# Parse the data (it's always a JSON string from the frontend)
		data_dict = json.loads(data)
		if 'company' in data_dict:
			del data_dict['company']
			frappe.logger().info("Removed 'company' field from Student Applicant webform data")
			# Convert back to JSON string
			data = json.dumps(data_dict)
	
	# Call the original accept method
	doc = original_accept(web_form, data)
	
	frappe.logger().info(f"Original accept returned doc: {doc.name if hasattr(doc, 'name') else 'No name'}")
	
	# If this is a Student Applicant webform, create user and return credentials
	if is_student_applicant:
		student_applicant = doc
		frappe.logger().info(f"Processing Student Applicant: {student_applicant.name}")
		frappe.logger().info(f"Student email: {student_applicant.student_email_id}")
		
		username = None
		password = None
		
		# Create user if email is provided and user doesn't exist
		if student_applicant.student_email_id:
			# Check if user already exists
			user_exists = frappe.db.exists("User", student_applicant.student_email_id)
			
			if not user_exists:
				# Check if user creation should be skipped
				user_creation_skip = frappe.db.get_single_value("Education Settings", "user_creation_skip")
				
				if not user_creation_skip:
					try:
						# Generate password
						generated_password = random_string(10)
						frappe.logger().info(f"Generating password for new user")
						
						# Temporarily switch to Administrator to create User
						original_user = frappe.session.user
						try:
							frappe.set_user("Administrator")
							frappe.flags.ignore_permissions = True
							
							# Create user using new_doc and insert
							student_user = frappe.new_doc("User")
							student_user.update({
								"first_name": student_applicant.first_name,
								"last_name": student_applicant.last_name,
								"email": student_applicant.student_email_id,
								"gender": student_applicant.gender or "",
								"send_welcome_email": 0,  # Don't send email, we'll return password in response
								"user_type": "Website User",
								"new_password": generated_password,
							})
							student_user.insert(ignore_permissions=True)
						student_user.add_roles("Student")
						student_user.save(ignore_permissions=True)
						finally:
							# Always restore original user and flags
							frappe.flags.ignore_permissions = False
							if frappe.session.user != original_user:
								frappe.set_user(original_user)
						
						username = student_user.name
						password = generated_password
						
						frappe.logger().info(f"User created successfully: {username}")
					except Exception as e:
						frappe.logger().error(f"Error creating user: {str(e)}")
						frappe.log_error(f"Error creating user in webform: {str(e)}", frappe.get_traceback())
				else:
					frappe.logger().info("User creation is skipped in Education Settings")
			else:
				frappe.logger().info(f"User already exists: {student_applicant.student_email_id}")
				username = student_applicant.student_email_id
		
		# Create Student document from Student Applicant
		# This ensures Student is created even if after_insert fails
		try:
			create_student_from_applicant(student_applicant, username)
		except Exception as e:
			frappe.logger().error(f"Error creating Student: {str(e)}")
			frappe.log_error(f"Error creating Student in webform: {str(e)}", frappe.get_traceback())
		
		# Convert doc to dict and add credentials if available
		doc_dict = doc.as_dict(no_nulls=True)
		
		if username and password:
			doc_dict['username'] = username
			doc_dict['password'] = password
			doc_dict['credentials_generated'] = True
			frappe.logger().info(f"Returning credentials in response for: {username}")
		elif username:
			doc_dict['username'] = username
			doc_dict['user_exists'] = True
			frappe.logger().info(f"Returning user exists message for: {username}")
		
		# Return dict with credentials
		return doc_dict
	
	# Return doc for other doctypes
	return doc


def create_student_from_applicant(student_applicant, username=None):
	"""Create a Student document from Student Applicant"""
	# Check if Student already exists for this applicant
	if frappe.db.exists("Student", {"student_applicant": student_applicant.name}):
		frappe.logger().info(f"Student already exists for applicant: {student_applicant.name}")
		return
	
	# Check if Student already exists with same email
	if student_applicant.student_email_id and frappe.db.exists("Student", {"student_email_id": student_applicant.student_email_id}):
		frappe.logger().info(f"Student already exists with email: {student_applicant.student_email_id}")
		return
	
	# Temporarily switch to Administrator to create Student
	original_user = frappe.session.user
	try:
		frappe.set_user("Administrator")
		frappe.flags.ignore_permissions = True
		
		# Create Student document using new_doc
		student = frappe.new_doc("Student")
		student.update({
			"student_applicant": student_applicant.name,
			"first_name": student_applicant.first_name,
			"middle_name": student_applicant.middle_name or "",
			"last_name": student_applicant.last_name or "",
			"student_email_id": student_applicant.student_email_id,
			"student_mobile_number": student_applicant.student_mobile_number or "",
			"date_of_birth": student_applicant.date_of_birth,
			"gender": student_applicant.gender,
			"blood_group": student_applicant.blood_group or "",
			"nationality": student_applicant.nationality or "",
			"address_line_1": student_applicant.address_line_1 or "",
			"address_line_2": student_applicant.address_line_2 or "",
			"city": student_applicant.city or "",
			"state": student_applicant.state or "",
			"pincode": student_applicant.pincode or "",
			"country": student_applicant.country or "",
			"image": student_applicant.image or "",
			"joining_date": today(),  # Set joining date to today
		})
		
		# Set user if it exists
		if username:
			student.user = username
		elif student_applicant.student_email_id and frappe.db.exists("User", student_applicant.student_email_id):
			student.user = student_applicant.student_email_id
		
		# Copy guardians if they exist
		if hasattr(student_applicant, "guardians") and student_applicant.guardians:
			for guardian in student_applicant.guardians:
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
		if hasattr(student_applicant, "siblings") and student_applicant.siblings:
			for sibling in student_applicant.siblings:
				student.append("siblings", {
					"first_name": sibling.first_name,
					"last_name": sibling.last_name,
					"gender": sibling.gender,
					"date_of_birth": sibling.date_of_birth,
				})
		
		student.insert(ignore_permissions=True)
		
		frappe.logger().info(f"Student created successfully: {student.name} from applicant: {student_applicant.name}")
		
		# Update applicant status to Admitted
		frappe.db.set_value("Student Applicant", student_applicant.name, "application_status", "Admitted")
	except Exception as e:
		frappe.logger().error(f"Error creating Student from applicant: {str(e)}")
		frappe.log_error(f"Error creating Student from applicant: {str(e)}", frappe.get_traceback())
		raise
	finally:
		# Always restore original user and flags
		frappe.flags.ignore_permissions = False
		if frappe.session.user != original_user:
			frappe.set_user(original_user)

