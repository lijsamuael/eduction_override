# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, getdate, flt
from datetime import timedelta


def daily():
	"""Daily scheduler to add late fine items to overdue sales invoices based on fine frequency."""
	process_late_fines_for_overdue_invoices()


def process_late_fines_for_overdue_invoices():
	"""Process late fines for overdue invoices based on custom_fine_frequency.
	
	Logic:
	- If custom_fine_frequency is "Once" and invoice is overdue: add fine once, skip if already added
	- If custom_fine_frequency is "Daily" or "Per Day" and invoice is overdue: add fine amount each day
	"""
	current_date = today()
	
	# Find all overdue sales invoices with late fine configuration
	# Check custom_payment_status instead of status
	# Only process draft invoices (not submitted or cancelled)
	overdue_invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"custom_payment_status": ["in", ["Overdue", "Unpaid"]],  # Check custom_payment_status
			"custom_has_late_fine": 1,
			"custom_late_fine_amount": [">", 0],
			"docstatus": 0  # Only draft invoices (not submitted or cancelled)
		},
		fields=[
			"name", 
			"custom_late_fine_amount", 
			"custom_fine_frequency",
			"due_date",
			"fee_schedule"
		]
	)
	
	if not overdue_invoices:
		return
	
	processed_count = 0
	skipped_count = 0
	error_count = 0
	
	for invoice_data in overdue_invoices:
		invoice_name = invoice_data.name
		late_fine_amount = invoice_data.custom_late_fine_amount or 0
		fine_frequency = invoice_data.custom_fine_frequency or "Once"
		due_date = invoice_data.due_date
		fee_schedule_name = invoice_data.fee_schedule
		
		# Skip if amount is zero
		if late_fine_amount <= 0:
			continue
		
		# Check if invoice is actually overdue (due_date < today)
		if due_date and getdate(due_date) >= getdate(current_date):
			# Not overdue yet, skip
			continue
		
		try:
			# Check current payment status to ensure it's still overdue
			current_payment_status = frappe.db.get_value("Sales Invoice", invoice_name, "custom_payment_status")
			if current_payment_status not in ["Overdue", "Unpaid"]:
				# Status changed, skip
				continue
			
			if fine_frequency == "Once":
				# Add fine once, skip if already added
				added = add_late_fine_once(invoice_name, late_fine_amount, fee_schedule_name)
				if added:
					processed_count += 1
				else:
					skipped_count += 1
			elif fine_frequency in ["Daily", "Per Day"]:
				# Add fine amount each day
				added = add_late_fine_daily(invoice_name, late_fine_amount, fee_schedule_name, due_date)
				if added:
					processed_count += 1
				else:
					skipped_count += 1
			else:
				# Unknown frequency, skip
				skipped_count += 1
				
		except Exception as e:
			error_count += 1
			frappe.log_error(
				title=f"Error processing late fine for invoice {invoice_name}",
				message=f"Error: {str(e)}\nFrequency: {fine_frequency}"
			)
	
	# Log summary
	if processed_count > 0 or error_count > 0:
		frappe.log_error(
			title="Late Fine Scheduler Summary",
			message=f"Processed: {processed_count}, Skipped: {skipped_count}, Errors: {error_count}"
		)


def add_late_fine_once(invoice_name, late_fine_amount, fee_schedule_name):
	"""Add late fine item once to an invoice. Skip if already added.
	
	Only processes draft invoices (not submitted or cancelled).
	"""
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
	
	# Only process draft invoices
	if invoice_doc.docstatus != 0:
		return False
	
	# Check if late fine item already exists
	for item in invoice_doc.items:
		if is_late_fine_item(item):
			# Late fine already added, skip
			return False
	
	# Add late fine item directly (only draft invoices are processed)
	_add_late_fine_item_to_invoice(invoice_doc, late_fine_amount, fee_schedule_name)
	invoice_doc.save()
	frappe.db.commit()
	
	return True


def add_late_fine_daily(invoice_name, late_fine_amount, fee_schedule_name, due_date):
	"""Add late fine amount each day for overdue invoices.
	
	For Daily frequency: adds fine amount each day the invoice is overdue.
	Only processes draft invoices (not submitted or cancelled).
	"""
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
	
	# Only process draft invoices
	if invoice_doc.docstatus != 0:
		return False
	
	current_date = today()
	current_date_obj = getdate(current_date)
	
	# Start from day after due date
	start_date = getdate(due_date) + timedelta(days=1) if due_date else current_date_obj
	
	# Check if current date is past the start date
	if current_date_obj < start_date:
		# Not yet time to add fine
		return False
	
	# Draft invoice - check if late fine item was added today
	# Count existing late fine items
	existing_items = [item for item in invoice_doc.items if is_late_fine_item(item)]
	
	# Calculate how many days we should have fines for
	days_overdue = (current_date_obj - start_date).days + 1
	
	# If we have fewer items than days overdue, add items for missing days
	items_to_add = days_overdue - len(existing_items)
	
	if items_to_add > 0:
		# Add fine items for missing days (including today)
		for day in range(items_to_add):
			_add_late_fine_item_to_invoice(invoice_doc, late_fine_amount, fee_schedule_name)
		invoice_doc.save()
		frappe.db.commit()
	else:
		# Already up to date, skip
		return False
	
	return True


