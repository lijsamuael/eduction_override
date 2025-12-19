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
	
	def validate(self):
		"""Override validate to skip permission checks for Web Form documents
		This fixes the issue: User Guest does not have doctype access via role permission
		"""
		# Always ignore permissions for Web Form documents to avoid permission checks on target doctypes
		# This allows webform creation for any doctype (User, Student, Student Applicant, etc.)
		self.flags.ignore_permissions = True
		
		# Call parent validate
		super().validate()
	
	def get_invalid_links(self, is_submittable=False):
		"""Override get_invalid_links to skip validation for doc_type field
		This prevents permission check on target doctypes (User, Student, etc.) during link validation
		"""
		from frappe import _dict
		
		invalid_links = []
		cancelled_links = []
		
		# Get all link fields except doc_type
		link_fields = [
			df for df in self.meta.get_link_fields() + self.meta.get("fields", {"fieldtype": ("=", "Dynamic Link")})
			if df.fieldname != "doc_type"  # Skip doc_type field validation
		]
		
		# Validate only non-doc_type links
		for df in link_fields:
			docname = self.get(df.fieldname)
			
			if docname:
				if df.fieldtype == "Link":
					doctype = df.options
					if not doctype:
						frappe.throw(_("Options not set for link field {0}").format(df.fieldname))
				else:
					doctype = self.get(df.options)
					if not doctype:
						frappe.throw(_("{0} must be set first").format(self.meta.get_label(df.options)))
				
				meta = frappe.get_meta(doctype)
				
				if not meta.get("is_virtual"):
					values = _dict(name=frappe.db.get_value(doctype, docname, "name", cache=True))
				else:
					values = frappe.get_doc(doctype, docname).as_dict()
				
				if not values or not values.name:
					def get_msg(df, docname):
						if self.get("parentfield"):
							return "{} #{}: {}: {}".format(_("Row"), self.idx, _(df.label, context=df.parent), docname)
						return f"{_(df.label, context=df.parent)}: {docname}"
					invalid_links.append((df.fieldname, docname, get_msg(df, docname)))
		
		# Also check children
		for d in self.get_all_children():
			result = d.get_invalid_links(is_submittable=self.meta.is_submittable)
			invalid_links.extend(result[0])
			cancelled_links.extend(result[1])
		
		return invalid_links, cancelled_links

