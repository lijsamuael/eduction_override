// Add Student Applicant link to student portal sidebar
// This script injects a link into the Vue.js student portal

(function() {
	console.log('Student Portal Menu JS loaded');
	
	function addStudentApplicantLink() {
		// Only run on student portal pages
		if (!window.location.pathname.includes('/student-portal')) {
			return;
		}

		// Check if link already exists
		if (document.querySelector('[data-student-applicant-link]')) {
			return;
		}

		// Find the sidebar container - try multiple selectors
		let sidebarContainer = document.querySelector('.flex.flex-col.overflow-y-auto');
		
		// If not found, try other selectors
		if (!sidebarContainer) {
			sidebarContainer = document.querySelector('aside, nav, [role="navigation"]');
		}
		
		if (!sidebarContainer) {
			// Retry after delay
			setTimeout(addStudentApplicantLink, 500);
			return;
		}

		// Find all divs with class mx-2 my-0.5 (these are the SidebarLink wrappers)
		const linkWrappers = sidebarContainer.querySelectorAll('.mx-2.my-0.5, .mx-2');
		
		// Find the Attendance wrapper by checking text content of buttons inside
		let insertAfter = null;
		for (let wrapper of linkWrappers) {
			const button = wrapper.querySelector('button');
			if (button) {
				const text = (button.textContent || button.innerText || '').trim();
				if (text === 'Attendance' || text.includes('Attendance')) {
					insertAfter = wrapper;
					break;
				}
			}
		}
		
		// If still not found, try finding any element with "Attendance" text
		if (!insertAfter) {
			const allElements = Array.from(sidebarContainer.querySelectorAll('*'));
			for (let el of allElements) {
				const text = (el.textContent || el.innerText || '').trim();
				if (text === 'Attendance') {
					insertAfter = el.closest('.mx-2') || el.parentElement;
					break;
				}
			}
		}
		
		if (!insertAfter && linkWrappers.length === 0) {
			// Links not ready yet, retry
			setTimeout(addStudentApplicantLink, 500);
			return;
		}

		// Create the Student Applicant link element matching the existing structure exactly
		const linkWrapper = document.createElement('div');
		linkWrapper.className = 'mx-2 my-0.5';
		linkWrapper.setAttribute('data-student-applicant-link', 'true');
		
		// Create button matching SidebarLink component structure exactly
		const link = document.createElement('button');
		link.type = 'button';
		link.className = 'flex h-7 cursor-pointer items-center rounded text-gray-800 duration-300 ease-in-out focus:outline-none focus:transition-none focus-visible:rounded focus-visible:ring-2 focus-visible:ring-gray-400 hover:bg-gray-100';
		
		// Add click handler - use both onclick and addEventListener for better compatibility
		link.addEventListener('click', function(e) {
			e.preventDefault();
			e.stopPropagation();
			console.log('Student Applicant link clicked, navigating to /student_applicant_list');
			// Navigate to the student applicant list page
			window.location.href = '/student_applicant_list';
			return false;
		}, true); // Use capture phase to ensure it fires
		
		// Also add onclick as fallback
		link.onclick = function(e) {
			e.preventDefault();
			e.stopPropagation();
			console.log('Student Applicant link clicked (onclick), navigating to /student_applicant_list');
			window.location.href = '/student_applicant_list';
			return false;
		};
		
		// Add accessibility attributes
		link.setAttribute('role', 'button');
		link.setAttribute('aria-label', 'Student Applicant');
		link.setAttribute('data-href', '/student_applicant_list');
		
		// Create inner div matching SidebarLink structure
		const innerDiv = document.createElement('div');
		innerDiv.className = 'flex items-center duration-300 ease-in-out px-2 py-1';
		
		// Create icon wrapper matching the structure
		const iconWrapper = document.createElement('span');
		iconWrapper.className = 'grid h-5 w-6 flex-shrink-0 place-items-center';
		
		// Create SVG icon (FileText icon) - using inline SVG string for simplicity
		iconWrapper.innerHTML = `
			<svg class="h-4.5 w-4.5 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24" xmlns="http://www.w3.org/2000/svg">
				<path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"></path>
			</svg>
		`;
		
		// Create label
		const label = document.createElement('span');
		label.className = 'flex-shrink-0 text-base duration-300 ease-in-out ml-2 w-auto opacity-100';
		label.textContent = 'Student Applicant';
		
		innerDiv.appendChild(iconWrapper);
		innerDiv.appendChild(label);
		link.appendChild(innerDiv);
		linkWrapper.appendChild(link);

		// Insert after Attendance or append to container
		if (insertAfter && insertAfter.parentElement) {
			if (insertAfter.nextSibling) {
				insertAfter.parentElement.insertBefore(linkWrapper, insertAfter.nextSibling);
			} else {
				insertAfter.parentElement.appendChild(linkWrapper);
			}
			console.log('✓ Student Applicant link added to sidebar');
		} else {
			sidebarContainer.appendChild(linkWrapper);
			console.log('✓ Student Applicant link appended to sidebar');
		}
	}

	// Run when DOM is ready
	if (document.readyState === 'loading') {
		document.addEventListener('DOMContentLoaded', addStudentApplicantLink);
	} else {
		addStudentApplicantLink();
	}

	// Retry with multiple delays to catch Vue.js rendering
	const delays = [500, 1000, 2000, 3000, 5000];
	delays.forEach(delay => {
		setTimeout(addStudentApplicantLink, delay);
	});
	
	// Watch for navigation changes (Vue router)
	const observer = new MutationObserver(() => {
		setTimeout(addStudentApplicantLink, 300);
	});
	
	// Observe the sidebar container for changes
	setTimeout(() => {
		const sidebar = document.querySelector('.flex.flex-col.overflow-y-auto');
		if (sidebar) {
			observer.observe(sidebar, { childList: true, subtree: true });
		}
	}, 1000);
	
	// Watch for Vue app to mount - check for #app element
	const appElement = document.getElementById('app');
	if (appElement) {
		// Watch for Vue to mount
		const appObserver = new MutationObserver(() => {
			setTimeout(addStudentApplicantLink, 500);
		});
		appObserver.observe(appElement, { childList: true, subtree: true });
		
		// Also try after a delay to catch Vue mounting
		setTimeout(() => {
			addStudentApplicantLink();
			// Try multiple times as Vue renders
			for (let i = 0; i < 10; i++) {
				setTimeout(addStudentApplicantLink, i * 500);
			}
		}, 1000);
	}
	
	// Last resort: try after window load
	window.addEventListener('load', () => {
		setTimeout(addStudentApplicantLink, 2000);
	});
})();
