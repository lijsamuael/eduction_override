# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import today, getdate


def daily():
	"""Daily scheduler to add late fine items to sales invoices when late fine date is reached."""
	add_late_fine_to_invoices()
	add_late_fine_to_overdue_invoices()


def add_late_fine_to_invoices():
	"""Add late fine items to sales invoices where current date >= late fine date."""
	current_date = today()
	
	# Find all fee schedules with late fine enabled and date <= today
	fee_schedules = frappe.get_all(
		"Fee Schedule",
		filters={
			"custom_allow_late_fine": 1,
			"custom_late_fine_from": ["<=", current_date],
			"docstatus": 1  # Only submitted fee schedules
		},
		fields=["name", "custom_late_fine_amount", "custom_fine_frequency", "custom_description", "custom_late_fine_from"]
	)
	
	if not fee_schedules:
		return
	
	for fee_schedule_data in fee_schedules:
		fee_schedule_name = fee_schedule_data.name
		late_fine_amount = fee_schedule_data.custom_late_fine_amount or 0
		
		if late_fine_amount <= 0:
			continue
		
		# Check if date is reached (current date >= late fine from date)
		late_fine_from = fee_schedule_data.custom_late_fine_from
		if not late_fine_from or getdate(current_date) < getdate(late_fine_from):
			continue
		
		# Find all sales invoices for this fee schedule that don't have late fine yet
		sales_invoices = frappe.get_all(
			"Sales Invoice",
			filters={
				"fee_schedule": fee_schedule_name,
				"docstatus": ["<", 2]  # Draft or Submitted (not cancelled)
			},
			fields=["name"]
		)
		
		for invoice in sales_invoices:
			try:
				add_late_fine_item_to_invoice(
					invoice.name,
					fee_schedule_name,
					late_fine_amount,
					fee_schedule_data.custom_description
				)
			except Exception as e:
				frappe.log_error(
					title=f"Error adding late fine to invoice {invoice.name}",
					message=str(e)
				)


def add_late_fine_item_to_invoice(invoice_name, fee_schedule_name, late_fine_amount, description=None):
	"""Add late fine item to a sales invoice if not already added."""
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
	
	# Check if invoice is submitted - if so, we need to cancel and recreate or use amendment
	if invoice_doc.docstatus == 1:
		# Invoice is submitted, we can't modify it directly
		# For now, log an error - user will need to manually add or cancel and recreate
		frappe.log_error(
			title=f"Cannot add late fine to submitted invoice {invoice_name}",
			message=f"Late fine cannot be automatically added to submitted invoice. Please cancel and recreate or add manually."
		)
		return
	
	# Check if late fine item already exists
	for item in invoice_doc.items:
		# Check by item_code, item_name, or description containing "Late Fine"
		if (item.item_code and "Late Fine" in (item.item_code or "")) or \
		   (item.item_name and "Late Fine" in (item.item_name or "")) or \
		   (item.description and "Late Fine" in (item.description or "")):
			# Late fine already added, skip
			return
	
	# Get fee schedule to find the late fine item
	fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule_name)
	
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
	
	# Calculate totals
	invoice_doc.calculate_taxes_and_totals()
	
	# Save the invoice
	invoice_doc.save()
	
	frappe.db.commit()


