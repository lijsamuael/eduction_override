import frappe
from frappe import _


@frappe.whitelist()
def get_students_by_guardian(guardian):
	"""Get all students that have the specified guardian
	
	:param guardian: Guardian name
	:return: List of students with their details
	"""
	if not guardian:
		return []
	
	# Get all Student Guardian records where guardian matches and parenttype is "Student"
	student_guardians = frappe.get_all(
		"Student Guardian",
		filters={"guardian": guardian, "parenttype": "Student"},
		fields=["parent"]
	)
	
	if not student_guardians:
		return []
	
	# Get unique student names
	student_names = list(set([sg.parent for sg in student_guardians]))
	
	# Get student details
	students = frappe.get_all(
		"Student",
		filters={"name": ["in", student_names]},
		fields=["name", "student_name", "date_of_birth", "gender"]
	)
	
	# Get program details for each student from Program Enrollment
	result = []
	for student in students:
		# Get current program enrollment if available
		program = frappe.db.get_value(
			"Program Enrollment",
			{"student": student.name, "docstatus": 1},
			"program",
			order_by="creation desc"
		)
		
		result.append({
			"student": student.name,
			"full_name": student.student_name,
			"date_of_birth": student.date_of_birth,
			"gender": student.gender,
			"program": program or ""
		})
	
	return result


