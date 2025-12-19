// Custom client script for Student Admission
// Handles web_form field to automatically fetch route

frappe.ui.form.on('Student Admission', {
	web_form: function(frm) {
		// When web_form is selected, fetch the route
		if (frm.doc.web_form) {
			frappe.db.get_value('Web Form', frm.doc.web_form, 'route', (r) => {
				if (r && r.route) {
					frm.set_value('webform_route', r.route);
				} else {
					// If route is not found, clear the field
					frm.set_value('webform_route', '');
				}
			});
		} else {
			// If web_form is cleared, clear webform_route
			frm.set_value('webform_route', '');
		}
	},
	
	refresh: function(frm) {
		// Ensure webform_route is populated if web_form is set but route is empty
		if (frm.doc.web_form && !frm.doc.webform_route) {
			frappe.db.get_value('Web Form', frm.doc.web_form, 'route', (r) => {
				if (r && r.route) {
					frm.set_value('webform_route', r.route);
				}
			});
		}
	}
});


