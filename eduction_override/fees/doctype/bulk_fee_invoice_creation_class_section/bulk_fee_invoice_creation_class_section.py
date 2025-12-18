# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class BulkFeeInvoiceCreationClassSection(Document):
	pass


@frappe.whitelist()
def get_class_query(doctype, txt, searchfield, start, page_len, filters):
	"""Query to get only classes (Student Groups with group_based_on = 'Batch')"""
	return frappe.db.sql("""
		SELECT name, student_group_name
		FROM `tabStudent Group`
		WHERE disabled = 0
			AND group_based_on = 'Batch'
			AND (name LIKE %(txt)s OR student_group_name LIKE %(txt)s)
		ORDER BY name
		LIMIT %(start)s, %(page_len)s
	""", {
		'txt': f'%{txt}%',
		'start': start,
		'page_len': page_len
	})


@frappe.whitelist()
def get_section_query(doctype, txt, searchfield, start, page_len, filters):
	"""Query to get sections for a given class"""
	class_name = filters.get('class')
	if not class_name:
		return []
	
	# Get class details
	class_doc = frappe.get_doc('Student Group', class_name)
	
	# Get sections (Student Groups with same program and academic year, but different name)
	return frappe.db.sql("""
		SELECT name, student_group_name
		FROM `tabStudent Group`
		WHERE disabled = 0
			AND program = %(program)s
			AND academic_year = %(academic_year)s
			AND name != %(class_name)s
			AND group_based_on = 'Batch'
			AND (name LIKE %(txt)s OR student_group_name LIKE %(txt)s)
		ORDER BY name
		LIMIT %(start)s, %(page_len)s
	""", {
		'program': class_doc.program,
		'academic_year': class_doc.academic_year,
		'class_name': class_name,
		'txt': f'%{txt}%',
		'start': start,
		'page_len': page_len
	})
