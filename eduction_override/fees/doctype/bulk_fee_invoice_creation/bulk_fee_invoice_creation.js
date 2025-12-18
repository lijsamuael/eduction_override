// Copyright (c) 2024, Eduction Override and contributors
// For license information, please see license.txt

console.log('[Bulk Fee Invoice Creation] JavaScript file loaded');

frappe.ui.form.on('Bulk Fee Invoice Creation', {
	onload: function(frm) {
		console.log('[Bulk Fee Invoice Creation] Form onload triggered');
		setTimeout(function() {
			render_rows_table(frm);
		}, 500);
	},
	
	refresh: function(frm) {
		console.log('[Refresh] refresh function called');
		console.log('[Refresh] Form document name:', frm.doc.name);
		console.log('[Refresh] Fee structure:', frm.doc.fee_structure);
		
		if (frm.doc.status === 'Completed' || frm.doc.status === 'Failed') {
			frm.disable_save();
		} else {
			frm.enable_save();
		}
		
		// Hide table and button if document is not saved
		if (!frm.doc.name) {
			frm.set_df_property('class_sections_html', 'hidden', 1);
			$('.custom-btn-create-fee-schedules').remove();
		} else {
			frm.set_df_property('class_sections_html', 'hidden', 0);
		}
		
		// Add Create Fee Schedule button at the top, left to Actions menu
		// Show button even if status is Failed (to allow retry)
		// Remove any existing button first
		$('.custom-btn-create-fee-schedules').remove();
		
		if (frm.doc.name && frm.doc.status !== 'Completed') {
			// Add button to page header, left to Actions
			const btn = frm.page.add_button(__('Create Fee Schedules'), function() {
				frm.trigger('create_fee_schedules');
			}, {
				btn_class: 'btn-primary',
				btn_size: 'btn-sm'
			});
			
			// Add class for easy removal
			$(btn).addClass('custom-btn-create-fee-schedules');
			
			// Style the button with black background
			$(btn).css({
				'background-color': '#000000',
				'color': '#ffffff',
				'border-color': '#000000',
				'margin-right': '10px'
			}).hover(
				function() { $(this).css('background-color', '#333333'); },
				function() { $(this).css('background-color', '#000000'); }
			);
			
			// Add icon
			$(btn).prepend('<i class="fa fa-plus"></i> ');
		}
		
		// If fee structure is selected, fetch and populate components
		if (frm.doc.fee_structure) {
			console.log('[Refresh] Fee structure found:', frm.doc.fee_structure);
			console.log('[Refresh] Current fee_components count:', frm.doc.fee_components ? frm.doc.fee_components.length : 0);
			
			// If components are already loaded, use them
			if (frm.doc.fee_components && frm.doc.fee_components.length > 0) {
				console.log('[Refresh] Fee components already exist, using them');
				
				var fee_categories = [];
				var category_map = {};
				
				$.each(frm.doc.fee_components, function(i, component) {
					if (component.fees_category && !category_map[component.fees_category]) {
						category_map[component.fees_category] = true;
						fee_categories.push({
							name: component.fees_category,
							description: component.description || ''
						});
					}
				});
				
			} else {
				// Components not loaded, fetch from fee structure
				console.log('[Refresh] Fee components not loaded, fetching from Fee Structure:', frm.doc.fee_structure);
				console.log('[Refresh] Calling fetch_and_populate_fee_components function');
				fetch_and_populate_fee_components(frm, frm.doc.fee_structure);
			}
		}
		
		setTimeout(function() {
			render_rows_table(frm);
		}, 300);
	},

	fee_structure: function(frm) {
		console.log('========================================');
		console.log('[Fee Structure] fee_structure field changed - FUNCTION CALLED');
		console.log('[Fee Structure] Selected fee structure:', frm.doc.fee_structure);
		console.log('[Fee Structure] Form document:', frm.doc);
		
		// Clear existing components
		try {
			frm.clear_table('fee_components');
			console.log('[Fee Structure] Cleared fee_components table');
		} catch(e) {
			console.error('[Fee Structure] Error clearing tables:', e);
		}
		
		if (frm.doc.fee_structure) {
			console.log('[Fee Structure] Fetching Fee Structure document:', frm.doc.fee_structure);
			
			// Load company if not set
			if (!frm.doc.company) {
				frappe.call({
					method: 'frappe.client.get',
					args: {
						doctype: 'Fee Structure',
						name: frm.doc.fee_structure
					},
					callback: function(r) {
						console.log('[Fee Structure] Company fetch response:', r);
						if (r.message && r.message.company) {
							frm.set_value('company', r.message.company);
							console.log('[Fee Structure] Set company to:', r.message.company);
						}
					}
				});
			}
			
			// Load fee components from Fee Structure into child table
			// Use the same approach as Fee Schedule - get full Fee Structure document
			console.log('[Fee Structure] Making API call to fetch Fee Structure...');
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Fee Structure',
					name: frm.doc.fee_structure
				},
				callback: function(r) {
					console.log('[Fee Structure] ===== API CALLBACK RECEIVED =====');
					console.log('[Fee Structure] Full response object:', r);
					console.log('[Fee Structure] Response message:', r.message);
					console.log('[Fee Structure] Components found:', r.message && r.message.components ? r.message.components.length : 0);
					
					if (!r.message) {
						console.error('[Fee Structure] ERROR: No message in response');
						return;
					}
					
					if (r.message && r.message.components && r.message.components.length > 0) {
						console.log('[Fee Structure] Components data:', JSON.stringify(r.message.components, null, 2));
						
						// Clear existing components first
						frm.clear_table('fee_components');
						console.log('[Fee Structure] Cleared fee_components table');
						
						// Collect unique fee categories
						var fee_categories = [];
						var category_map = {};
						
						// Add each component from Fee Structure to fee_components table
						$.each(r.message.components, function(i, d) {
							console.log('[Fee Structure] Processing component', i + 1, ':', d);
							
							var row = frappe.model.add_child(
								frm.doc,
								'Fee Component',
								'fee_components'
							);
							// Set all fields from Fee Structure component
							row.fees_category = d.fees_category;
							row.description = d.description;
							row.amount = d.amount;
							row.item = d.item || '';
							row.discount = d.discount || 0;
							// Calculate total: amount - (amount * discount / 100)
							if (d.discount && d.discount > 0) {
								row.total = d.amount - (d.amount * d.discount / 100);
							} else {
								row.total = d.amount;
							}
							console.log('[Fee Structure] Added to fee_components:', {
								fees_category: row.fees_category,
								description: row.description,
								amount: row.amount,
								total: row.total
							});
							
							// Collect fee categories
							if (d.fees_category && !category_map[d.fees_category]) {
								category_map[d.fees_category] = true;
								fee_categories.push({
									name: d.fees_category,
									description: d.description || ''
								});
							}
						});
						frm.refresh_field('fee_components');
						console.log('[Fee Structure] Refreshed fee_components field');
						console.log('========================================');
					} else {
						console.log('[Fee Structure] No components found in fee structure');
					}
				},
				error: function(r) {
					console.error('[Fee Structure] ===== API ERROR =====');
					console.error('[Fee Structure] Error response:', r);
					console.error('[Fee Structure] Error details:', JSON.stringify(r, null, 2));
				}
			}).fail(function(r) {
				console.error('[Fee Structure] ===== API CALL FAILED =====');
				console.error('[Fee Structure] Fail response:', r);
			});
		} else {
			console.log('[Fee Structure] No fee structure selected');
		}
	},

	create_fee_schedules: function(frm) {
		if (!frm.doc.fee_structure) {
			frappe.msgprint(__('Please select Fee Structure'));
			return;
		}

		if (!frm.doc.name) {
			frappe.msgprint(__('Please save the document first.'));
			return;
		}

		frappe.confirm(
			__('This will create fee schedules for all selected sections. Do you want to continue?'),
			function() {
				frm.call('create_fee_schedules', {}, function(r) {
					if (r.message) {
						frappe.msgprint({
							title: __('Success'),
							message: __('Created {0} fee schedule(s)', [r.message.created]),
							indicator: 'green'
						});
						frm.reload_doc();
					}
				});
			}
		);
	}
});

