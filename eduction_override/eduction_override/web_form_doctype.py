import frappe
from frappe import _
from frappe.website.doctype.web_form.web_form import WebForm


class CustomWebForm(WebForm):
	def validate_fields(self):
		"""Override validate_fields to skip validation for 'company' field in Student Applicant webforms
		This fixes the issue: https://github.com/frappe/education/issues/316
		The 'company' field exists in the webform JSON but doesn't exist in Student Applicant doctype
		"""
		from frappe.model import no_value_fields
		
		# For Student Applicant webforms, skip validation for 'company' field
		if self.doc_type == "Student Applicant":
			meta = frappe.get_meta(self.doc_type)
			missing = [
				df.fieldname
				for df in self.web_form_fields
				if df.fieldname 
				and df.fieldname != "company"  # Skip company field validation
				and (df.fieldtype not in no_value_fields and not meta.has_field(df.fieldname))
			]
			
			if missing:
				frappe.throw(_("Following fields are missing:") + "<br>" + "<br>".join(missing))
		else:
			# For other webforms, use standard validation
			super().validate_fields()

