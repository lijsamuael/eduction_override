# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.model.document import Document
from frappe.utils import cint
import json


class BulkFeeInvoiceCreation(Document):
	def validate(self):
		self.calculate_summary()

	def calculate_summary(self):
		"""Calculate total classes, sections, and students from database."""
		if not self.name:
			self.total_classes = 0
			self.total_sections = 0
			self.total_students = 0
			return

		# Fetch from database using new Bulk Fee Invoice Creation Row structure
		rows = frappe.get_all(
			"Bulk Fee Invoice Creation Row",
			filters={"bulk_fee_invoice_creation": self.name},
			fields=["name", "program"]
		)

		unique_programs = set()
		total_sections = 0
		total_students = 0

		for row in rows:
			row_doc = frappe.get_doc("Bulk Fee Invoice Creation Row", row.name)
			
			program_name = row_doc.program
			if program_name:
				unique_programs.add(program_name)
			
			if row_doc.sections:
				total_sections += len(row_doc.sections)
				for section_row in row_doc.sections:
					section_name = section_row.section
					if section_name:
						student_count = frappe.db.count(
							"Student Group Student",
							filters={"parent": section_name, "active": 1}
						)
						total_students += cint(student_count)

		self.total_classes = len(unique_programs)
		self.total_sections = total_sections
		self.total_students = total_students

	@frappe.whitelist()
	def create_fee_schedules(self):
		"""Create fee schedules for all selected sections."""
		if not self.name:
			frappe.throw(_("Please save the document first."))
		
		# Reload to ensure fee_components are loaded
		self.reload()

		# Fetch from database - using new Bulk Fee Invoice Creation Row structure
		rows = frappe.get_all(
			"Bulk Fee Invoice Creation Row",
			filters={"bulk_fee_invoice_creation": self.name},
			fields=["name", "program"]
		)

		if not rows:
			frappe.throw(_("Please add at least one program with sections."))

		if not self.fee_structure:
			frappe.throw(_("Please select Fee Structure"))

		self.db_set("status", "In Process")
		created_schedules = []
		errors = []

		fee_structure_doc = frappe.get_doc("Fee Structure", self.fee_structure)
		academic_year = None
		academic_term = None
		student_category = fee_structure_doc.student_category

		# Get academic year and term from first section if available
		for row in rows:
			row_doc = frappe.get_doc("Bulk Fee Invoice Creation Row", row.name)
			if row_doc.sections and len(row_doc.sections) > 0:
				first_section = row_doc.sections[0].section
				if first_section:
					section_doc = frappe.get_doc("Student Group", first_section)
					academic_year = section_doc.academic_year
					academic_term = section_doc.academic_term
					break

		# Process each row - create ONE fee schedule per row with ALL sections attached
		for row in rows:
			row_doc = frappe.get_doc("Bulk Fee Invoice Creation Row", row.name)
			
			if not row_doc.sections:
				continue

			# Collect all sections from this row
			section_names = []
			for section_row in row_doc.sections:
				section_name = section_row.section
				if section_name:
					section_names.append(section_name)

			if not section_names:
				continue

			try:
				# Create ONE fee schedule for this row with ALL sections
				# Pass self to access fee_components from bulk creation
				fee_schedule = self._create_fee_schedule_for_row(
					row_doc,
					section_names,
					fee_structure_doc,
					academic_year,
					academic_term,
					student_category,
					self
				)
				
				created_schedules.append({
					"fee_schedule": fee_schedule.name,
					"row_name": row.name,
					"status": fee_schedule.status
				})

			except Exception as e:
				error_msg = f"Error creating fee schedule for row {row.name}: {str(e)}"
				errors.append(error_msg)
				frappe.log_error(
					title=f"Bulk Fee Invoice Creation Error",
					message=error_msg
				)

		# Reload to get fresh data including fee_components
		self.reload()
		
		if errors:
			self.error_log = "\n".join(errors)
			self.status = "Failed"
			frappe.msgprint(
				_("Some fee schedules could not be created. Please check Error Log."),
				alert=True
			)
		else:
			self.error_log = None
			self.status = "Completed"
			frappe.msgprint(
				_("Successfully created {0} fee schedule(s)").format(len(created_schedules)),
				indicator="green"
			)

		self.save()
		return {
			"created": len(created_schedules),
			"errors": len(errors),
			"schedules": [s["fee_schedule"] for s in created_schedules]
		}

	def _create_fee_schedule_for_row(self, row_doc, section_names, fee_structure_doc, academic_year, academic_term, student_category, bulk_doc=None):
		"""Create a single fee schedule for a row with all sections attached."""
		# Get section details from first section for defaults
		first_section_doc = frappe.get_doc("Student Group", section_names[0])
		
		# Get currency from company if not in fee structure
		currency = None
		if hasattr(fee_structure_doc, 'currency') and fee_structure_doc.currency:
			currency = fee_structure_doc.currency
		else:
			# Get currency from company
			import erpnext
			if self.company:
				currency = erpnext.get_company_currency(self.company)
			else:
				currency = frappe.db.get_single_value("System Settings", "default_currency") or "USD"
		
		# Get account and receivable_account safely - check if attributes exist
		account = None
		if hasattr(self, 'account') and self.account:
			account = self.account
		elif hasattr(fee_structure_doc, 'account') and fee_structure_doc.account:
			account = fee_structure_doc.account
		
		receivable_account = None
		if hasattr(self, 'receivable_account') and self.receivable_account:
			receivable_account = self.receivable_account
		elif hasattr(fee_structure_doc, 'receivable_account') and fee_structure_doc.receivable_account:
			receivable_account = fee_structure_doc.receivable_account
		
		# Get other optional fields safely
		cost_center = None
		if hasattr(self, 'cost_center') and self.cost_center:
			cost_center = self.cost_center
		
		letter_head = None
		if hasattr(self, 'letter_head') and self.letter_head:
			letter_head = self.letter_head
		
		select_print_heading = None
		if hasattr(self, 'select_print_heading') and self.select_print_heading:
			select_print_heading = self.select_print_heading
		
		# Use program from row_doc if available, otherwise from first section or fee structure
		program = row_doc.program or first_section_doc.program or fee_structure_doc.program
		
		# Get late fine configuration from bulk creation
		allow_late_fine = 0
		fine_frequency = None
		late_fine_amount = 0
		late_fine_from = None
		late_fine_description = None
		
		if hasattr(self, 'allow_late_fine') and self.allow_late_fine:
			allow_late_fine = 1
			fine_frequency = getattr(self, 'fine_frequency', None)
			late_fine_amount = getattr(self, 'late_fine_amount', 0) or 0
			late_fine_from = getattr(self, 'late_fine_from', None)
			late_fine_description = getattr(self, 'late_fine_description', None)
		
		fee_schedule = frappe.get_doc({
			"doctype": "Fee Schedule",
			"fee_structure": self.fee_structure,
			"posting_date": self.posting_date,
			"due_date": self.due_date,
			"academic_year": academic_year or first_section_doc.academic_year,
			"academic_term": academic_term or first_section_doc.academic_term,
			"student_category": student_category or first_section_doc.student_category,
			"program": program,
			"company": self.company,
			"send_email": self.send_email,
			"currency": currency,
			"account": account,
			"receivable_account": receivable_account,
			"cost_center": cost_center,
			"letter_head": letter_head,
			"select_print_heading": select_print_heading,
			"custom_allow_late_fine": allow_late_fine,
			"custom_fine_frequency": fine_frequency,
			"custom_late_fine_amount": late_fine_amount,
			"custom_late_fine_from": late_fine_from,
			"custom_description": late_fine_description,
		})

		# Add ALL sections from this row to the fee schedule with student counts
		# Use simple count like in bulk creation - count active students in Student Group Student table
		for section_name in section_names:
			# Calculate total students for this section - simple count of active students
			# This matches the method used in bulk creation calculate_summary
			student_count = frappe.db.count(
				"Student Group Student",
				filters={"parent": section_name, "active": 1}
			)
			
			fee_schedule.append("student_groups", {
				"student_group": section_name,
				"total_students": cint(student_count) or 0
			})

		# Add fee components from bulk creation document (priority) or fee structure (fallback)
		components_to_use = []
		if bulk_doc and hasattr(bulk_doc, 'fee_components') and bulk_doc.fee_components:
			# Use components from bulk creation document
			components_to_use = bulk_doc.fee_components
			frappe.log_error(
				title="Fee Components Debug",
				message=f"Using {len(components_to_use)} components from bulk creation"
			)
		elif fee_structure_doc and hasattr(fee_structure_doc, 'components') and fee_structure_doc.components:
			# Fall back to fee structure components
			components_to_use = fee_structure_doc.components
			frappe.log_error(
				title="Fee Components Debug",
				message=f"Using {len(components_to_use)} components from fee structure (fallback)"
			)
		
		# Add all components to fee schedule
		for component in components_to_use:
			fee_schedule.append("components", {
				"fees_category": component.fees_category or "",
				"description": component.description or "",
				"amount": component.amount or 0,
				"item": component.item or "",
				"discount": component.discount or 0,
				"total": component.total or component.amount or 0,
			})

		fee_schedule.insert()
		
		# After insert, the validate method may have recalculated total_students
		# Re-set the student counts to ensure they match the bulk creation values
		fee_schedule.reload()
		for student_group_row in fee_schedule.student_groups:
			# Recalculate using simple count (same as bulk creation)
			student_count = frappe.db.count(
				"Student Group Student",
				filters={"parent": student_group_row.student_group, "active": 1}
			)
			student_group_row.total_students = cint(student_count) or 0
		
		# Save again to persist the student counts
		fee_schedule.save()
		
		return fee_schedule
