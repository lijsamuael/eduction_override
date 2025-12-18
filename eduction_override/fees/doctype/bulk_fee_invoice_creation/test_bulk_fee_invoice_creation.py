# Copyright (c) 2024, Eduction Override and contributors
# For license information, please see license.txt

import frappe
import unittest
from frappe.tests.utils import FrappeTestCase


class TestBulkFeeInvoiceCreation(FrappeTestCase):
	def setUp(self):
		"""Set up test data"""
		# Create a test program
		if not frappe.db.exists("Program", "Test Program"):
			frappe.get_doc({
				"doctype": "Program",
				"program_name": "Test Program"
			}).insert()
		
		# Create test student groups
		for i in range(3):
			student_group_name = f"Test Student Group {i+1}"
			if not frappe.db.exists("Student Group", student_group_name):
				frappe.get_doc({
					"doctype": "Student Group",
					"student_group_name": student_group_name,
					"group_based_on": "Batch",
					"program": "Test Program",
					"academic_year": frappe.db.get_value("Academic Year", {"year_start_date": ["<=", frappe.utils.today()]}, "name") or frappe.db.get_single_value("Education Settings", "current_academic_year"),
					"disabled": 0
				}).insert()
	
	def test_student_group_fetching(self):
		"""Test that student groups are fetched correctly for a program"""
		program = "Test Program"
		
		student_groups = frappe.get_all(
			"Student Group",
			filters={
				"program": program,
				"disabled": 0
			},
			fields=["name", "student_group_name"]
		)
		
		self.assertGreater(len(student_groups), 0, "Should have at least one student group")
		self.assertEqual(student_groups[0].get("program"), program, "Student group should belong to the program")
	
	def test_bulk_fee_invoice_creation(self):
		"""Test creating a Bulk Fee Invoice Creation document"""
		# Create the document
		doc = frappe.get_doc({
			"doctype": "Bulk Fee Invoice Creation",
			"fee_structure": frappe.db.get_value("Fee Structure", {}, "name"),
			"posting_date": frappe.utils.today(),
			"due_date": frappe.utils.add_days(frappe.utils.today(), 30),
			"company": frappe.db.get_value("Company", {}, "name")
		})
		
		# Save without validation errors
		try:
			doc.insert()
			self.assertIsNotNone(doc.name, "Document should be saved with a name")
		except Exception as e:
			self.fail(f"Document creation failed: {str(e)}")
		finally:
			if doc.name:
				frappe.delete_doc("Bulk Fee Invoice Creation", doc.name, force=1)
	
	def test_class_section_creation(self):
		"""Test creating a class section with program and student groups"""
		# Create bulk fee invoice creation first
		bfic = frappe.get_doc({
			"doctype": "Bulk Fee Invoice Creation",
			"fee_structure": frappe.db.get_value("Fee Structure", {}, "name"),
			"posting_date": frappe.utils.today(),
			"due_date": frappe.utils.add_days(frappe.utils.today(), 30),
			"company": frappe.db.get_value("Company", {}, "name")
		})
		bfic.insert()
		
		try:
			# Create class section
			class_section = frappe.get_doc({
				"doctype": "Bulk Fee Invoice Creation Class Section",
				"bulk_fee_invoice_creation": bfic.name,
				"class": "Test Program",
				"sections_json": '["Test Student Group 1", "Test Student Group 2"]'
			})
			class_section.insert()
			
			self.assertIsNotNone(class_section.name, "Class section should be saved")
			self.assertEqual(class_section.class, "Test Program", "Program should be set correctly")
			
			import json
			sections = json.loads(class_section.sections_json)
			self.assertEqual(len(sections), 2, "Should have 2 student groups selected")
			
		finally:
			if bfic.name:
				# Clean up
				frappe.db.delete("Bulk Fee Invoice Creation Class Section", {"bulk_fee_invoice_creation": bfic.name})
				frappe.delete_doc("Bulk Fee Invoice Creation", bfic.name, force=1)

