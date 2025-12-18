# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice


class CustomSalesInvoice(SalesInvoice):
	def on_update_after_submit(self):
		"""Override to handle cases where items are added to submitted invoices.
		
		The base implementation fails with IndexError when new items are added
		because it tries to compare items by index, but the new items list
		has more items than the old items list.
		"""
		fields_to_check = [
			"cash_bank_account",
			"write_off_account",
			"unrealized_profit_loss_account",
			"is_opening",
		]
		child_tables = {
			"items": ("income_account", "expense_account", "discount_account"),
			"taxes": ("account_head",),
		}
		
		# Try the normal check first
		try:
			self.needs_repost = self.check_if_fields_updated(fields_to_check, child_tables)
		except (IndexError, AttributeError, KeyError) as e:
			# If there's an IndexError, it's likely because items were added
			# In this case, we need to repost to account for the new items
			frappe.log_error(
				title="Sales Invoice: Error checking fields update",
				message=f"Error in check_if_fields_updated: {str(e)}\n"
						f"This usually happens when items are added to a submitted invoice.\n"
						f"Invoice: {self.name}"
			)
			# Assume repost is needed when items are added
			self.needs_repost = True
		
		if self.needs_repost:
			self.validate_for_repost()
			self.repost_accounting_entries()

