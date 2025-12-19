# Admission Campaign Module

This folder contains all customizations for the Admission Campaign functionality.

## Structure

- **api/** - API endpoints
  - `student_api.py` - Student portal and info APIs
  - `guardian_api.py` - Guardian-related APIs
  - `sibling_switch.py` - Sibling switching functionality

- **doctype/** - DocType class overrides
  - `student.py` - CustomStudent class
  - `student_admission.py` - StudentAdmission class
  - `web_form.py` - CustomWebForm class
  - `fee_schedule.py` - CustomFeeSchedule class

- **js/** - JavaScript client scripts
  - `student_admission.js` - Student Admission form scripts
  - `student_applicant.js` - Student Applicant form scripts
  - `student_applicant_webform.js` - Webform scripts
  - `student_portal_menu.js` - Portal menu scripts
  - `student_sibling_switch.js` - Sibling switching UI

- **web_form/** - Web form overrides
  - `web_form.py` - Web form accept override

- **list/** - List view overrides
  - `list_override.py` - List view customizations

- **utils/** - Utility functions
  - `utils.py` - before_request hook
  - `fix_portal_menu.py` - Portal menu fix (after_migrate)
  - `test_and_fix.py` - Testing utility

- **auth/** - Authentication hooks
  - `auth.py` - on_login hook

## Standard Frappe Folders

- **www/** - Web pages (required by Frappe)
  - `student-portal.py` - Student portal page
  - `student_applicant_list.py` - Student applicant list page

- **public/js/** - Public JavaScript (if needed for web pages)

- **templates/** - Jinja templates

- **patches/** - Database migration patches

