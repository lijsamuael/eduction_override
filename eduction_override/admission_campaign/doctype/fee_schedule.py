import frappe
from frappe.query_builder import DocType
from frappe.query_builder.functions import Sum

from education.education.doctype.fee_schedule.fee_schedule import FeeSchedule


class CustomFeeSchedule(FeeSchedule):
	def validate_total_against_fee_strucuture(self):
		"""Use query builder to aggregate totals without raw SQL strings."""
		FeeScheduleDoctype = DocType("Fee Schedule")

		result = (
			frappe.qb.from_(FeeScheduleDoctype)
			.select(Sum(FeeScheduleDoctype.total_amount).as_("total"))
			.where(FeeScheduleDoctype.fee_structure == self.fee_structure)
			.run(as_dict=True)
		)

		fee_schedules_total = (result and result[0].get("total")) or 0
		fee_structure_total = (
			frappe.db.get_value("Fee Structure", self.fee_structure, "total_amount") or 0
		)

		if fee_schedules_total > fee_structure_total:
			frappe.msgprint(
				"Total amount of Fee Schedules exceeds the Total Amount of Fee Structure",
				alert=True,
			)

