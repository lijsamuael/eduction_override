import frappe


def execute():
	"""
	Migration: Remove Additional Settings fields from Bulk Fee Invoice Creation doctype.
	This patch removes the fields from the database table if they exist.
	"""
	doctype = "Bulk Fee Invoice Creation"
	fields_to_remove = [
		"account",
		"receivable_account",
		"cost_center",
		"letter_head",
		"select_print_heading"
	]
	
	# Check if table exists
	if not frappe.db.exists("DocType", doctype):
		return
	
	# Remove columns from database table if they exist
	for fieldname in fields_to_remove:
		if frappe.db.has_column(doctype, fieldname):
			try:
				frappe.db.sql(f"ALTER TABLE `tab{doctype}` DROP COLUMN `{fieldname}`")
				frappe.db.commit()
				print(f"Removed column {fieldname} from {doctype}")
			except Exception as e:
				print(f"Error removing column {fieldname} from {doctype}: {str(e)}")
				frappe.db.rollback()

