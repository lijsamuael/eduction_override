# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe

# Import the original function
from education.education.doctype.fee_schedule import fee_schedule as fee_schedule_module


# Store the original function
_original_create_sales_invoice = fee_schedule_module.create_sales_invoice

def create_sales_invoice(fee_schedule, student_id, create_sales_order=False):
	"""Override to copy late fine configuration from fee schedule to sales invoice."""
	from education.education.doctype.fee_schedule.fee_schedule import get_customer_from_student, get_fees_mapped_doc
	
	# Get fee schedule to copy late fine configuration
	fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule)
	
	# Create the invoice document (same as base function)
	customer = get_customer_from_student(student_id)
	
	sales_invoice_doc = get_fees_mapped_doc(
		fee_schedule=fee_schedule,
		doctype="Sales Invoice",
		student_id=student_id,
		customer=customer,
	)

	if frappe.db.get_single_value(
		"Education Settings", "sales_invoice_posting_date_fee_schedule"
	):
		sales_invoice_doc.set_posting_time = 1

	for item in sales_invoice_doc.items:
		item.qty = 1
		item.cost_center = ""
	
	# Copy late fine configuration from fee schedule to sales invoice
	if hasattr(fee_schedule_doc, 'custom_allow_late_fine'):
		sales_invoice_doc.custom_has_late_fine = fee_schedule_doc.custom_allow_late_fine or 0
		sales_invoice_doc.custom_fine_frequency = fee_schedule_doc.custom_fine_frequency
		sales_invoice_doc.custom_late_fine_amount = fee_schedule_doc.custom_late_fine_amount or 0
		# Set late fine from date to the due date of the sales invoice
		sales_invoice_doc.custom_late_fine_from = sales_invoice_doc.due_date
	
	# Calculate totals before saving
	sales_invoice_doc.calculate_taxes_and_totals()
	
	# Save the invoice (as draft, not submitted)
	sales_invoice_doc.save()
	frappe.db.commit()

	return sales_invoice_doc.name