// Function to fetch and populate fee components from fee structure
function fetch_and_populate_fee_components(frm, fee_structure_name) {
	console.log('[fetch_and_populate_fee_components] ===== FUNCTION CALLED =====');
	console.log('[fetch_and_populate_fee_components] Fee Structure:', fee_structure_name);
	
	if (!fee_structure_name) {
		console.error('[fetch_and_populate_fee_components] No fee structure provided');
		return;
	}
	
	// Load company if not set
	if (!frm.doc.company) {
		frappe.call({
			method: 'frappe.client.get',
			args: {
				doctype: 'Fee Structure',
				name: fee_structure_name
			},
			callback: function(r) {
				console.log('[fetch_and_populate_fee_components] Company fetch response:', r);
				if (r.message && r.message.company) {
					frm.set_value('company', r.message.company);
					console.log('[fetch_and_populate_fee_components] Set company to:', r.message.company);
				}
			}
		});
	}
	
	// Fetch fee structure with components
	console.log('[fetch_and_populate_fee_components] Making API call to fetch Fee Structure...');
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Fee Structure',
			name: fee_structure_name
		},
		callback: function(r) {
			console.log('[fetch_and_populate_fee_components] ===== API CALLBACK RECEIVED =====');
			console.log('[fetch_and_populate_fee_components] Full response:', r);
			console.log('[fetch_and_populate_fee_components] Response message:', r.message);
			console.log('[fetch_and_populate_fee_components] Components found:', r.message && r.message.components ? r.message.components.length : 0);
			
			if (!r.message) {
				console.error('[fetch_and_populate_fee_components] ERROR: No message in response');
				return;
			}
			
			if (r.message && r.message.components && r.message.components.length > 0) {
				console.log('[fetch_and_populate_fee_components] Components data:', JSON.stringify(r.message.components, null, 2));
				
				// Clear existing components first
				frm.clear_table('fee_components');
				console.log('[fetch_and_populate_fee_components] Cleared fee_components table');
				
				// Collect unique fee categories
				var fee_categories = [];
				var category_map = {};
				
				// Add each component from Fee Structure to fee_components table
				$.each(r.message.components, function(i, d) {
					console.log('[fetch_and_populate_fee_components] Processing component', i + 1, ':', d);
					
					var row = frappe.model.add_child(
						frm.doc,
						'Fee Component',
						'fee_components'
					);
					// Set all fields from Fee Structure component
					row.fees_category = d.fees_category;
					row.description = d.description;
					row.amount = d.amount;
					row.item = d.item || '';
					row.discount = d.discount || 0;
					// Calculate total: amount - (amount * discount / 100)
					if (d.discount && d.discount > 0) {
						row.total = d.amount - (d.amount * d.discount / 100);
					} else {
						row.total = d.amount;
					}
					console.log('[fetch_and_populate_fee_components] Added to fee_components:', {
						fees_category: row.fees_category,
						description: row.description,
						amount: row.amount,
						total: row.total
					});
					
					// Collect fee categories
					if (d.fees_category && !category_map[d.fees_category]) {
						category_map[d.fees_category] = true;
						fee_categories.push({
							name: d.fees_category,
							description: d.description || ''
						});
					}
				});
				frm.refresh_field('fee_components');
				console.log('[fetch_and_populate_fee_components] Refreshed fee_components field');
				console.log('[fetch_and_populate_fee_components] ===== FUNCTION COMPLETED =====');
			} else {
				console.log('[fetch_and_populate_fee_components] No components found in fee structure');
			}
		},
		error: function(r) {
			console.error('[fetch_and_populate_fee_components] ===== API ERROR =====');
			console.error('[fetch_and_populate_fee_components] Error response:', r);
			console.error('[fetch_and_populate_fee_components] Error details:', JSON.stringify(r, null, 2));
		}
	}).fail(function(r) {
		console.error('[fetch_and_populate_fee_components] ===== API CALL FAILED =====');
		console.error('[fetch_and_populate_fee_components] Fail response:', r);
	});
}

