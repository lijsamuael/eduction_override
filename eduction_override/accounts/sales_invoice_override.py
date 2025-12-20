# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice
from frappe.utils import getdate, today


class CustomSalesInvoice(SalesInvoice):
	def validate(self):
		"""Override validate to set custom_payment_status to Overdue if due date is reached."""
		# Call parent validate first
		super().validate()
		
		# Set custom_payment_status based on due date
		self.set_custom_payment_status()
	
	def set_custom_payment_status(self):
		"""Set custom_payment_status to Overdue if due date has passed and invoice is not paid."""
		if not self.due_date:
			return
		
		# Only set if custom_payment_status field exists
		if not hasattr(self, 'custom_payment_status'):
			return
		
		due_date = getdate(self.due_date)
		current_date = getdate(today())
		
		# Check if due date has been reached (due_date <= current_date)
		if due_date <= current_date:
			# Due date has been reached
			if self.outstanding_amount > 0:
				# Invoice is still outstanding, set to Overdue
				self.custom_payment_status = "Overdue"
			elif self.outstanding_amount == 0:
				# Fully paid
				self.custom_payment_status = "Paid"
			elif self.outstanding_amount > 0 and self.outstanding_amount < self.grand_total:
				# Partially paid
				self.custom_payment_status = "Partially Paid"
		else:
			# Due date hasn't been reached yet
			if self.outstanding_amount > 0:
				# Still unpaid but not overdue yet
				if not self.custom_payment_status:
					self.custom_payment_status = "Unpaid"
			elif self.outstanding_amount == 0:
				# Fully paid
				self.custom_payment_status = "Paid"
			elif self.outstanding_amount > 0 and self.outstanding_amount < self.grand_total:
				# Partially paid
				self.custom_payment_status = "Partially Paid"
