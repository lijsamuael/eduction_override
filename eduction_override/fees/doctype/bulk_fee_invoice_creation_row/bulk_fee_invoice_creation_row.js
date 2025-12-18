// Copyright (c) 2024, Eduction Override and contributors
// For license information, please see license.txt

frappe.ui.form.on('Bulk Fee Invoice Creation Row', {
	onload: function(frm) {
		// Set query for sections based on program
		frm.set_query('section', 'sections', function(doc, cdt, cdn) {
			if (doc.program) {
				return {
					filters: {
						program: doc.program,
						disabled: 0
					}
				};
			}
			return {
				filters: {
					disabled: 0
				}
			};
		});
	},
	
	program: function(frm) {
		// Clear sections when program changes
		if (frm.doc.sections && frm.doc.sections.length > 0) {
			frappe.confirm(__('Changing program will clear all sections. Do you want to continue?'), function() {
				frm.clear_table('sections');
				frm.refresh_field('sections');
			}, function() {
				// Revert program selection
				frm.set_value('program', frm.doc._previous_values.program || '');
			});
		} else {
			// Refresh sections query
			frm.refresh_field('sections');
		}
	}
});

frappe.ui.form.on('Bulk Fee Invoice Creation Row Section', {
	section: function(frm, cdt, cdn) {
		// Validate section belongs to selected program
		let row = locals[cdt][cdn];
		if (frm.doc.program && row.section) {
			frappe.call({
				method: 'frappe.client.get',
				args: {
					doctype: 'Student Group',
					name: row.section
				},
				callback: function(r) {
					if (r.message) {
						if (r.message.program !== frm.doc.program) {
							frappe.msgprint(__('Section {0} does not belong to Program {1}', [row.section, frm.doc.program]));
							frappe.model.set_value(cdt, cdn, 'section', '');
						}
					}
				}
			});
		}
	}
});