// Handle Fee Component changes (same as Fee Schedule)
frappe.ui.form.on('Fee Component', {
	amount: function(frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		d.total = d.amount;
		frm.refresh_field('fee_components');
		if (d.discount) {
			d.total = d.amount - d.amount * (d.discount / 100);
			frm.refresh_field('fee_components');
		}
	},
	discount: function(frm, cdt, cdn) {
		let d = locals[cdt][cdn];
		if (d.discount <= 100) {
			d.total = d.amount - d.amount * (d.discount / 100);
		}
		frm.refresh_field('fee_components');
	}
});

function open_add_row_dialog(frm, row_name = null) {
	if (!frm.doc.name) {
		frappe.msgprint(__('Please save the document first.'));
		return;
	}
	
	// Determine if editing or creating
	const is_edit = row_name !== null;
	
	// Start with one default empty row or load existing data
	let sections_data = [{}];
	let total_students = 0;
	let existing_program = "";

	const d = new frappe.ui.Dialog({
		title: is_edit ? __("Edit Bulk Fee Invoice Creation Row") : __("Add Bulk Fee Invoice Creation Row"),
		fields: [
			{
				fieldname: "program",
				fieldtype: "Link",
				options: "Program",
				label: __("Program"),
				reqd: 1,
				default: existing_program,
			},
			{
				fieldname: "sections_html",
				fieldtype: "HTML",
				options: "",
			},
		],
		primary_action_label: is_edit ? __("Update") : __("Create"),
		primary_action: async (values) => {
			if (!values) return;
			try {
				// Check for duplicate program (prevent same program in multiple rows)
				if (values.program) {
					let existing_rows = await frappe.db.get_list("Bulk Fee Invoice Creation Row", {
						filters: {
							bulk_fee_invoice_creation: frm.doc.name,
							program: values.program
						},
						fields: ["name", "program"]
					});
					
					// If editing, exclude current row from check
					if (is_edit && row_name) {
						existing_rows = existing_rows.filter(r => r.name !== row_name);
					}
					
					// Also filter out rows with empty/null program
					existing_rows = existing_rows.filter(r => r.program && r.program.trim() !== '');
					
					if (existing_rows.length > 0) {
						frappe.msgprint({
							title: __("Validation Error"),
							message: __("This program '{0}' is already selected in another row. Please select a different program.", [values.program]),
							indicator: "orange",
						});
						return;
					}
				}
				
				// Get data from custom table
				const sections = get_sections_from_table();
				
				if (!sections || sections.length === 0) {
					frappe.msgprint({
						title: __("Validation Error"),
						message: __("Please add at least one section"),
						indicator: "orange",
					});
					return;
				}

				// Format for insert/update
				const sections_formatted = sections.map((row) => ({
					doctype: "Bulk Fee Invoice Creation Row Section",
					section: row.section,
				}));

				if (is_edit) {
					// Update existing row
					await frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "Bulk Fee Invoice Creation Row",
							name: row_name,
							fieldname: "program",
							value: values.program,
						},
					});
					
					// Delete existing sections
					const existing_doc = await frappe.db.get_doc("Bulk Fee Invoice Creation Row", row_name);
					if (existing_doc.sections) {
						for (const section_row of existing_doc.sections) {
							await frappe.call({
								method: "frappe.client.delete",
								args: {
									doctype: "Bulk Fee Invoice Creation Row Section",
									name: section_row.name,
								},
							});
						}
					}
					
					// Add new sections
					for (const section_row of sections_formatted) {
						await frappe.call({
							method: "frappe.client.insert",
							args: {
								doc: {
									...section_row,
									parent: row_name,
									parenttype: "Bulk Fee Invoice Creation Row",
									parentfield: "sections",
								},
							},
						});
					}
					
					d.hide();
					frappe.msgprint(__("Row updated successfully"));
				} else {
					// Create new row
					await frappe.call({
						method: "frappe.client.insert",
						args: {
							doc: {
								doctype: "Bulk Fee Invoice Creation Row",
								bulk_fee_invoice_creation: frm.doc.name,
								program: values.program,
								sections: sections_formatted,
							},
						},
						freeze: true,
						freeze_message: __("Creating Row..."),
					});
					d.hide();
					frappe.msgprint(__("Row created successfully"));
				}
				render_rows_table(frm);
			} catch (e) {
				console.error(e);
				frappe.msgprint({
					title: __("Error"),
					message: e.message || (is_edit ? __("Could not update row") : __("Could not create row")),
					indicator: "red",
				});
			}
		},
	});
	
	// Function to get sections data from custom table
	function get_sections_from_table() {
		const rows = d.$wrapper.find(".custom-sections-table tbody tr");
		const sections = [];
		rows.each(function () {
			const $row = $(this);
			// Get value from link control
			const $wrapper = $row.find('.section-link-wrapper');
			const link_control = $wrapper.data('link-control');
			if (link_control) {
				const section = link_control.get_value();
				if (section) {
					sections.push({ section: section });
				}
			}
		});
		return sections;
	}

	// Function to update total students (not displayed in modal, but kept for future use)
	async function update_total_students() {
		const sections = get_sections_from_table();
		total_students = 0;
		
		for (const section_row of sections) {
			if (section_row.section) {
				try {
					const count = await frappe.db.count("Student Group Student", {
						filters: {
							parent: section_row.section,
							active: 1
						}
					});
					total_students += count;
				} catch(e) {
					// Silently handle errors
				}
			}
		}
	}

	// Function to render custom table
	function render_custom_table() {
		const sections_html = `
			<div class="custom-sections-container">
				<label class="control-label">${__("Sections")} <span class="text-muted">(${__("Required")})</span></label>
				<table class="custom-sections-table table table-bordered" style="margin-top: 10px;">
					<thead>
						<tr>
							<th style="width: 85%;">${__("Section")}</th>
							<th style="width: 15%; text-align: center;">${__("Action")}</th>
						</tr>
					</thead>
					<tbody>
						${sections_data.map((row, idx) => `
							<tr data-index="${idx}">
								<td>
									<div class="section-link-wrapper" data-section-value="${frappe.utils.escape_html(row.section || "")}"></div>
								</td>
								<td style="text-align: center;">
									<button type="button" class="btn btn-xs btn-secondary remove-row" title="${__("Remove")}">
										<i class="fa fa-remove"></i>
									</button>
								</td>
							</tr>
						`).join("")}
					</tbody>
				</table>
				<button type="button" class="btn btn-sm btn-default add-section-row" style="margin-top: 10px;">
					<i class="fa fa-plus"></i> ${__("Add Row")}
				</button>
			</div>
			<style>
				.custom-sections-container {
					margin: 15px 0;
				}
				.custom-sections-table {
					font-size: 13px;
					margin-bottom: 0;
				}
				.custom-sections-table input {
					font-size: 13px;
					padding: 6px 10px;
				}
				.custom-sections-table th {
					background: #f8f9fa;
					font-weight: 600;
					padding: 10px;
					border-bottom: 2px solid #d1d8dd;
				}
				.custom-sections-table td {
					padding: 8px;
					vertical-align: middle;
				}
				.custom-sections-table tbody tr:hover {
					background-color: #f8f9fa;
				}
				.section-link-wrapper {
					position: relative;
				}
				.section-link-wrapper .frappe-control {
					margin-bottom: 0;
				}
				.section-link-wrapper .control-input-wrapper {
					margin-bottom: 0;
				}
				.section-link-wrapper .control-label {
					display: none;
				}
				.section-link-wrapper .form-control {
					height: 36px;
					font-size: 13px;
					border: 1px solid #d1d8dd;
					border-radius: 4px;
				}
				.section-link-wrapper .form-control:focus {
					border-color: #5e64ff;
					box-shadow: 0 0 0 2px rgba(94, 100, 255, 0.1);
				}
				.section-link-wrapper .link-field {
					width: 100%;
				}
				.section-link-wrapper .awesomplete {
					width: 100%;
				}
				.section-link-wrapper .awesomplete > ul {
					z-index: 9999;
					max-height: 300px;
					overflow-y: auto;
					border: 1px solid #d1d8dd;
					border-radius: 4px;
					box-shadow: 0 2px 8px rgba(0,0,0,0.1);
				}
			</style>
		`;
		
		d.fields_dict.sections_html.$wrapper.html(sections_html);
		
		// Function to create inline link field with autocomplete
		function create_section_link_field($wrapper, value = "") {
			$wrapper.empty();
			
			// Create field definition
			const df = {
				fieldname: "section",
				fieldtype: "Link",
				options: "Student Group",
				label: "",
				get_query: function(doc, cdt, cdn) {
					const program_value = d.get_value('program');
					if (program_value) {
						return {
							filters: {
								program: program_value,
								disabled: 0
							}
						};
					}
					return {
						filters: {
							disabled: 0
						}
					};
				}
			};
			
			// Create minimal mock form
			const mock_frm = {
				doc: {},
				fields_dict: {},
				get_doc: function() { return {}; }
			};
			
			// Create control wrapper
			const $control_wrapper = $('<div class="frappe-control" style="margin-bottom: 0;"></div>');
			const $input_area = $('<div class="control-input-wrapper" style="margin-bottom: 0;"></div>');
			$control_wrapper.append($input_area);
			$wrapper.append($control_wrapper);
			
			// Create the Link control
			const link_control = new frappe.ui.form.ControlLink({
				df: df,
				parent: $input_area,
				frm: mock_frm,
				render_input: true
			});
			
			// Store control reference
			$wrapper.data('link-control', link_control);
			
			// Set value if provided - wait for control to be fully initialized
			if (value) {
				// Wait for awesomplete to be set up, then set value
				setTimeout(() => {
					if (link_control && link_control.$input && link_control.$input.length) {
						// First, try to get the display name for the value
						frappe.db.get_value("Student Group", value, "student_group_name").then(function(r) {
							const display_name = r.message && r.message.student_group_name ? r.message.student_group_name : value;
							// Set the input value with display name
							link_control.$input.val(display_name);
							// Store the actual value
							link_control.value = value;
							// Update the link title cache
							frappe.utils.add_link_title("Student Group", value, display_name);
							// Trigger input event to update awesomplete
							link_control.$input.trigger('input');
						}).catch(function() {
							// If fetch fails, just set the value directly
							link_control.$input.val(value);
							link_control.value = value;
							link_control.$input.trigger('input');
						});
					}
				}, 500);
			}
			
			// Update query when program changes
			d.fields_dict.program.$input.off('change.section-update').on('change.section-update', function() {
				const program_value = d.get_value('program');
				if (!program_value && link_control.get_value()) {
					link_control.set_value('');
				}
			});
		}
		
		// Initialize section inputs as Link fields
		setTimeout(() => {
			d.$wrapper.find(".section-link-wrapper").each(function() {
				const $wrapper = $(this);
				const current_value = $wrapper.data("section-value") || "";
				create_section_link_field($wrapper, current_value);
			});
		}, 300);
		
		// Bind add row button
		d.$wrapper.find(".add-section-row").on("click", function () {
			const new_row = `
				<tr>
					<td>
						<div class="section-link-wrapper"></div>
					</td>
					<td style="text-align: center;">
						<button type="button" class="btn btn-xs btn-secondary remove-row" title="${__("Remove")}">
							<i class="fa fa-remove"></i>
						</button>
					</td>
				</tr>
			`;
			const $new_row = $(new_row);
			d.$wrapper.find(".custom-sections-table tbody").append($new_row);
			
			// Add to sections_data
			sections_data.push({});
			
			// Create Link field for the new row
			setTimeout(() => {
				create_section_link_field($new_row.find(".section-link-wrapper"), "");
			}, 100);
		});
		
		// Bind remove row buttons (using event delegation)
		d.$wrapper.on("click", ".remove-row", function () {
			const $row = $(this).closest("tr");
			const idx = $row.data("index");
			if (idx !== undefined) {
				sections_data.splice(idx, 1);
			}
			$row.remove();
		});
	}

	// Load existing data if editing, then show dialog
	if (is_edit) {
		frappe.db.get_doc("Bulk Fee Invoice Creation Row", row_name).then(function(doc) {
			existing_program = doc.program || "";
			
			// Load sections
			if (doc.sections && doc.sections.length > 0) {
				sections_data = doc.sections.map(s => ({ section: s.section || "" }));
			} else {
				sections_data = [{}];
			}
			
			// Show dialog and set values
			d.show();
			setTimeout(() => {
				d.set_value("program", existing_program);
				render_custom_table();
			}, 200);
		}).catch(function(e) {
			console.error("Error loading row data:", e);
			frappe.msgprint({
				title: __("Error"),
				message: __("Could not load row data for editing"),
				indicator: "red",
			});
		});
	} else {
		// Show dialog immediately for new rows
		d.show();
		setTimeout(() => {
			render_custom_table();
		}, 100);
	}
}

