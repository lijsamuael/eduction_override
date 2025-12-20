// Copyright (c) 2024, Eduction Override and contributors
// For license information, please see license.txt

frappe.listview_settings["Sales Invoice"] = {
	add_fields: [
		"customer",
		"customer_name",
		"posting_date",
		"due_date",
		"total",
		"base_total",
		"grand_total",
		"base_grand_total",
		"rounded_total",
		"base_rounded_total",
		"discount_amount",
		"base_discount_amount",
		"paid_amount",
		"base_paid_amount",
		"outstanding_amount",
		"base_outstanding_amount",
		"status",
		"custom_payment_status",
		"company",
		"currency",
		"is_return",
		"custom_late_fine_amount",
		"custom_has_late_fine",
	],
	
	get_indicator: function (doc) {
		const status_colors = {
			Draft: "red",
			Unpaid: "orange",
			Paid: "green",
			Return: "gray",
			"Credit Note Issued": "gray",
			"Unpaid and Discounted": "orange",
			"Partly Paid and Discounted": "yellow",
			"Overdue and Discounted": "red",
			Overdue: "red",
			"Partly Paid": "yellow",
			"Internal Transfer": "darkgrey",
		};
		return [__(doc.status), status_colors[doc.status], "status,=," + doc.status];
	},
	
	// Custom column formatters
	formatters: {
		// Format Date column to show both posting_date and due_date
		posting_date: function(value, doc) {
			if (!value) return "";
			const posting_date = frappe.datetime.str_to_user(value);
			const due_date = doc.due_date ? frappe.datetime.str_to_user(doc.due_date) : "";
			if (due_date) {
				return `<div>Date: ${posting_date}</div><div>Due: ${due_date}</div>`;
			}
			return `<div>Date: ${posting_date}</div>`;
		},
		
		// Format Status to include paid date
		status: function(value, doc) {
			if (!value) return "";
			const status_colors = {
				Draft: "red",
				Unpaid: "orange",
				Paid: "green",
				Return: "gray",
				"Credit Note Issued": "gray",
				"Unpaid and Discounted": "orange",
				"Partly Paid and Discounted": "yellow",
				"Overdue and Discounted": "red",
				Overdue: "red",
				"Partly Paid": "yellow",
				"Internal Transfer": "darkgrey",
			};
			const color = status_colors[value] || "gray";
			let html = `<span class="indicator ${color}">${__(value)}</span>`;
			
			// For paid invoices, fetch and show paid date
			if (value === "Paid" && doc.paid_amount > 0) {
				// Store doc name for async update
				html += `<div class="paid-date-${doc.name}" style="font-size: 11px; color: #666; margin-top: 2px;"></div>`;
				
				// Fetch paid date asynchronously
				setTimeout(function() {
					frappe.call({
						method: "frappe.client.get_list",
						args: {
							doctype: "Payment Entry Reference",
							filters: {
								reference_doctype: "Sales Invoice",
								reference_name: doc.name
							},
							fields: ["parent"],
							limit: 1,
							order_by: "creation desc"
						},
						callback: function(r) {
							if (r.message && r.message.length > 0) {
								frappe.db.get_value("Payment Entry", r.message[0].parent, "posting_date", function(payment) {
									if (payment && payment.posting_date) {
										const paid_date = frappe.datetime.str_to_user(payment.posting_date);
										const paid_date_elem = $(`.paid-date-${doc.name}`);
										if (paid_date_elem.length) {
											paid_date_elem.text(`Paid on: ${paid_date}`);
										}
									}
								});
							}
						}
					});
				}, 100);
			}
			
			return html;
		},
		
		// Format Due Date
		due_date: function(value, doc) {
			if (!value) return "";
			return frappe.datetime.str_to_user(value);
		},
		
		// Format Payment Status with colors
		custom_payment_status: function(value, doc) {
			if (!value) return "";
			
			const status_colors = {
				"Unpaid": "orange",
				"Overdue": "red",
				"Partially Paid": "yellow",
				"Paid": "green"
			};
			
			const color = status_colors[value] || "gray";
			return `<span class="indicator ${color}">${__(value)}</span>`;
		},
		
		// Format Gross amount (total)
		total: function(value, doc) {
			if (!value) return "0.00";
			return format_currency(value, doc.currency);
		},
		
		// Format Net amount (grand_total)
		grand_total: function(value, doc) {
			if (!value) return "0.00";
			return format_currency(value, doc.currency);
		},
		
		// Format Fine amount
		custom_late_fine_amount: function(value, doc) {
			if (!value || value === 0) return "0.00";
			return format_currency(value, doc.currency);
		},
		
		// Format Discount
		discount_amount: function(value, doc) {
			if (!value || value === 0) return "0.00";
			return format_currency(value, doc.currency);
		},
		
		// Format Paid amount
		paid_amount: function(value, doc) {
			if (!value) return "0.00";
			return format_currency(value, doc.currency);
		},
		
		// Format Balance (outstanding_amount)
		outstanding_amount: function(value, doc) {
			if (!value) return "0.00";
			return format_currency(value, doc.currency);
		}
	},
	
	onload: function (listview) {
		// Set default columns by modifying list view settings
		// This will be applied when user customizes columns or we can set it programmatically
		
		// Wait for list view to be ready, then set default columns
		setTimeout(function() {
			// Get or create list view settings
			frappe.call({
				method: "frappe.desk.doctype.list_view_settings.list_view_settings.get_list_view_settings",
				args: {
					doctype: "Sales Invoice"
				},
				callback: function(r) {
					if (r.message) {
						const settings = r.message;
						// Set default fields if not already set
						if (!settings.fields || settings.fields === "[]") {
							const default_fields = [
								{fieldname: "name", label: "Invoice"},
								{fieldname: "posting_date", label: "Date"},
								{fieldname: "status", label: "Status"},
								{fieldname: "grand_total", label: "Gross amount"},
								{fieldname: "custom_late_fine_amount", label: "Fine amount"},
								{fieldname: "discount_amount", label: "Discount"},
								{fieldname: "paid_amount", label: "Paid amount"},
								{fieldname: "outstanding_amount", label: "Balance"}
							];
							
							frappe.call({
								method: "frappe.desk.doctype.list_view_settings.list_view_settings.save_list_view_settings",
								args: {
									doctype: "Sales Invoice",
									fields: JSON.stringify(default_fields)
								},
								callback: function() {
									// Refresh list view to apply new columns
									listview.refresh();
								}
							});
						}
					}
				}
			});
		}, 500);
		
		if (frappe.model.can_create("Delivery Note")) {
			listview.page.add_action_item(__("Delivery Note"), () => {
				erpnext.bulk_transaction_processing.create(listview, "Sales Invoice", "Delivery Note");
			});
		}

		if (frappe.model.can_create("Payment Entry")) {
			listview.page.add_action_item(__("Payment"), () => {
				erpnext.bulk_transaction_processing.create(listview, "Sales Invoice", "Payment Entry");
			});
		}
	},
	
	right_column: "grand_total"
};

// Helper function to format currency
function format_currency(value, currency) {
	if (!value) value = 0;
	return format_number(value, {
		precision: 2
	});
}
