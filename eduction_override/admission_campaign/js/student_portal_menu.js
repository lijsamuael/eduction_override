// Redirect ALL Student Applicant clicks to /app/student-applicant
// This is the standard Frappe list view route
(function() {
	'use strict';
	
	// Skip if we're on the Vue student portal (it has its own menu)
	if (window.location.pathname && window.location.pathname.startsWith('/student-portal')) {
		console.log('Student Portal Menu JS: Skipping on Vue student portal');
		return;
	}
	
	// Skip if Vue router is detected (Vue student portal)
	if (window.Vue && window.Vue.version) {
		console.log('Student Portal Menu JS: Skipping on Vue app');
		return;
	}
	
	console.log('Student Portal Menu JS loaded - redirecting ALL Student Applicant to /app/student-applicant');
	
	// Wrap everything in try-catch to prevent errors from breaking the page
	try {
	
	var correctUrl = '/app/student-applicant';
	var correctUrlFull = window.location.origin + correctUrl;
	
	// Helper function to check if a route should be redirected
	function shouldRedirect(route) {
		if (!route) return false;
		var routeStr = String(route).toLowerCase();
		// Check for student_applicant_list (with underscores)
		if (routeStr.includes('student_applicant_list')) {
			return true;
		}
		// Check for student-applicant routes that are NOT the correct /app/student-applicant route
		if (routeStr.includes('student-applicant') && !routeStr.includes('/app/student-applicant')) {
			return true;
		}
		return false;
	}
	
	// Function to intercept Frappe routing (call this when Frappe is ready)
	function interceptFrappeRouting() {
		// Intercept Frappe's set_route function (most important!)
		if (window.frappe && window.frappe.set_route) {
			var originalSetRoute = window.frappe.set_route;
			// Only intercept if not already intercepted
			if (!originalSetRoute._studentApplicantIntercepted) {
				window.frappe.set_route = function() {
					var route = arguments[0];
					if (shouldRedirect(route)) {
						console.log('🚫 Intercepted frappe.set_route, redirecting from:', route, 'to:', correctUrl);
						return originalSetRoute.call(window.frappe, correctUrl);
					}
					return originalSetRoute.apply(window.frappe, arguments);
				};
				window.frappe.set_route._studentApplicantIntercepted = true;
				console.log('✅ Intercepted frappe.set_route');
			}
		}
		
		// Intercept Frappe's router.route function
		if (window.frappe && window.frappe.router && window.frappe.router.route) {
			var originalRouterRoute = window.frappe.router.route;
			// Only intercept if not already intercepted
			if (!originalRouterRoute._studentApplicantIntercepted) {
				window.frappe.router.route = function() {
					var route = arguments[0];
					if (shouldRedirect(route)) {
						console.log('🚫 Intercepted frappe.router.route, redirecting from:', route, 'to:', correctUrl);
						return originalRouterRoute.call(window.frappe.router, correctUrl);
					}
					return originalRouterRoute.apply(window.frappe.router, arguments);
				};
				window.frappe.router.route._studentApplicantIntercepted = true;
				console.log('✅ Intercepted frappe.router.route');
			}
		}
	}
	
	// Try to intercept immediately
	interceptFrappeRouting();
	
	// Also try when DOM is ready (Frappe might load after this script)
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', interceptFrappeRouting);
	}
	
	// Try multiple times to catch Frappe when it loads
	[100, 300, 500, 1000, 2000].forEach(function(delay) {
		setTimeout(interceptFrappeRouting, delay);
	});
	
	// Intercept window.location.replace
	var originalReplace = window.location.replace;
	window.location.replace = function(url) {
		if (shouldRedirect(url)) {
			console.log('🚫 Intercepted location.replace, redirecting from:', url, 'to:', correctUrlFull);
			return originalReplace.call(window.location, correctUrlFull);
		}
		return originalReplace.apply(window.location, arguments);
	};
	
	// Intercept window.location.assign
	var originalAssign = window.location.assign;
	window.location.assign = function(url) {
		if (shouldRedirect(url)) {
			console.log('🚫 Intercepted location.assign, redirecting from:', url, 'to:', correctUrlFull);
			return originalAssign.call(window.location, correctUrlFull);
		}
		return originalAssign.apply(window.location, arguments);
	};
	
	// Intercept ALL clicks on Student Applicant links - use capture phase (highest priority)
	document.addEventListener('click', function(e) {
		var target = e.target;
		var link = target.closest('a, button, [role="button"]');
		
		if (link) {
			var text = (link.textContent || link.innerText || '').trim();
			var href = link.getAttribute('href') || link.href || '';
			
			// If this is a Student Applicant link, ALWAYS redirect to /app/student-applicant
			if (text === 'Student Applicant' || text.includes('Student Applicant')) {
				// ALWAYS redirect, even if href looks correct (to be safe)
				if (shouldRedirect(href) || href.includes('student') || href === '' || !href) {
					e.preventDefault();
					e.stopPropagation();
					e.stopImmediatePropagation();
					
					console.log('🚫 Redirecting Student Applicant click from:', href, 'to:', correctUrlFull);
					// Use multiple methods to ensure redirect works
					setTimeout(function() {
						window.location.href = correctUrlFull;
					}, 0);
					return false;
				}
			}
		}
	}, true); // Capture phase - runs FIRST
	
	// Fix all Student Applicant links on the page
	function fixAllStudentApplicantLinks() {
		var allElements = document.querySelectorAll('a, button, [role="button"]');
		
		allElements.forEach(function(el) {
			var text = (el.textContent || el.innerText || '').trim();
			var href = el.getAttribute('href') || el.href || '';
			
			if (text === 'Student Applicant' || text.includes('Student Applicant')) {
				// ALWAYS fix Student Applicant links, regardless of current href
				// Remove old onclick
				el.removeAttribute('onclick');
				
				// Add new onclick
				el.onclick = function(e) {
					e.preventDefault();
					e.stopPropagation();
					e.stopImmediatePropagation();
					console.log('🔧 Fixed Student Applicant link, redirecting to:', correctUrlFull);
					window.location.href = correctUrlFull;
					return false;
				};
				
				// If it's an anchor tag, ALWAYS fix the href
				if (el.tagName === 'A') {
					el.href = correctUrl;
					el.setAttribute('href', correctUrl);
					console.log('✅ Fixed Student Applicant link href to:', correctUrl);
				}
			}
		});
	}
	
	// Run immediately
	fixAllStudentApplicantLinks();
	
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', fixAllStudentApplicantLinks);
	} else {
		fixAllStudentApplicantLinks();
	}
	
	// Run multiple times
	[50, 100, 200, 300, 500, 1000, 2000, 3000, 5000].forEach(function(delay) {
		setTimeout(fixAllStudentApplicantLinks, delay);
	});
	
	// Watch for changes
	var observer = new MutationObserver(function() {
		setTimeout(fixAllStudentApplicantLinks, 10);
	});
	
	setTimeout(function() {
		observer.observe(document.body, { 
			childList: true, 
			subtree: true,
			attributes: true,
			attributeFilter: ['href', 'onclick']
		});
	}, 50);
	
	// Intercept Vue router if it exists
	if (window.Vue && window.Vue.prototype && window.Vue.prototype.$router) {
		var originalPush = window.Vue.prototype.$router.push;
		window.Vue.prototype.$router.push = function(location) {
			if (shouldRedirect(location)) {
				console.log('🚫 Intercepted Vue router, redirecting to:', correctUrlFull);
				window.location.href = correctUrlFull;
				return Promise.reject();
			}
			return originalPush.apply(this, arguments);
		};
	}
	} catch (error) {
		console.error('Error in student_portal_menu.js:', error);
	}
})();