def is_late_fine_item(item):
	"""Check if an item is a late fine item."""
	return (
		(item.item_code and "Late Fine" in (item.item_code or "")) or
		(item.item_name and "Late Fine" in (item.item_name or "")) or
		(item.description and "Late Fine" in (item.description or ""))
	)


def _add_late_fine_item_to_invoice(invoice_doc, late_fine_amount, fee_schedule_name):
	"""Add a late fine item to an invoice document."""
	# Get fee schedule to find the late fine item if available
	late_fine_component = None
	if fee_schedule_name:
		try:
			fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule_name)
			for component in fee_schedule_doc.components:
				if component.fees_category == "Late Fine" or "Late Fine" in (component.description or ""):
					late_fine_component = component
					break
		except Exception:
			pass
	
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
	
	# Get income account from existing items or company defaults
	income_account = None
	if invoice_doc.items:
		income_account = invoice_doc.items[0].income_account
	
	if not income_account:
		# Get from company defaults
		income_account = frappe.db.get_value("Company", invoice_doc.company, "default_income_account")
	
	# Create the item row
	item_row = invoice_doc.append("items", {
		"item_code": item_code,
		"item_name": item_name if not item_code else None,
		"description": late_fine_component.description if late_fine_component else "Late Fine",
		"qty": 1,
		"rate": late_fine_amount,
		"amount": late_fine_amount,
		"income_account": income_account
	})
	
	# Set discount if available from component
	if late_fine_component and late_fine_component.discount:
		item_row.discount_percentage = late_fine_component.discount
		# Recalculate amount with discount
		item_row.amount = late_fine_amount - (late_fine_amount * late_fine_component.discount / 100)
	
	# Calculate totals
	invoice_doc.calculate_taxes_and_totals()


def _create_late_fine_invoice_for_submitted(original_invoice_doc, late_fine_amount, fee_schedule_name):
	"""Create a new invoice for late fine when the original invoice is submitted."""
	# Check if a late fine invoice already exists for this fee schedule today
	current_date = today()
	existing_late_fine_invoice = frappe.db.exists(
		"Sales Invoice",
		{
			"fee_schedule": fee_schedule_name,
			"posting_date": current_date,
			"docstatus": ["<", 2],  # Draft or Submitted
			"name": ["!=", original_invoice_doc.name]
		}
	)
	
	if existing_late_fine_invoice:
		# Late fine invoice already created today, skip
		return
	
	# Get fee schedule to find the late fine item if available
	late_fine_component = None
	if fee_schedule_name:
		try:
			fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule_name)
			for component in fee_schedule_doc.components:
				if component.fees_category == "Late Fine" or "Late Fine" in (component.description or ""):
					late_fine_component = component
					break
		except Exception:
			pass
	
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
	
	# Get income account
	income_account = None
	if original_invoice_doc.items:
		income_account = original_invoice_doc.items[0].income_account
	
	if not income_account:
		income_account = frappe.db.get_value("Company", original_invoice_doc.company, "default_income_account")
	
	# Create a new invoice for the late fine
	late_fine_invoice = frappe.get_doc({
		"doctype": "Sales Invoice",
		"customer": original_invoice_doc.customer,
		"posting_date": today(),
		"due_date": original_invoice_doc.due_date or today(),
		"company": original_invoice_doc.company,
		"currency": original_invoice_doc.currency,
		"conversion_rate": original_invoice_doc.conversion_rate,
		"selling_price_list": original_invoice_doc.selling_price_list,
		"price_list_currency": original_invoice_doc.price_list_currency,
		"plc_conversion_rate": original_invoice_doc.plc_conversion_rate,
		"debit_to": original_invoice_doc.debit_to,
		"cost_center": original_invoice_doc.cost_center,
		"project": original_invoice_doc.project,
		"student": getattr(original_invoice_doc, 'student', None),
		"fee_schedule": getattr(original_invoice_doc, 'fee_schedule', None),
		"custom_has_late_fine": 1,
		"custom_late_fine_amount": late_fine_amount,
		"custom_fine_frequency": original_invoice_doc.get('custom_fine_frequency', 'Once'),
		"custom_late_fine_from": original_invoice_doc.due_date or today(),
	})
	
	# Add the late fine item
	item_row = late_fine_invoice.append("items", {
		"item_code": item_code,
		"item_name": item_name if not item_code else None,
		"description": late_fine_component.description if late_fine_component else "Late Fine",
		"qty": 1,
		"rate": late_fine_amount,
		"amount": late_fine_amount,
		"income_account": income_account
	})
	
	# Set discount if available from component
	if late_fine_component and late_fine_component.discount:
		item_row.discount_percentage = late_fine_component.discount
		# Recalculate amount with discount
		item_row.amount = late_fine_amount - (late_fine_amount * late_fine_component.discount / 100)
	
	# Calculate totals
	late_fine_invoice.calculate_taxes_and_totals()
	
	# Save the invoice
	late_fine_invoice.save()
	
	frappe.db.commit()
	
	frappe.log_error(
		title="Late Fine Invoice Created",
		message=f"Created late fine invoice {late_fine_invoice.name} for overdue invoice {original_invoice_doc.name}"
	)
