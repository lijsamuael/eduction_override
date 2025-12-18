import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum

from education.education.doctype.fee_schedule.fee_schedule import FeeSchedule


class CustomFeeSchedule(FeeSchedule):
	def validate_total_against_fee_strucuture(self):
		"""Override to disable validation - allow creating fee schedules above fee structure limit.
		This method intentionally does nothing to bypass the base class validation.
		"""
		# Validation disabled - do nothing, allow creating fee schedules regardless of total
		pass
	
	def validate_fee_components(self):
		"""Override to disable validation - allow components from bulk creation even if not in fee structure.
		This method intentionally does nothing to bypass the base class validation.
		"""
		# Validation disabled - allow all components from bulk creation, even if not in fee structure
		pass
	
	def calculate_total_and_program(self):
		"""Override to use simple student count (same as bulk creation) instead of requiring Program Enrollment.
		This ensures student counts match the values shown in bulk creation.
		"""
		import frappe
		from frappe.utils import cint, money_in_words
		
		no_of_students = 0
		for d in self.student_groups:
			# Use simple count of active students (same method as bulk creation)
			# This doesn't require Program Enrollment, so it will always return accurate counts
			if d.student_group:
				student_count = frappe.db.count(
					"Student Group Student",
					filters={"parent": d.student_group, "active": 1}
				)
				d.total_students = cint(student_count) or 0
			else:
				d.total_students = 0
			
			no_of_students += cint(d.total_students)
			
			# Validate the program of fee structure and student groups
			if d.student_group:
				student_group_program = frappe.db.get_value(
					"Student Group", d.student_group, "program"
				)
				if self.program and student_group_program and self.program != student_group_program:
					frappe.msgprint(
						_("Program in the Fee Structure and Student Group {0} are different.").format(
							d.student_group
						)
					)
		
		self.grand_total = no_of_students * self.total_amount
		self.grand_total_in_words = money_in_words(self.grand_total)