async function render_rows_table(frm) {
	// Wait for field to be available
	if (!frm.fields_dict.class_sections_html) {
		setTimeout(function() {
			render_rows_table(frm);
		}, 500);
		return;
	}
	
	let wrapper = frm.fields_dict.class_sections_html.$wrapper || frm.fields_dict.class_sections_html.wrapper;
	if (!wrapper || $(wrapper).length === 0) {
		setTimeout(function() {
			render_rows_table(frm);
		}, 500);
		return;
	}
	
	if (!frm.doc.name) {
		$(wrapper).html(`
			<div style="text-align: center; padding: 20px;">
				<p class="text-muted">Please save the document first to add rows.</p>
			</div>
		`);
		return;
	}

	// Fetch all Rows for this Bulk Fee Invoice Creation
	let rows_list = [];
	try {
		rows_list = await frappe.db.get_list("Bulk Fee Invoice Creation Row", {
			filters: { bulk_fee_invoice_creation: frm.doc.name },
			fields: ["name", "program"],
			order_by: "creation asc",
		});
		
		// Filter out duplicate programs - keep only the first occurrence
		const seen_programs = new Set();
		rows_list = rows_list.filter(row => {
			if (!row.program) return true; // Keep rows without program
			if (seen_programs.has(row.program)) {
				console.warn('[Render Rows Table] Duplicate program detected:', row.program, 'Row:', row.name);
				return false; // Skip duplicate
			}
			seen_programs.add(row.program);
			return true;
		});
	} catch(e) {
		console.error('[Render Rows Table] Error fetching rows:', e);
		rows_list = [];
	}

	// Build HTML table
	let html = `
	<div class="class-sections-wrapper">
		<table class="class-sections-grid">
			<thead>
				<tr>
					<th class="cs-header cs-number">No.</th>
					<th class="cs-header cs-class">Program</th>
					<th class="cs-header cs-sections">Sections</th>
					<th class="cs-header cs-students">Total Students</th>
					<th class="cs-header cs-actions">Actions</th>
				</tr>
			</thead>
			<tbody>`;

	if (rows_list.length > 0) {
		// Fetch full docs with sections
		for (let i = 0; i < rows_list.length; i++) {
			const row = rows_list[i];
			try {
				const full_doc = await frappe.db.get_doc("Bulk Fee Invoice Creation Row", row.name);
				let sections_list = [];
				let sections_display = [];
				let row_total_students = 0;
				
				if (full_doc.sections) {
					sections_list = full_doc.sections.map(s => s.section).filter(s => s);
					// Get section names and student counts for display
					for (let j = 0; j < sections_list.length; j++) {
						try {
							const section_doc = await frappe.db.get_doc("Student Group", sections_list[j]);
							sections_display.push(section_doc.student_group_name || sections_list[j]);
							
							// Count students in this section
							const student_count = await frappe.db.count("Student Group Student", {
								filters: {
									parent: sections_list[j],
									active: 1
								}
							});
							row_total_students += student_count;
						} catch(e) {
							sections_display.push(sections_list[j]);
						}
					}
				}
				
				let program_name = full_doc.program || '';
				// Get program display name
				if (program_name) {
					try {
						const program_doc = await frappe.db.get_doc("Program", program_name);
						program_name = program_doc.program_name || program_name;
					} catch(e) {}
				}

				html += `
				<tr data-row-name="${row.name}">
					<td class="cs-cell cs-number">${i + 1}</td>
					<td class="cs-cell cs-class">${frappe.utils.escape_html(program_name || 'Not set')}</td>
					<td class="cs-cell cs-sections">
						${sections_display.length > 0 ? frappe.utils.escape_html(sections_display.join(', ')) : '<span class="text-muted">No sections</span>'}
						${sections_list.length > 0 ? ` <span class="text-muted">(${sections_list.length} section${sections_list.length > 1 ? 's' : ''})</span>` : ''}
					</td>
					<td class="cs-cell cs-students">
						${row_total_students > 0 ? `<span class="text-primary"><strong>${row_total_students}</strong></span>` : '<span class="text-muted">-</span>'}
					</td>
					<td class="cs-cell cs-actions">
						<button type="button" class="btn btn-xs btn-default edit-row-btn" data-row-name="${row.name}" title="${__('Edit')}">
							<i class="fa fa-edit"></i>
						</button>
						<button type="button" class="btn btn-xs btn-danger delete-row-btn" data-row-name="${row.name}" title="${__('Delete')}" style="margin-left: 5px;">
							<i class="fa fa-trash"></i>
						</button>
					</td>
				</tr>`;
			} catch(e) {
				console.error('[Render Rows Table] Error fetching row:', row.name, e);
			}
		}
	} else {
		html += `
			<tr class="empty-row">
				<td colspan="5" class="text-center text-muted" style="padding: 20px;">
					No rows added. Click "Add Row" button to add a program and sections.
				</td>
			</tr>`;
	}

	html += `
			</tbody>
		</table>
	</div>
	<div style="margin-top: 10px; padding: 10px; border-top: 1px solid #d1d8dd;">
		<button type="button" class="btn btn-sm btn-primary add-row-btn">
			<i class="fa fa-plus"></i> Add Row
		</button>
	</div>
	<style>
     		.class-sections-wrapper {
     			width: 100%;
     			overflow-x: auto;
     			overflow-y: visible;
     			position: relative;
     		}
		.class-sections-grid {
			min-width: 800px;
			width: 100%;
			border-collapse: separate;
			border-spacing: 0;
			font-size: 0.875rem;
			border: 1px solid #d1d8dd;
			border-radius: 4px;
			overflow: hidden;
			box-shadow: 0 1px 2px rgba(0,0,0,0.05);
		}
		.class-sections-grid tbody tr {
			height: 35px;
			max-height: 35px;
		}
     		.class-sections-grid .program-field-wrapper,
     		.class-sections-grid .student-group-field-wrapper {
     			min-height: 32px;
     			overflow: visible;
     			position: relative;
     		}
     		.class-sections-grid .student-group-tag-container {
     			position: relative;
     		}
     		.class-sections-grid .student-group-tag-container .tag-item:hover {
     			background: #f8f9fa;
     		}
     		.class-sections-grid .student-group-tag-container .tag-remove:hover {
     			color: #ff5858;
     		}
     		.class-sections-grid td.cs-sections {
     			overflow: visible;
     		}
     		.class-sections-grid .program-field-wrapper .form-control,
     		.class-sections-grid .student-group-field-wrapper .form-control,
     		.class-sections-grid .program-field-wrapper input,
     		.class-sections-grid .student-group-field-wrapper input {
     			height: 32px;
     			padding: 4px 30px 4px 8px;
     			font-size: 12px;
     			line-height: 1.2;
     			border: 1px solid #d1d8dd;
     			border-radius: 4px;
     			transition: border-color 0.2s, box-shadow 0.2s;
     		}
     		.class-sections-grid .program-field-wrapper .form-control:focus,
     		.class-sections-grid .student-group-field-wrapper .form-control:focus {
     			border-color: #5e64ff;
     			outline: none;
     			box-shadow: 0 0 0 2px rgba(94, 100, 255, 0.1);
     		}
     		.class-sections-grid .program-select-wrapper {
     			position: relative;
     		}
     		.class-sections-grid .program-select-wrapper .select-arrow {
     			position: absolute;
     			right: 10px;
     			top: 50%;
     			transform: translateY(-50%);
     			pointer-events: none;
     			color: #8d99a6;
     			font-size: 10px;
     		}
		.class-sections-grid .program-field-wrapper .link-btn,
		.class-sections-grid .student-group-field-wrapper .multiselect-control {
			height: 28px;
			margin: 0;
		}
		.class-sections-grid thead {
			background: #f8f9fa;
		}
		.class-sections-grid th,
		.class-sections-grid td {
			padding: 4px 8px;
			border-right: 1px solid #e1e6eb;
			border-bottom: 1px solid #e1e6eb;
			text-align: left;
			vertical-align: middle;
		}
     		.class-sections-grid td {
     			min-height: 35px;
     			vertical-align: top;
     			padding: 6px 8px;
     			overflow: visible;
     			position: relative;
     		}
     		.class-sections-grid td.cs-sections {
     			overflow: visible;
     		}
     		.class-sections-grid tbody {
     			overflow: visible;
     		}
		.class-sections-grid tr:last-child td {
			border-bottom: none;
		}
		.class-sections-grid tr td:last-child,
		.class-sections-grid tr th:last-child {
			border-right: none;
		}
		.class-sections-grid .cs-header {
			font-weight: 600;
			background: #f8f9fa;
		}
		.class-sections-grid .cs-select {
			width: 40px;
			text-align: center;
		}
		.class-sections-grid .cs-number {
			width: 50px;
			text-align: center;
		}
		.class-sections-grid .cs-class {
			width: 250px;
		}
		.class-sections-grid .cs-sections {
			width: auto;
			min-width: 300px;
		}
		.class-sections-grid .cs-students {
			width: 120px;
			text-align: center;
		}
		.class-sections-grid .cs-actions {
			width: 120px;
			text-align: center;
		}
		.class-sections-grid .cs-actions .btn {
			margin: 0 2px;
		}
		.class-sections-grid tr:hover td {
			background: #fbfcfd;
		}
		.class-sections-grid .cs-header {
			padding: 12px 8px;
			font-size: 13px;
		}
		.class-sections-grid .cs-cell {
			padding: 10px 8px;
			font-size: 13px;
		}
	</style>`;

	// Use the wrapper we already have
	let $wrapper = $(wrapper);
	$wrapper.html(html);
	
	// Bind handlers
	setTimeout(function() {
		bind_rows_table_handlers(frm, rows_list);
	}, 300);
}

function bind_rows_table_handlers(frm, rows_list) {
	if (!frm.fields_dict.class_sections_html) return;
	let wrapper = frm.fields_dict.class_sections_html.$wrapper || frm.fields_dict.class_sections_html.wrapper;
	if (!wrapper) return;
	const $wrapper = $(wrapper);
	
	// Add Row button
	$wrapper.find('.add-row-btn').off('click').on('click', function() {
		open_add_row_dialog(frm);
	});
	
	// Edit row button - open modal
	$wrapper.find('.edit-row-btn').off('click').on('click', function() {
		let row_name = $(this).data('row-name');
		open_add_row_dialog(frm, row_name);
	});
	
	// Delete row button
	$wrapper.find('.delete-row-btn').off('click').on('click', function() {
		let row_name = $(this).data('row-name');
		frappe.confirm(
			__('Are you sure you want to delete this row?'),
			function() {
				frappe.call({
					method: 'frappe.client.delete',
					args: {
						doctype: 'Bulk Fee Invoice Creation Row',
						name: row_name
					},
					callback: function() {
						frappe.show_alert({
							message: __('Row deleted successfully'),
							indicator: 'green'
						});
						render_rows_table(frm);
					}
				});
			}
		);
	});
}

