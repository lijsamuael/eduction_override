# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, getdate

# Import the original function
from education.education.doctype.fee_schedule import fee_schedule as fee_schedule_module


# Store the original function
_original_create_sales_invoice = fee_schedule_module.create_sales_invoice

def create_sales_invoice(fee_schedule, student_id, create_sales_order=False):
	"""Override to add late fine item when creating sales invoice if current date equals late fine date."""
	from education.education.doctype.fee_schedule.fee_schedule import get_customer_from_student, get_fees_mapped_doc
	
	# Get fee schedule to check late fine configuration
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
	
	# Copy late fee configuration from fee schedule to sales invoice
	if hasattr(fee_schedule_doc, 'custom_allow_late_fine'):
		sales_invoice_doc.custom_has_late_fine = fee_schedule_doc.custom_allow_late_fine or 0
		sales_invoice_doc.custom_fine_frequency = fee_schedule_doc.custom_fine_frequency
		sales_invoice_doc.custom_late_fine_amount = fee_schedule_doc.custom_late_fine_amount or 0
		sales_invoice_doc.custom_late_fine_from = fee_schedule_doc.custom_late_fine_from
		sales_invoice_doc.custom_late_fine_description = fee_schedule_doc.custom_description
	
	# Check if late fine should be added (current date >= late fine date)
	should_add_late_fine = (
		fee_schedule_doc.custom_allow_late_fine and 
		fee_schedule_doc.custom_late_fine_from and 
		getdate(today()) >= getdate(fee_schedule_doc.custom_late_fine_from) and
		fee_schedule_doc.custom_late_fine_amount and 
		fee_schedule_doc.custom_late_fine_amount > 0
	)
	
	# Add late fine item before saving if needed
	if should_add_late_fine:
		_add_late_fine_item_to_invoice_doc(
			sales_invoice_doc,
			fee_schedule_doc,
			fee_schedule_doc.custom_late_fine_amount,
			fee_schedule_doc.custom_description
		)
	
	# Calculate totals before saving
	sales_invoice_doc.calculate_taxes_and_totals()
	
	# Save the invoice first
	sales_invoice_doc.save()
	frappe.db.commit()
	
	# Always auto-submit the invoice
	try:
		# Reload to ensure we have the latest data
		sales_invoice_doc.reload()
		
		# Validate before submitting
		sales_invoice_doc.validate()
		
		# Submit the invoice
		sales_invoice_doc.submit()
		frappe.db.commit()
		
	except Exception as e:
		# Log the error - invoice is saved as draft
		error_msg = str(e)
		frappe.log_error(
			title=f"Error auto-submitting invoice {sales_invoice_doc.name}",
			message=f"Error: {error_msg}\n\nInvoice saved as draft. Please submit manually."
		)
		# Don't raise - invoice is already saved as draft
		# The error will be logged for debugging

	return sales_invoice_doc.name


def _add_late_fine_item_to_invoice_doc(invoice_doc, fee_schedule_doc, late_fine_amount, description=None):
	"""Add late fine item to invoice document before saving."""
	# Check if late fine item already exists
	for item in invoice_doc.items:
		# Check by item_code, item_name, or description containing "Late Fine"
		if (item.item_code and "Late Fine" in (item.item_code or "")) or \
		   (item.item_name and "Late Fine" in (item.item_name or "")) or \
		   (item.description and "Late Fine" in (item.description or "")):
			# Late fine already added, skip
			return
	
	# Find Late Fine component in fee schedule
	late_fine_component = None
	for component in fee_schedule_doc.components:
		if component.fees_category == "Late Fine" or "Late Fine" in (component.description or ""):
			late_fine_component = component
			break
	
	# Determine item_code to use
	item_code = None
	item_name = "Late Fine"
	
	if late_fine_component and late_fine_component.item:
		item_code = late_fine_component.item
		item_name = late_fine_component.item
	else:
		# Try to find Late Fine item in Item master
		item_code = frappe.db.get_value("Item", {"item_name": "Late Fine"}, "name")
		if not item_code:
			item_code = frappe.db.get_value("Item", {"item_code": "Late Fine"}, "name")
	
	# Create the item row
	item_row = invoice_doc.append("items", {
		"item_code": item_code,
		"item_name": item_name if not item_code else None,
		"description": description or (late_fine_component.description if late_fine_component else "Late Fine"),
		"qty": 1,
		"rate": late_fine_amount,
		"amount": late_fine_amount
	})
	
	# Set discount if available from component
	if late_fine_component and late_fine_component.discount:
		item_row.discount_percentage = late_fine_component.discount
		# Recalculate amount with discount
		item_row.amount = late_fine_amount - (late_fine_amount * late_fine_component.discount / 100)

