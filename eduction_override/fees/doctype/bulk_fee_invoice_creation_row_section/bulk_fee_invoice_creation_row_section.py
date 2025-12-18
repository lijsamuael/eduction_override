# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe


class BulkFeeInvoiceCreationRowSection(Document):
	pass


@frappe.whitelist()
def get_section_query(doctype, txt, searchfield, start, page_len, filters):
	"""Query to get sections for a given program"""
	# Get program from parent document
	program = None
	if filters:
		program = filters.get('program')
	
	# If no program in filters, try to get from parent
	if not program and filters and filters.get('parent'):
		parent_doc = frappe.get_doc('Bulk Fee Invoice Creation Row', filters.get('parent'))
		program = parent_doc.program
	
	if not program:
		return []
	
	# Get sections (Student Groups) for the selected program
	return frappe.db.sql("""
		SELECT name, student_group_name
		FROM `tabStudent Group`
		WHERE disabled = 0
			AND program = %(program)s
			AND (name LIKE %(txt)s OR student_group_name LIKE %(txt)s)
		ORDER BY name
		LIMIT %(start)s, %(page_len)s
	""", {
		'program': program,
		'txt': f'%{txt}%',
		'start': start,
		'page_len': page_len
	})

