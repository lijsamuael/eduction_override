# Simple Override Workflow

## Overview

This system copies your override files to the Education app before building. **No vite.config.js modification needed!**

## Quick Start

### 1. Copy Override Files

```bash
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py
```

**What it does:**
- Reads `file_mappings.json`
- Backs up original files to `apps/education/frontend/src_backup/`
- Copies your override files to `apps/education/frontend/src/`

### 2. Build Frontend

```bash
cd apps/education/frontend
yarn build
```

### 3. Restart Bench

```bash
bench restart
```

## Adding New Overrides

1. **Add your file** to `admission_campaign/frontend/src/`
   Example: `admission_campaign/frontend/src/components/MyComponent.vue`

2. **Add mapping** to `file_mappings.json` (paths relative to `apps/`):
   ```json
   {
     "source": "eduction_override/eduction_override/admission_campaign/frontend/src/components/MyComponent.vue",
     "target": "education/frontend/src/components/MyComponent.vue",
     "description": "My custom component"
   }
   ```

3. **Run copy script:**
   ```bash
   python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py
   ```

4. **Build:**
   ```bash
   cd apps/education/frontend && yarn build
   ```

## Restore Original Files

If you want to go back to original Education app files:

```bash
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py restore
```

## File Mappings Format

Edit `admission_campaign/frontend/file_mappings.json`:

```json
{
  "mappings": [
    {
      "source": "eduction_override/eduction_override/admission_campaign/frontend/src/path/to/file.vue",
      "target": "education/frontend/src/path/to/file.vue",
      "description": "What this does"
    }
  ]
}
```

**Important:** All paths are relative to the `apps/` directory. This prevents conflicts when you have multiple apps.

## Example Workflow

```bash
# 1. Make changes to your override files
vim apps/eduction_override/eduction_override/admission_campaign/frontend/src/components/Sidebar.vue

# 2. Copy to education app
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py

# 3. Build
cd apps/education/frontend && yarn build

# 4. Restart
bench restart

# 5. Test in browser
# Open /student-portal and see your changes!
```

## After Education App Updates

When Education app is updated, just re-run the copy script:

```bash
python apps/eduction_override/eduction_override/admission_campaign/utils/copy_overrides_cli.py
cd apps/education/frontend && yarn build
bench restart
```

## Benefits

✅ **Simple** - Just copy files, no complex config  
✅ **Reliable** - Works every time  
✅ **Safe** - Backs up originals automatically  
✅ **Reversible** - Can restore anytime  
✅ **No patches** - No vite.config.js modification needed  

## Current Mappings

- `eduction_override/.../Sidebar.vue` → `education/frontend/src/components/Sidebar.vue`
- `eduction_override/.../SidebarLink.vue` → `education/frontend/src/components/SidebarLink.vue`
- `eduction_override/.../student.js` → `education/frontend/src/stores/student.js`

Edit `file_mappings.json` to add more!

