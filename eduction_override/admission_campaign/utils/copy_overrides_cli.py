#!/usr/bin/env python3
"""
Standalone script to copy override files (can run without Frappe)
Usage: python copy_overrides_cli.py
"""
import os
import json
import shutil
from pathlib import Path


def get_bench_path():
	"""Get bench root path (apps/ directory)"""
	script_dir = Path(__file__).resolve().parent
	# Go up: utils -> admission_campaign -> eduction_override -> eduction_override -> apps
	bench_path = script_dir.parent.parent.parent.parent.parent
	return bench_path / "apps"


def get_mapping_file():
	"""Get path to file_mappings.json"""
	script_dir = Path(__file__).resolve().parent
	mapping_file = script_dir.parent / "frontend" / "file_mappings.json"
	return mapping_file


def copy_files():
	"""Copy override files to education app"""
	mapping_file = get_mapping_file()
	
	if not mapping_file.exists():
		print(f"❌ Mapping file not found: {mapping_file}")
		return False
	
	# Read mappings
	with open(mapping_file, 'r') as f:
		config = json.load(f)
	
	mappings = config.get("mappings", [])
	if not mappings:
		print("❌ No mappings found in file_mappings.json")
		return False
	
	# Get apps directory
	apps_dir = get_bench_path()
	
	if not apps_dir.exists():
		print(f"❌ Apps directory not found: {apps_dir}")
		return False
	
	copied_count = 0
	backed_up_count = 0
	backup_locations = set()
	
	# Process each mapping
	for mapping in mappings:
		source_path_str = mapping.get("source")
		target_path_str = mapping.get("target")
		description = mapping.get("description", "")
		
		if not source_path_str or not target_path_str:
			continue
		
		# Build full paths from apps directory
		source_path = apps_dir / source_path_str
		target_path = apps_dir / target_path_str
		
		# Check if source exists
		if not source_path.exists():
			print(f"⚠️  Source file not found: {source_path}")
			continue
		
		# Determine backup location dynamically from target path
		# Extract: app_name/frontend/src/... -> app_name/frontend/src_backup
		target_parts = Path(target_path_str).parts
		if len(target_parts) < 3:
			print(f"⚠️  Invalid target path format: {target_path_str}")
			continue
		
		# Find where "frontend" appears in the path
		try:
			frontend_idx = target_parts.index("frontend")
			app_name = target_parts[0]
			# Build backup path: app_name/frontend/src_backup
			backup_base = apps_dir / app_name / "frontend" / "src_backup"
			backup_locations.add(backup_base)
			
			# Create backup directory if needed
			if not backup_base.exists():
				backup_base.mkdir(parents=True)
				print(f"📁 Created backup directory: {backup_base}")
			
			# Get relative path from frontend/src/ for backup filename
			# e.g., education/frontend/src/components/Sidebar.vue -> components/Sidebar.vue
			frontend_src_path = Path(*target_parts[:frontend_idx+1]) / "src"
			target_relative_to_src = Path(target_path_str).relative_to(frontend_src_path)
			
			# Backup target if it exists
			if target_path.exists():
				# Create backup filename from relative path
				backup_filename = str(target_relative_to_src).replace("/", "_")
				backup_path = backup_base / backup_filename
				backup_path.parent.mkdir(parents=True, exist_ok=True)
				shutil.copy2(target_path, backup_path)
				backed_up_count += 1
				print(f"💾 Backed up: {target_path.name}")
		except (ValueError, IndexError) as e:
			print(f"⚠️  Could not determine backup location for {target_path_str}: {e}")
			continue
		
		# Copy override file
		target_path.parent.mkdir(parents=True, exist_ok=True)
		shutil.copy2(source_path, target_path)
		copied_count += 1
		print(f"✅ Copied: {source_path_str} -> {target_path_str} {f'({description})' if description else ''}")
	
	print(f"\n✅ Success! Copied {copied_count} file(s), backed up {backed_up_count} file(s)")
	if backup_locations:
		print(f"📁 Backups saved to:")
		for backup_loc in backup_locations:
			print(f"   - {backup_loc}")
	return True


def restore_backups():
	"""Restore original files from backup"""
	apps_dir = get_bench_path()
	
	# Read mappings to know which files to restore
	mapping_file = get_mapping_file()
	if not mapping_file.exists():
		print("❌ Mapping file not found. Cannot restore.")
		return False
	
	with open(mapping_file, 'r') as f:
		config = json.load(f)
	
	mappings = config.get("mappings", [])
	if not mappings:
		print("❌ No mappings found. Nothing to restore.")
		return False
	
	restored_count = 0
	
	# Restore each mapped file
	for mapping in mappings:
		target_path_str = mapping.get("target")
		if not target_path_str:
			continue
		
		target_path = apps_dir / target_path_str
		
		# Determine backup location dynamically from target path
		target_parts = Path(target_path_str).parts
		if len(target_parts) < 3:
			print(f"⚠️  Invalid target path format: {target_path_str}")
			continue
		
		try:
			# Find where "frontend" appears in the path
			frontend_idx = target_parts.index("frontend")
			app_name = target_parts[0]
			backup_dir = apps_dir / app_name / "frontend" / "src_backup"
			
			if not backup_dir.exists():
				print(f"⚠️  Backup directory not found: {backup_dir}")
				continue
			
			# Get relative path from frontend/src/ for backup filename
			frontend_src_path = Path(*target_parts[:frontend_idx+1]) / "src"
			target_relative_to_src = Path(target_path_str).relative_to(frontend_src_path)
			backup_filename = str(target_relative_to_src).replace("/", "_")
			backup_path = backup_dir / backup_filename
			
			if backup_path.exists():
				target_path.parent.mkdir(parents=True, exist_ok=True)
				shutil.copy2(backup_path, target_path)
				restored_count += 1
				print(f"✅ Restored: {target_path_str}")
			else:
				print(f"⚠️  Backup file not found: {backup_path}")
		except (ValueError, IndexError) as e:
			print(f"⚠️  Could not determine backup location for {target_path_str}: {e}")
			continue
	
	print(f"\n✅ Restored {restored_count} file(s) from backup")
	return True


if __name__ == "__main__":
	import sys
	
	if len(sys.argv) > 1 and sys.argv[1] == "restore":
		restore_backups()
	else:
		success = copy_files()
		sys.exit(0 if success else 1)

