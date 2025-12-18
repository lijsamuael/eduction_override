# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

from frappe.model.document import Document
import frappe


class BulkFeeInvoiceCreationRow(Document):
	def validate(self):
		if not self.program:
			frappe.throw("Program is required")
		if not self.sections or len(self.sections) == 0:
			frappe.throw("Please add at least one Section")

