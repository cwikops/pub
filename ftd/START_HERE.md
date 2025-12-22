# 🚀 START HERE - FTD Restart Automation

## ✅ All Files Present - Package Contents

### 📂 Root Directory Files

| File | Purpose | Size |
|------|---------|------|
| **restart_ftd.py** | Main Python script for FTD restart | 10.6 KB |
| **setup-azure-resources.sh** | Automated Azure setup script | 7.9 KB |
| **requirements.txt** | Python dependencies | 32 bytes |
| **azure-pipelines.yml** | Multi-environment pipeline | 6.5 KB |
| **azure-pipelines-simple.yml** | Simplified pipeline | 2.9 KB |

### 📂 scripts/ Directory

| File | Purpose | Size |
|------|---------|------|
| **restart_ftd.py** | Main Python script (copy for pipeline) | 10.6 KB |

### 📖 Documentation Files

| File | Purpose | Size |
|------|---------|------|
| **README.md** | Complete documentation | 10.2 KB |
| **QUICKSTART.md** | 5-minute setup guide | 4.7 KB |
| **DEPLOYMENT.md** | Deployment overview | 7.3 KB |
| **RUNBOOK.md** | Operational procedures | 11.1 KB |
| **PIPELINE_VARIABLES.md** | Variable reference | 7.1 KB |
| **FILE_LIST.md** | File inventory | 6.9 KB |

### 🔧 Additional Helper Files

| File | Purpose |
|------|---------|
| **setup-keyvault.sh** | Alternative Key Vault setup |
| **test_connectivity.py** | FTD connectivity test script |

---

## 🎯 Quick Start (3 Steps)

### Step 1: Setup Azure Resources
```bash
chmod +x setup-azure-resources.sh
./setup-azure-resources.sh
```
This creates:
- Azure Key Vault
- Service Principal
- Stores FTD credentials

### Step 2: Configure Azure DevOps
1. Create Service Connection using output from Step 1
2. Import pipeline: `azure-pipelines-simple.yml`
3. Update these values in the pipeline:
   ```yaml
   keyVaultName: 'YOUR-VAULT-NAME'
   serviceConnection: 'YOUR-CONNECTION-NAME'
   ```

### Step 3: Run Pipeline
1. Go to Pipelines → Your pipeline
2. Click "Run pipeline"
3. Set parameters:
   - Environment: production
   - Restart Mode: GRACEFUL
   - Confirm: YES
4. Click Run

---

## 📋 Which Files Do You Need?

### For Minimum Setup (Core Files Only)
```
✓ scripts/restart_ftd.py
✓ azure-pipelines-simple.yml
✓ requirements.txt
✓ setup-azure-resources.sh
✓ QUICKSTART.md
```

### For Complete Production Setup
```
✓ All files listed above
```

---

## 🔍 File Locations Explained

**Why are there two restart_ftd.py files?**
- `/restart_ftd.py` - For reference and manual use
- `/scripts/restart_ftd.py` - Used by the pipeline

The pipeline looks for the script at `scripts/restart_ftd.py`, so it MUST be in that location.

---

## 📖 Documentation Guide

**Start Here:**
1. **QUICKSTART.md** - Fast 5-minute setup
2. **README.md** - Complete reference documentation
3. **DEPLOYMENT.md** - Package overview

**For Operations:**
1. **RUNBOOK.md** - Day-to-day operations
2. **PIPELINE_VARIABLES.md** - Configuration reference

---

## ✅ Verify All Files Present

Run this command to verify:
```bash
# Check critical files
test -f scripts/restart_ftd.py && echo "✓ Main script"
test -f azure-pipelines-simple.yml && echo "✓ Pipeline"
test -f setup-azure-resources.sh && echo "✓ Setup script"
test -f requirements.txt && echo "✓ Requirements"
test -f README.md && echo "✓ Documentation"
```

Expected output:
```
✓ Main script
✓ Pipeline
✓ Setup script
✓ Requirements
✓ Documentation
```

---

## 🆘 Troubleshooting

### "Script not found" error in pipeline
**Fix:** Ensure `scripts/restart_ftd.py` exists (not just root `restart_ftd.py`)

### "Cannot find setup script"
**Fix:** Make it executable: `chmod +x setup-azure-resources.sh`

### "Missing requirements"
**Fix:** File is very small (32 bytes), should contain:
```
requests==2.31.0
urllib3==2.1.0
```

---

## 📁 Complete File Tree

```
ftd-restart-automation/
│
├── scripts/
│   └── restart_ftd.py          ← Pipeline uses this
│
├── restart_ftd.py              ← Reference copy
├── setup-azure-resources.sh    ← Run this first
├── requirements.txt            ← Python dependencies
│
├── azure-pipelines.yml         ← Multi-environment
├── azure-pipelines-simple.yml  ← Recommended start
│
├── README.md                   ← Complete docs
├── QUICKSTART.md               ← Start here
├── DEPLOYMENT.md               ← Overview
├── RUNBOOK.md                  ← Operations
├── PIPELINE_VARIABLES.md       ← Config reference
├── FILE_LIST.md                ← File inventory
│
└── docs/                       ← Empty (for your additions)
```

---

## 🎯 Next Actions

1. **Read QUICKSTART.md** for fastest path
2. **Run setup-azure-resources.sh** to create Azure resources
3. **Import azure-pipelines-simple.yml** to Azure DevOps
4. **Run a test** in development environment

---

## ✨ All Files Are Present and Ready!

Total: **15 files** including documentation
Core scripts: **5 files**
Documentation: **6 files**

**Everything you need is here. Start with QUICKSTART.md!** 🚀
