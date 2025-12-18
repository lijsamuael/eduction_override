# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

# Monkey patch the create_sales_invoice function when this module is imported
def patch_create_sales_invoice():
	"""Patch the create_sales_invoice function in fee_schedule module."""
	from eduction_override.fees import fee_schedule_override
	import education.education.doctype.fee_schedule.fee_schedule as fee_schedule_module
	
	# Replace the original function with our override
	fee_schedule_module.create_sales_invoice = fee_schedule_override.create_sales_invoice

# Apply the patch
patch_create_sales_invoice()

