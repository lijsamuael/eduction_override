// Custom JavaScript for Student Applicant Webform
// This displays username and password after successful submission

console.log('Student Applicant Webform JS loaded');

// Store the original frappe.call BEFORE frappe.ready
const originalFrappeCall = frappe.call;

// Override frappe.call to intercept webform responses
frappe.call = function(opts) {
	// Check if this is a webform accept call
	if (opts && opts.method && (
		opts.method === "frappe.website.doctype.web_form.web_form.accept" ||
		opts.method === "eduction_override.eduction_override.web_form.accept" ||
		opts.method.includes("web_form.web_form.accept")
	)) {
		console.log('Intercepted webform accept call', opts.method);
		const originalCallback = opts.callback;
		
		opts.callback = function(response) {
			console.log('Webform response received', response);
			
			// Call original callback first
			if (originalCallback) {
				originalCallback(response);
			}
			
			// Check for credentials in response
			if (response && response.message) {
				const data = response.message;
				console.log('Response message data', data);
				console.log('Has credentials_generated:', data.credentials_generated);
				console.log('Has username:', data.username);
				console.log('Has password:', !!data.password);
				
				// Wait a bit for the success page to render
				setTimeout(function() {
					if (data.credentials_generated && data.username && data.password) {
						console.log('Displaying credentials');
						displayCredentials(data.username, data.password);
					} else if (data.user_exists && data.username) {
						console.log('Displaying user exists message');
						displayUserExistsMessage(data.username);
					} else {
						console.log('No credentials found in response', data);
					}
				}, 1000);
			} else {
				console.log('No message in response', response);
			}
		};
	}
	
	// Call original frappe.call
	return originalFrappeCall.apply(this, arguments);
};

// Also hook into webform handle_success as backup
frappe.ready(function() {
	setTimeout(function() {
		// Check if WebForm class exists
		if (typeof frappe.web_form !== 'undefined' && frappe.web_form.WebForm) {
			const WebFormClass = frappe.web_form.WebForm;
			const originalHandleSuccess = WebFormClass.prototype.handle_success;
			
			WebFormClass.prototype.handle_success = function(data) {
				console.log('handle_success called with data:', data);
				// Call original handler
				originalHandleSuccess.call(this, data);
				
				// Check for credentials
				if (data && data.credentials_generated && data.username && data.password) {
					setTimeout(() => {
						displayCredentials(data.username, data.password);
					}, 500);
				} else if (data && data.user_exists && data.username) {
					setTimeout(() => {
						displayUserExistsMessage(data.username);
					}, 500);
				}
			};
		}
	}, 1000);
});

function displayCredentials(username, password) {
	console.log('displayCredentials called', username, password);
	
	// Check if already displayed
	if ($('.student-credentials-displayed').length) {
		console.log('Credentials already displayed');
		return;
	}
	
	// Update the success message
	const successMessage = $(".success-message");
	if (successMessage.length) {
		const credentialsHtml = `
			<div class="student-credentials-displayed" style="margin-top: 20px; padding: 15px; background-color: #f0f9ff; border: 1px solid #0ea5e9; border-radius: 5px;">
				<h4 style="margin-top: 0; color: #0c4a6e;">Your Login Credentials</h4>
				<p style="margin-bottom: 10px;"><strong>Username:</strong> <code style="background-color: #fff; padding: 2px 6px; border-radius: 3px;">${frappe.utils.escape_html(username)}</code></p>
				<p style="margin-bottom: 10px;"><strong>Password:</strong> <code style="background-color: #fff; padding: 2px 6px; border-radius: 3px;">${frappe.utils.escape_html(password)}</code></p>
				<p style="margin-bottom: 0; font-size: 12px; color: #64748b;"><em>Please save these credentials. You will need them to login to your student portal.</em></p>
			</div>
		`;
		successMessage.after(credentialsHtml);
		console.log('Credentials displayed');
	} else {
		console.log('Success message not found, retrying...');
		// Retry after a delay
		setTimeout(function() {
			displayCredentials(username, password);
		}, 500);
	}
}

function displayUserExistsMessage(username) {
	console.log('displayUserExistsMessage called', username);
	
	// Check if already displayed
	if ($('.student-user-exists-displayed').length) {
		return;
	}
	
	const successMessage = $(".success-message");
	if (successMessage.length) {
		const messageHtml = `
			<div class="student-user-exists-displayed" style="margin-top: 20px; padding: 15px; background-color: #fef3c7; border: 1px solid #f59e0b; border-radius: 5px;">
				<p style="margin-bottom: 10px;"><strong>Username:</strong> <code style="background-color: #fff; padding: 2px 6px; border-radius: 3px;">${frappe.utils.escape_html(username)}</code></p>
				<p style="margin-bottom: 0; font-size: 12px; color: #64748b;">A user account already exists with this email. Please use your existing credentials or reset your password.</p>
			</div>
		`;
		successMessage.after(messageHtml);
	} else {
		setTimeout(function() {
			displayUserExistsMessage(username);
		}, 500);
	}
}
