# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe


def execute():
	"""Set in_list_view=1 for Sales Invoice fields to show custom columns in list view."""
	doctype = "Sales Invoice"
	
	from frappe.custom.doctype.property_setter.property_setter import make_property_setter
	
	# Fields to show in list view (in order)
	fields_to_show = [
		"name",                    # Invoice
		"posting_date",           # Date
		"due_date",               # Due Date
		"status",                 # Status
		"custom_payment_status",  # Payment Status
		"total",                  # Gross amount (total before taxes)
		"custom_late_fine_amount", # Fine amount
		"discount_amount",        # Discount
		"grand_total",            # Net amount (grand_total after taxes)
		"paid_amount",            # Paid amount
		"outstanding_amount",    # Balance
	]
	
	created_count = 0
	updated_count = 0
	
	for fieldname in fields_to_show:
		# Check if field exists
		if not frappe.db.exists("DocField", {"parent": doctype, "fieldname": fieldname}):
			continue
		
		# Check if property setter already exists
		existing_property = frappe.db.get_value(
			"Property Setter",
			{"doc_type": doctype, "field_name": fieldname, "property": "in_list_view"},
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
					property="in_list_view",
					value="1",
					property_type="Check",
					validate_fields_for_doctype=False
				)
				created_count += 1
			except Exception as e:
				frappe.log_error(f"Error creating property setter for {fieldname}: {str(e)}")
	
	# Also set default list view settings with field order
	try:
		# Get or create List View Settings
		list_view_settings = frappe.db.get_value("List View Settings", doctype, "name")
		
		if list_view_settings:
			# Update existing settings
			settings_doc = frappe.get_doc("List View Settings", list_view_settings)
		else:
			# Create new settings
			settings_doc = frappe.new_doc("List View Settings")
			settings_doc.name = doctype
		
		# Set fields in order with custom labels
		fields_json = []
		custom_labels = {
			"total": "Gross amount",
			"grand_total": "Net amount",
			"name": "Invoice",
			"posting_date": "Date",
			"due_date": "Due Date",
			"status": "Status",
			"custom_payment_status": "Payment Status",
			"custom_late_fine_amount": "Fine amount",
			"discount_amount": "Discount",
			"paid_amount": "Paid amount",
			"outstanding_amount": "Balance"
		}
		
		for fieldname in fields_to_show:
			meta_field = frappe.get_meta(doctype).get_field(fieldname)
			if meta_field:
				label = custom_labels.get(fieldname, meta_field.label or fieldname)
				fields_json.append({
					"fieldname": fieldname,
					"label": label
				})
		
		settings_doc.fields = frappe.as_json(fields_json)
		settings_doc.save(ignore_permissions=True)
		
		frappe.db.commit()
		
	except Exception as e:
		frappe.log_error(f"Error setting list view settings: {str(e)}")
	
	frappe.db.commit()
	
	# Clear cache
	frappe.clear_cache(doctype=doctype)
	
	# Log summary
	frappe.log_error(
		title="List View Fields Set",
		message=f"Created {created_count} new property setters, updated {updated_count} existing ones for {doctype} with in_list_view=1"
	)

