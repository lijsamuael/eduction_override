import frappe
from frappe.custom.doctype.custom_field.custom_field import create_custom_field


def execute():
	# Ensure the ERPNext "Is Billing Contact" field exists on Contact.
	if not frappe.db.exists("Custom Field", "Contact-is_billing_contact"):
		create_custom_field(
			"Contact",
			{
				"fieldname": "is_billing_contact",
				"label": "Is Billing Contact",
				"fieldtype": "Check",
				"insert_after": "is_primary_contact",
			},
			ignore_validate=True,
		)

	if not frappe.db.has_column("Contact", "is_billing_contact"):
		# Custom Field might exist without the physical column; ensure column is present.
		frappe.db.add_column("Contact", "is_billing_contact", "int(1) not null default 0")

