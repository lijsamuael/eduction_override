"""
Copy override files to education app before building
This avoids modifying vite.config.js

Usage:
    bench --site [site] execute eduction_override.admission_campaign.utils.copy_overrides.copy_files
    OR
    python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides.py
"""
import frappe
import os
import json
import shutil
from pathlib import Path


def get_mapping_file_path():
	"""Get path to file_mappings.json"""
	current_file = Path(__file__).resolve()
	# Go up: utils -> admission_campaign -> frontend
	mapping_file = current_file.parent.parent / "frontend" / "file_mappings.json"
	return mapping_file


def get_bench_path():
	"""Get bench root path (apps/ directory)"""
	# Method 1: Try frappe.get_app_path (if available)
	try:
		override_app_path = frappe.get_app_path("eduction_override")
		# Go up from app to apps directory
		apps_dir = Path(override_app_path).parent.parent
		return apps_dir
	except:
		pass
	
	# Method 2: Relative to current file
	current_file_dir = Path(__file__).resolve().parent
	# Go up: utils -> admission_campaign -> eduction_override -> eduction_override -> apps
	bench_path = current_file_dir.parent.parent.parent.parent.parent
	return bench_path / "apps"


@frappe.whitelist()
def copy_files():
	"""Copy override files to education app based on mappings"""
	mapping_file = get_mapping_file_path()
	
	if not mapping_file.exists():
		frappe.throw(f"Mapping file not found: {mapping_file}")
	
	# Read mappings
	with open(mapping_file, 'r') as f:
		config = json.load(f)
	
	mappings = config.get("mappings", [])
	if not mappings:
		frappe.throw("No mappings found in file_mappings.json")
	
	# Get apps directory
	apps_dir = get_bench_path()
	
	if not apps_dir.exists():
		frappe.throw(f"Apps directory not found: {apps_dir}")
	
	copied_files = []
	backed_up_files = []
	backup_locations = set()
	
	# Process each mapping
	for mapping in mappings:
		source_path_str = mapping.get("source")
		target_path_str = mapping.get("target")
		
		if not source_path_str or not target_path_str:
			continue
		
		# Build full paths from apps directory
		source_path = apps_dir / source_path_str
		target_path = apps_dir / target_path_str
		
		# Check if source exists
		if not source_path.exists():
			frappe.logger().warning(f"Source file not found: {source_path}")
			continue
		
		# Determine backup location dynamically from target path
		target_parts = Path(target_path_str).parts
		if len(target_parts) < 3:
			frappe.logger().warning(f"Invalid target path format: {target_path_str}")
			continue
		
		try:
			# Find where "frontend" appears in the path
			frontend_idx = target_parts.index("frontend")
			app_name = target_parts[0]
			# Build backup path: app_name/frontend/src_backup
			backup_base = apps_dir / app_name / "frontend" / "src_backup"
			backup_locations.add(backup_base)
			
			# Create backup directory if needed
			if not backup_base.exists():
				backup_base.mkdir(parents=True)
				frappe.logger().info(f"Created backup directory: {backup_base}")
			
			# Get relative path from frontend/src/ for backup filename
			frontend_src_path = Path(*target_parts[:frontend_idx+1]) / "src"
			target_relative_to_src = Path(target_path_str).relative_to(frontend_src_path)
			backup_filename = str(target_relative_to_src).replace("/", "_")
			backup_path = backup_base / backup_filename
			
			# Backup target if it exists
			if target_path.exists():
				backup_path.parent.mkdir(parents=True, exist_ok=True)
				shutil.copy2(target_path, backup_path)
				backed_up_files.append(str(target_path))
				frappe.logger().info(f"Backed up: {target_path} -> {backup_path}")
		except (ValueError, IndexError) as e:
			frappe.logger().warning(f"Could not determine backup location for {target_path_str}: {e}")
			continue
		
		# Copy override file
		# Create target directory if needed
		target_path.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(source_path, target_path)
		copied_files.append(str(target_path))
		frappe.logger().info(f"Copied: {source_path} -> {target_path}")
	
	backup_locations_str = ", ".join(str(loc) for loc in backup_locations) if backup_locations else "None"
	
	result = {
		"copied": copied_files,
		"backed_up": backed_up_files,
		"backup_locations": [str(loc) for loc in backup_locations],
		"count": len(copied_files)
	}
	
	frappe.msgprint(f"✅ Copied {len(copied_files)} file(s). Backups saved to: {backup_locations_str}")
	return result


@frappe.whitelist()
def restore_backups():
	"""Restore original files from backup"""
	apps_dir = get_bench_path()
	
	# Read mappings to know which files to restore
	mapping_file = get_mapping_file_path()
	if not mapping_file.exists():
		frappe.throw("Mapping file not found. Cannot restore.")
	
	with open(mapping_file, 'r') as f:
		config = json.load(f)
	
	mappings = config.get("mappings", [])
	if not mappings:
		frappe.throw("No mappings found. Nothing to restore.")
	
	restored_files = []
	
	# Restore each mapped file
	for mapping in mappings:
		target_path_str = mapping.get("target")
		if not target_path_str:
			continue
		
		target_path = apps_dir / target_path_str
		
		# Determine backup location dynamically from target path
		target_parts = Path(target_path_str).parts
		if len(target_parts) < 3:
			frappe.logger().warning(f"Invalid target path format: {target_path_str}")
			continue
		
		try:
			# Find where "frontend" appears in the path
			frontend_idx = target_parts.index("frontend")
			app_name = target_parts[0]
			backup_dir = apps_dir / app_name / "frontend" / "src_backup"
			
			if not backup_dir.exists():
				frappe.logger().warning(f"Backup directory not found: {backup_dir}")
				continue
			
			# Get relative path from frontend/src/ for backup filename
			frontend_src_path = Path(*target_parts[:frontend_idx+1]) / "src"
			target_relative_to_src = Path(target_path_str).relative_to(frontend_src_path)
			backup_filename = str(target_relative_to_src).replace("/", "_")
			backup_path = backup_dir / backup_filename
			
			if backup_path.exists():
				target_path.parent.mkdir(parents=True, exist_ok=True)
				shutil.copy2(backup_path, target_path)
				restored_files.append(str(target_path))
				frappe.logger().info(f"Restored: {backup_path} -> {target_path}")
			else:
				frappe.logger().warning(f"Backup file not found: {backup_path}")
		except (ValueError, IndexError) as e:
			frappe.logger().warning(f"Could not determine backup location for {target_path_str}: {e}")
			continue
	
	frappe.msgprint(f"✅ Restored {len(restored_files)} file(s) from backup")
	return {"restored": restored_files, "count": len(restored_files)}


if __name__ == "__main__":
	# Can be run directly without Frappe
	import sys
	sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "..", "..", "apps"))
	
	try:
		import frappe
		frappe.init()
		result = copy_files()
		print(f"✅ Copied {result['count']} file(s)")
		print(f"Backup location: {result['backup_location']}")
	except Exception as e:
		print(f"Error: {e}")
		sys.exit(1)

