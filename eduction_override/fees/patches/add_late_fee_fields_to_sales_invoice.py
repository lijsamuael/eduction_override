# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Enable allow_on_submit for items table and calculated fields in Sales Invoice.
	
	This patch ensures property setters are always in place, even if they were deleted.
	It can be run multiple times safely (idempotent).
	"""
	doctype = "Sales Invoice"
	
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter
	
	created_count = 0
	updated_count = 0
	
	# Enable allow_on_submit for items child table
	# Always ensure it exists (delete and recreate if needed to ensure it's correct)
	items_property = frappe.db.get_value(
		"Property Setter",
		{"doc_type": doctype, "field_name": "items", "property": "allow_on_submit"},
		["name", "value"]
	)
	
	if items_property:
		# Check if value is correct
		if items_property[1] != "1":
			# Update existing property setter
			frappe.db.set_value("Property Setter", items_property[0], "value", "1")
			updated_count += 1
	else:
		# Create new property setter
		try:
			make_property_setter(
				doctype=doctype,
				fieldname="items",
				property="allow_on_submit",
				value="1",
				property_type="Check",
				validate_fields_for_doctype=False
			)
			created_count += 1
		except Exception as e:
			frappe.log_error(f"Error creating property setter for items: {str(e)}")
	
	# Enable allow_on_submit for calculated fields that change when items are added
	calculated_fields = [
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
	
	for fieldname in calculated_fields:
		# Check if field exists in DocField
		if frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			# Check if property setter already exists
			existing_property = frappe.db.get_value(
				"Property Setter",
				{"doc_type": doctype, "field_name": fieldname, "property": "allow_on_submit"},
				["name", "value"]
			)
			
			if existing_property:
				# Check if value is correct
				if existing_property[1] != "1":
					# Update existing property setter
					frappe.db.set_value("Property Setter", existing_property[0], "value", "1")
					updated_count += 1
			else:
				# Create new property setter
				try:
					make_property_setter(
						doctype=doctype,
						fieldname=fieldname,
						property="allow_on_submit",
						value="1",
						property_type="Check",
						validate_fields_for_doctype=False
					)
					created_count += 1
				except Exception as e:
					frappe.log_error(f"Error creating property setter for {fieldname}: {str(e)}")
	
	frappe.db.commit()
	
	# Clear cache to ensure property setters are loaded
	frappe.clear_cache(doctype=doctype)
	
	# Log summary
	frappe.log_error(
		title="Property Setters Ensured",
		message=f"Created {created_count} new property setters, updated {updated_count} existing ones for {doctype} with allow_on_submit=1"
	)

