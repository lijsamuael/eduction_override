// Custom client script for Student doctype
// Adds sibling switch functionality

frappe.ui.form.on('Student', {
	refresh: function(frm) {
		// Show button for all students when viewing any Student detail form
		// Check if current logged-in user is a student
		const userRoles = frappe.boot.user.roles || [];
		if (userRoles.includes('Student') && !frm.is_new()) {
			// Check if currently impersonated (check boot data first for quick check)
			const isImpersonatedFromBoot = frappe.boot.user.impersonated_by;
			
			// Check if currently impersonated via API
			frappe.call({
				method: 'eduction_override.eduction_override.api.get_original_user',
				callback: function(r) {
					if (r.message) {
						const originalUser = r.message;
						const currentUser = frappe.boot.user.name;
						const isImpersonated = originalUser !== currentUser || isImpersonatedFromBoot;
						
						if (isImpersonated) {
							// Show switch back button prominently
							frappe.db.get_value('User', originalUser, 'full_name', function(user) {
								const originalUserName = user.message ? (user.message.full_name || originalUser) : originalUser;
								frm.add_custom_button(__('Switch Back to {0}', [originalUserName]), function() {
									switchToSibling(originalUser);
								}, __('Actions'));
							});
						}
					}
					
					// Add custom button to switch to siblings
					frm.add_custom_button(__('Switch to Sibling'), function() {
						showSiblingSwitchDialog();
					}, __('Actions'));
				},
				error: function() {
					// If API fails, still add the switch to sibling button
					frm.add_custom_button(__('Switch to Sibling'), function() {
						showSiblingSwitchDialog();
					}, __('Actions'));
				}
			});
		}
	}
});

function showSiblingSwitchDialog() {
	// Get siblings and original user
	frappe.call({
		method: 'eduction_override.eduction_override.api.get_siblings_for_current_student',
		callback: function(r) {
			if (r.message && Array.isArray(r.message) && r.message.length > 0) {
				showSiblingSelectionDialog(r.message);
			} else {
				frappe.show_alert({
					message: __('No siblings found'),
					indicator: 'orange'
				}, 3);
			}
		},
		error: function(r) {
			console.error('Error loading siblings:', r);
			frappe.show_alert({
				message: __('Error loading siblings: ') + (r.message || 'Unknown error'),
				indicator: 'red'
			}, 5);
		}
	});
}

function showSiblingSelectionDialog(siblings) {
	// Get original user to show switch back option
	frappe.call({
		method: 'eduction_override.eduction_override.api.get_original_user',
		callback: function(r) {
			const originalUser = r.message;
			const currentUser = frappe.boot.user.name;
			const isImpersonated = originalUser !== currentUser;

			// Build dialog content
			let dialogContent = '<div style="padding: 20px;">';
			
			if (isImpersonated) {
				// Get original user name
				frappe.db.get_value('User', originalUser, 'full_name', function(user) {
					const originalUserName = user.message.full_name || originalUser;
					
					dialogContent += '<div style="margin-bottom: 20px; padding: 12px; background: #f0f9ff; border: 1px solid #bae6fd; border-radius: 4px;">';
					dialogContent += '<strong>Currently viewing as:</strong> ' + (frappe.boot.user.full_name || currentUser) + '<br>';
					dialogContent += '<strong>Original user:</strong> ' + originalUserName;
					dialogContent += '</div>';
					
					// Add switch back button
					dialogContent += '<button class="btn btn-secondary" style="width: 100%; margin-bottom: 15px;" onclick="switchToSibling(\'' + originalUser + '\')">';
					dialogContent += '<i class="fa fa-arrow-left" style="margin-right: 5px;"></i> Switch back to ' + originalUserName;
					dialogContent += '</button>';
					
					dialogContent += '<hr style="margin: 15px 0;">';
					dialogContent += '<h5 style="margin-bottom: 15px;">Switch to another sibling:</h5>';
					
					// Add sibling list
					if (siblings.length === 0) {
						dialogContent += '<p style="color: #6b7280; text-align: center; padding: 20px;">No siblings available</p>';
					} else {
						siblings.forEach(function(sibling) {
							// Skip if it's the original user or currently viewed user
							if (sibling.user === originalUser || sibling.user === currentUser) {
								return;
							}
							
							const siblingName = sibling.student_name || sibling.user;
							
							dialogContent += '<button class="btn btn-default" style="width: 100%; margin-bottom: 10px; text-align: left; padding: 12px;" onclick="switchToSibling(\'' + sibling.user + '\')">';
							dialogContent += '<div><strong>' + siblingName + '</strong></div></button>';
						});
					}
					
					dialogContent += '</div>';

					// Show dialog
					const dialog = new frappe.ui.Dialog({
						title: __('Switch to Sibling'),
						fields: [
							{
								fieldtype: 'HTML',
								options: dialogContent
							}
						],
						primary_action_label: __('Close'),
						primary_action: function() {
							dialog.hide();
						}
					});

					dialog.show();
				});
			} else {
				// Not impersonated, just show sibling list
				dialogContent += '<h5 style="margin-bottom: 15px;">Select a sibling to switch to:</h5>';
				
				if (siblings.length === 0) {
					dialogContent += '<p style="color: #6b7280; text-align: center; padding: 20px;">No siblings available</p>';
				} else {
					siblings.forEach(function(sibling) {
						const siblingName = sibling.student_name || sibling.user;
						
						dialogContent += '<button class="btn btn-default" style="width: 100%; margin-bottom: 10px; text-align: left; padding: 12px;" onclick="switchToSibling(\'' + sibling.user + '\')">';
						dialogContent += '<div><strong>' + siblingName + '</strong></div></button>';
					});
				}
				
				dialogContent += '</div>';

				// Show dialog
				const dialog = new frappe.ui.Dialog({
					title: __('Switch to Sibling'),
					fields: [
						{
							fieldtype: 'HTML',
							options: dialogContent
						}
					],
					primary_action_label: __('Close'),
					primary_action: function() {
						dialog.hide();
					}
				});

				dialog.show();
			}
		}
	});
}

// Make switchToSibling available globally
window.switchToSibling = function(siblingUser) {
	frappe.call({
		method: 'eduction_override.eduction_override.api.switch_to_sibling',
		args: {
			sibling_user: siblingUser
		},
		callback: function(r) {
			if (r.message) {
				frappe.show_alert({
					message: r.message,
					indicator: 'green'
				}, 3);
				
				// Reload page after a short delay to reflect the switch
				setTimeout(function() {
					window.location.reload();
				}, 1000);
			}
		},
		error: function(r) {
			frappe.show_alert({
				message: r.message || __('Error switching to sibling'),
				indicator: 'red'
			}, 5);
		}
	});
};
