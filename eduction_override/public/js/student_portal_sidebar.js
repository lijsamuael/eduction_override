// Add Student Applicant menu item to Vue student portal sidebar
// This runs from eduction_override app to customize the sidebar
(function() {
	'use strict';
	
	// Only run on student portal
	if (!window.location.pathname.startsWith('/student-portal')) {
		return;
	}
	
	console.log('Student Portal Sidebar Customization JS loaded');
	
	var added = false; // Track if we've already added the item
	
	function addStudentApplicantMenuItem() {
		// Don't add multiple times
		if (added) {
			return;
		}
		
		// Find the sidebar container - look for the div with overflow-y-auto that contains the menu items
		// The structure is: div.overflow-y-auto > SidebarLink components (rendered as buttons)
		var sidebarContainer = document.querySelector('div.flex.flex-col.overflow-y-auto');
		
		if (!sidebarContainer) {
			// Try alternative selectors
			sidebarContainer = document.querySelector('.overflow-y-auto');
		}
		
		if (!sidebarContainer) {
			return; // Sidebar not ready yet
		}
		
		// Check if Student Applicant link already exists
		var allButtons = sidebarContainer.querySelectorAll('button');
		var existingLink = Array.from(allButtons).find(function(el) {
			var text = (el.textContent || el.innerText || '').trim();
			return text === 'Student Applicant';
		});
		
		if (existingLink) {
			added = true;
			return; // Already exists
		}
		
		// Find all menu item buttons (not the collapse button)
		// Menu items have class "mx-2 my-0.5" and are inside the overflow-y-auto container
		var menuItems = Array.from(sidebarContainer.querySelectorAll('button.mx-2.my-0.5'));
		
		if (menuItems.length === 0) {
			return; // No menu items found yet
		}
		
		// Get the last menu item (should be Attendance)
		var lastMenuItem = menuItems[menuItems.length - 1];
		
		if (lastMenuItem) {
			// Clone the last menu item to get the exact structure
			var newButton = lastMenuItem.cloneNode(true);
			
			// Update the label text - find the span with text-base class
			var labelSpan = newButton.querySelector('span.text-base');
			if (labelSpan) {
				labelSpan.textContent = 'Student Applicant';
			} else {
				// Fallback: find any text node and replace it
				var textNodes = [];
				var walker = document.createTreeWalker(
					newButton,
					NodeFilter.SHOW_TEXT,
					null,
					false
				);
				var node;
				while (node = walker.nextNode()) {
					if (node.textContent.trim()) {
						textNodes.push(node);
					}
				}
				if (textNodes.length > 0) {
					textNodes[0].textContent = 'Student Applicant';
				}
			}
			
			// Remove any active state classes
			newButton.classList.remove('bg-white', 'shadow-sm');
			newButton.classList.add('hover:bg-gray-100');
			
			// Add click handler to navigate to /app/student-applicant
			newButton.onclick = function(e) {
				e.preventDefault();
				e.stopPropagation();
				e.stopImmediatePropagation();
				console.log('Navigating to /app/student-applicant');
				window.location.href = '/app/student-applicant';
				return false;
			};
			
			// Insert after the last menu item
			lastMenuItem.parentNode.insertBefore(newButton, lastMenuItem.nextSibling);
			
			added = true;
			console.log('✅ Added Student Applicant menu item to sidebar');
		}
	}
	
	// Wait for Vue app to be fully loaded
	function waitForVueApp() {
		// Check if the sidebar container exists
		var sidebarContainer = document.querySelector('div.flex.flex-col.overflow-y-auto') || 
		                       document.querySelector('.overflow-y-auto');
		
		if (sidebarContainer) {
			// Check if there are menu items
			var menuItems = sidebarContainer.querySelectorAll('button.mx-2.my-0.5');
			if (menuItems.length > 0) {
				addStudentApplicantMenuItem();
			} else {
				// Wait a bit more
				setTimeout(waitForVueApp, 200);
			}
		} else {
			// Keep waiting
			setTimeout(waitForVueApp, 200);
		}
	}
	
	// Start waiting when DOM is ready
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', function() {
			setTimeout(waitForVueApp, 500);
		});
	} else {
		setTimeout(waitForVueApp, 500);
	}
	
	// Also try multiple times with increasing delays
	[1000, 2000, 3000, 5000].forEach(function(delay) {
		setTimeout(addStudentApplicantMenuItem, delay);
	});
	
	// Watch for DOM changes in the sidebar area
	var observer = new MutationObserver(function(mutations) {
		// Only check if we haven't added it yet
		if (!added) {
			var sidebarContainer = document.querySelector('div.flex.flex-col.overflow-y-auto') || 
			                       document.querySelector('.overflow-y-auto');
			if (sidebarContainer) {
				var menuItems = sidebarContainer.querySelectorAll('button.mx-2.my-0.5');
				if (menuItems.length > 0) {
					addStudentApplicantMenuItem();
				}
			}
		}
	});
	
	// Start observing after a delay
	setTimeout(function() {
		var app = document.querySelector('#app');
		if (app) {
			observer.observe(app, { 
				childList: true, 
				subtree: true,
				attributes: false
			});
		}
	}, 1000);
})();

