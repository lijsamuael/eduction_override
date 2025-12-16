__version__ = "0.0.1"

# Import auth module to ensure monkey-patch is applied
try:
	from eduction_override.eduction_override.auth import patch_login_manager
	patch_login_manager()
except Exception:
	pass
