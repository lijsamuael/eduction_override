# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Remove allow_on_submit property setters for Sales Invoice and Sales Invoice Item.
	
	This patch removes all property setters that were created to make submitted
	sales invoices editable. This reverts the changes made by add_late_fee_fields_to_sales_invoice.
	"""
	doctype = "Sales Invoice"
	child_doctype = "Sales Invoice Item"
	
	# List of all fields that had allow_on_submit enabled
	parent_fields = [
		"items",
		"total",
		"grand_total",
		"rounded_total",
		"total_qty",
		"base_grand_total",
		"base_rounded_total",
		"base_total",
		"net_total",
		"base_net_total",
		"total_taxes_and_charges",
		"base_total_taxes_and_charges",
		"in_words",
		"base_in_words",
		"rounding_adjustment",
		"base_rounding_adjustment",
		"outstanding_amount",
		"base_outstanding_amount",
		"discount_amount",
		"base_discount_amount",
		"amount_eligible_for_commission",
	]
	
	child_fields = [
		"net_rate",
		"base_net_rate",
		"net_amount",
		"base_net_amount",
		"amount",
		"base_amount",
		"rate",
		"base_rate",
		"stock_qty",
		"stock_uom_rate",
	]
	
	deleted_count = 0
	
	# Delete property setters for parent doctype
	for fieldname in parent_fields:
		property_setters = frappe.get_all(
			"Property Setter",
			filters={
				"doc_type": doctype,
				"field_name": fieldname,
				"property": "allow_on_submit"
			},
			fields=["name"]
		)
		
		for ps in property_setters:
			try:
				frappe.delete_doc("Property Setter", ps.name, force=1)
				deleted_count += 1
			except Exception as e:
				frappe.log_error(f"Error deleting property setter {ps.name}: {str(e)}")
	
	# Delete property setters for child doctype
	for fieldname in child_fields:
		property_setters = frappe.get_all(
			"Property Setter",
			filters={
				"doc_type": child_doctype,
				"field_name": fieldname,
				"property": "allow_on_submit"
			},
			fields=["name"]
		)
		
		for ps in property_setters:
			try:
				frappe.delete_doc("Property Setter", ps.name, force=1)
				deleted_count += 1
			except Exception as e:
				frappe.log_error(f"Error deleting property setter {ps.name}: {str(e)}")
	
	frappe.db.commit()
	
	# Clear cache
	frappe.clear_cache(doctype=doctype)
	frappe.clear_cache(doctype=child_doctype)
	
	# Log summary
	frappe.log_error(
		title="Property Setters Removed",
		message=f"Deleted {deleted_count} property setters for {doctype} and {child_doctype} with allow_on_submit=1"
	)

