import frappe
from education.education.doctype.student_admission.student_admission import StudentAdmission as BaseStudentAdmission


class StudentAdmission(BaseStudentAdmission):
	def get_context(self, context):
		"""Override to add webform_route to context and use custom template"""
		# Call parent method first
		super().get_context(context)
		
		# Get webform_route from field, or fetch from web_form if not set
		webform_route = self.webform_route
		if not webform_route and self.web_form:
			# Fetch route from Web Form document
			webform_route = frappe.db.get_value("Web Form", self.web_form, "route")
		
		# Default to 'student-applicant' if still not set
		context.webform_route = webform_route or "student-applicant"
		
		# Override template path to use our custom template
		# This allows us to customize the template without modifying the education app
		context.template = "eduction_override/education/doctype/student_admission/templates/student_admission.html"
		
		return context

