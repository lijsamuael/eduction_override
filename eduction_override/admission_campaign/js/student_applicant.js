// Copyright (c) 2024, Eduction Override
// Custom script for Student Applicant to auto-populate siblings from guardian

frappe.ui.form.on('Student Applicant', {
	refresh: function(frm) {
		// Set up event listener for guardian field changes
		if (frm.fields_dict.guardians && frm.fields_dict.guardians.grid) {
			frm.fields_dict.guardians.grid.grid_rows.forEach(function(row) {
				setup_guardian_listener(frm, row);
			});
		}
	},
	
	guardians_add: function(frm, cdt, cdn) {
		// When a new guardian row is added, set up the listener
		let row = locals[cdt][cdn];
		setup_guardian_listener(frm, row);
	}
});

// Listen to guardian field changes in the Student Guardian child table
frappe.ui.form.on('Student Guardian', {
	guardian: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.guardian) {
			fetch_and_populate_siblings(frm, row.guardian);
		}
	}
});

function setup_guardian_listener(frm, row) {
	// This function ensures the guardian field has a change listener
	// The frappe.ui.form.on('Student Guardian') handler above should handle this
	// But we can add additional setup here if needed
}

function fetch_and_populate_siblings(frm, guardian) {
	// Show loading indicator
	frappe.show_alert({
		message: __('Fetching siblings...'),
		indicator: 'blue'
	}, 2);
	
	// Call the API to get students by guardian
	frappe.call({
		method: 'eduction_override.admission_campaign.api.guardian_api.get_students_by_guardian',
		args: {
			guardian: guardian
		},
		callback: function(r) {
			if (r.message && r.message.length > 0) {
				populate_siblings_table(frm, r.message);
				frappe.show_alert({
					message: __('Found {0} sibling(s)', [r.message.length]),
					indicator: 'green'
				}, 3);
			} else {
				frappe.show_alert({
					message: __('No siblings found for this guardian'),
					indicator: 'orange'
				}, 3);
			}
		},
		error: function(r) {
			frappe.show_alert({
				message: __('Error fetching siblings'),
				indicator: 'red'
			}, 3);
		}
	});
}

function populate_siblings_table(frm, students) {
	// Get existing sibling student names to avoid duplicates
	let existing_sibling_students = [];
	if (frm.doc.siblings) {
		frm.doc.siblings.forEach(function(sibling) {
			if (sibling.student) {
				existing_sibling_students.push(sibling.student);
			}
		});
	}
	
	// Add each student as a sibling
	students.forEach(function(student) {
		// Skip if this student is already in the siblings table
		if (existing_sibling_students.includes(student.student)) {
			return;
		}
		
		// Add new sibling row
		let sibling_row = frm.add_child('siblings');
		sibling_row.studying_in_same_institute = 'YES';
		sibling_row.student = student.student;
		sibling_row.full_name = student.full_name;
		sibling_row.gender = student.gender;
		sibling_row.date_of_birth = student.date_of_birth;
		if (student.program) {
			sibling_row.program = student.program;
		}
	});
	
	// Refresh the siblings table
	frm.refresh_field('siblings');
}