@frappe.whitelist()
def add_late_fine_to_overdue_invoices():
	"""Add late fine items to overdue sales invoices that have late fine amount configured.
	This function is called by the scheduled job daily."""
	# Find all sales invoices with status "Overdue" that have late fine amount configured
	overdue_invoices = frappe.get_all(
		"Sales Invoice",
		filters={
			"status": ["like", "Overdue%"],  # Matches "Overdue" or "Overdue and Discounted"
			"custom_has_late_fine": 1,
			"custom_late_fine_amount": [">", 0],
			"docstatus": ["<", 2]  # Draft or Submitted (not cancelled)
		},
		fields=["name", "custom_late_fine_amount", "custom_late_fine_description", "fee_schedule"]
	)
	
	if not overdue_invoices:
		return
	
	for invoice_data in overdue_invoices:
		invoice_name = invoice_data.name
		late_fine_amount = invoice_data.custom_late_fine_amount or 0
		description = invoice_data.custom_late_fine_description
		fee_schedule_name = invoice_data.fee_schedule
		
		if late_fine_amount <= 0:
			continue
		
		try:
			add_late_fine_item_to_overdue_invoice(
				invoice_name,
				late_fine_amount,
				description,
				fee_schedule_name
			)
		except Exception as e:
			frappe.log_error(
				title=f"Error adding late fine to overdue invoice {invoice_name}",
				message=str(e)
			)


def add_late_fine_item_to_overdue_invoice(invoice_name, late_fine_amount, description=None, fee_schedule_name=None):
	"""Add late fine item to an overdue sales invoice if not already added."""
	invoice_doc = frappe.get_doc("Sales Invoice", invoice_name)
	
	# Check if late fine item already exists
	for item in invoice_doc.items:
		# Check by item_code, item_name, or description containing "Late Fine"
		if (item.item_code and "Late Fine" in (item.item_code or "")) or \
		   (item.item_name and "Late Fine" in (item.item_name or "")) or \
		   (item.description and "Late Fine" in (item.description or "")):
			# Late fine already added, skip
			return
	
	# If invoice is submitted, we need to handle it differently
	if invoice_doc.docstatus == 1:
		# For submitted invoices, create a new invoice for the late fine
		_create_late_fine_invoice_for_submitted(invoice_doc, late_fine_amount, description, fee_schedule_name)
		return
	
	# For draft invoices, add the item directly
	# Get fee schedule to find the late fine item if available
	late_fine_component = None
	if fee_schedule_name:
		try:
			fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule_name)
			# Find Late Fine component in fee schedule
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
	
	# Calculate totals
	invoice_doc.calculate_taxes_and_totals()
	
	# Save the invoice
	invoice_doc.save()
	
	frappe.db.commit()


def _create_late_fine_invoice_for_submitted(original_invoice_doc, late_fine_amount, description=None, fee_schedule_name=None):
	"""Create a new invoice for late fine when the original invoice is submitted."""
	# Check if a late fine invoice already exists for this invoice
	existing_late_fine_invoice = frappe.db.exists(
		"Sales Invoice",
		{
			"custom_original_invoice_for_late_fine": original_invoice_doc.name,
			"docstatus": ["<", 2]  # Draft or Submitted
		}
	)
	
	if existing_late_fine_invoice:
		# Late fine invoice already exists, skip
		return
	
	# Get fee schedule to find the late fine item if available
	late_fine_component = None
	if fee_schedule_name:
		try:
			fee_schedule_doc = frappe.get_doc("Fee Schedule", fee_schedule_name)
			# Find Late Fine component in fee schedule
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
		"student": original_invoice_doc.student if hasattr(original_invoice_doc, 'student') else None,
		"fee_schedule": original_invoice_doc.fee_schedule if hasattr(original_invoice_doc, 'fee_schedule') else None,
		"custom_original_invoice_for_late_fine": original_invoice_doc.name,
		"custom_allow_late_fine": 1,
		"custom_late_fine_amount": late_fine_amount,
		"custom_late_fine_description": description or "Late Fine for overdue invoice",
	})
	
	# Add the late fine item
	item_row = late_fine_invoice.append("items", {
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
	
	# Calculate totals
	late_fine_invoice.calculate_taxes_and_totals()
	
	# Save the invoice
	late_fine_invoice.save()
	
	frappe.db.commit()
	
	frappe.log_error(
		title=f"Created late fine invoice for overdue invoice {original_invoice_doc.name}",
		message=f"Late fine invoice {late_fine_invoice.name} created for overdue invoice {original_invoice_doc.name}"
	)

