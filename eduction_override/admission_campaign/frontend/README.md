# Frontend Override System (File Mapping Approach)

## How It Works

Instead of modifying `vite.config.js`, this system **copies** your override files to the Education app before building. Simple and reliable!

## File Mappings

Edit `file_mappings.json` to define which files to copy. **Paths are relative to the `apps/` directory** to avoid conflicts:

```json
{
  "mappings": [
    {
      "source": "eduction_override/eduction_override/admission_campaign/frontend/src/components/Sidebar.vue",
      "target": "education/frontend/src/components/Sidebar.vue",
      "description": "Override Sidebar component"
    },
    {
      "source": "eduction_override/eduction_override/admission_campaign/frontend/src/components/SidebarLink.vue",
      "target": "education/frontend/src/components/SidebarLink.vue",
      "description": "Override SidebarLink component"
    },
    {
      "source": "eduction_override/eduction_override/admission_campaign/frontend/src/stores/student.js",
      "target": "education/frontend/src/stores/student.js",
      "description": "Override student store"
    }
  ]
}
```

**Note:** All paths start from `apps/` directory. This ensures no conflicts when you have multiple apps.

## Usage

### Method 1: Using Bench Command

```bash
bench --site [your-site] execute eduction_override.admission_campaign.utils.copy_overrides.copy_files
```

### Method 2: Using Standalone Script

```bash
cd apps/eduction_override/eduction_override/admission_campaign/utils
python copy_overrides_cli.py
```

### Method 3: Direct Python

```bash
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py
```

## Workflow

1. **Copy overrides:**
   ```bash
   python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py
   ```

2. **Build frontend:**
   ```bash
   cd apps/education/frontend
   yarn build
   ```

3. **Restart bench:**
   ```bash
   bench restart
   ```

## Restore Original Files

If you want to restore the original Education app files:

```bash
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py restore
```

## How It Works

1. **Reads** `file_mappings.json` to get file mappings
2. **Backs up** original files to `apps/education/frontend/src_backup/`
3. **Copies** your override files to `apps/education/frontend/src/`
4. **You build** normally - Vite uses the copied files
5. **Restore** when needed to get originals back

## Benefits

✅ **No vite.config.js modification** - Works with standard config  
✅ **Simple and reliable** - Just file copying  
✅ **Easy to understand** - Clear file mappings  
✅ **Safe** - Backs up originals automatically  
✅ **Reversible** - Can restore originals anytime  

## Adding New Overrides

1. Add your override file to `admission_campaign/frontend/src/`
2. Add mapping to `file_mappings.json` (paths relative to `apps/`):
   ```json
   {
     "source": "eduction_override/eduction_override/admission_campaign/frontend/src/components/MyComponent.vue",
     "target": "education/frontend/src/components/MyComponent.vue",
     "description": "My custom component"
   }
   ```
3. Run copy script
4. Build frontend

## File Structure

```
admission_campaign/frontend/
├── src/
│   ├── components/
│   │   ├── Sidebar.vue      ← Your override
│   │   └── SidebarLink.vue  ← Your override
│   └── stores/
│       └── student.js       ← Your override
├── file_mappings.json        ← Mapping configuration
└── README.md
```

## Notes

- Original files are backed up to `apps/education/frontend/src_backup/`
- You can restore originals anytime with `restore` command
- After Education app updates, just re-run the copy script
- No need to modify vite.config.js or apply patches
