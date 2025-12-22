# FTD Restart Automation - Complete File List

## Directory Structure

```
ftd-restart-automation/
├── scripts/
│   └── restart_ftd.py              # Main Python script for FTD restart (8.9 KB)
│
├── azure-pipelines.yml             # Full-featured multi-environment pipeline (6.5 KB)
├── azure-pipelines-simple.yml      # Simplified single-environment pipeline (2.9 KB)
├── setup-azure-resources.sh        # Automated Azure setup script (7.9 KB)
├── requirements.txt                # Python dependencies (32 bytes)
│
├── DEPLOYMENT.md                   # Complete deployment package overview (7.3 KB)
├── README.md                       # Comprehensive documentation (10.2 KB)
├── QUICKSTART.md                   # 5-minute setup guide (4.7 KB)
├── RUNBOOK.md                      # Operational procedures (11.1 KB)
└── PIPELINE_VARIABLES.md           # Pipeline configuration reference (7.1 KB)
```

## File Descriptions

### Core Scripts

**scripts/restart_ftd.py**
- Main Python script for FTD restart automation
- Uses FTD REST API (v1/fdm/latest)
- Supports GRACEFUL and FORCED restart modes
- Reads credentials from environment variables (populated from Key Vault)
- Comprehensive error handling and logging
- Proper authentication, device info retrieval, and logout
- Executable: Yes

**setup-azure-resources.sh**
- Bash script to automate Azure resource creation
- Creates Resource Group, Key Vault, and Service Principal
- Stores FTD credentials in Key Vault
- Configures RBAC permissions
- Outputs configuration details for Azure DevOps
- Executable: Yes
- Interactive: Prompts for FTD credentials

### Pipeline Files

**azure-pipelines.yml**
- Full-featured Azure DevOps pipeline
- Multi-stage: Validation → RestartFTD → Notification
- Multi-environment support (dev, staging, production)
- Uses deployment environments with approval gates
- Integrated with Azure Key Vault
- Parameters: environment, restartMode, confirmRestart

**azure-pipelines-simple.yml**
- Simplified Azure DevOps pipeline
- Single job execution
- Easier to customize and understand
- Same functionality as full pipeline
- Recommended for single-environment deployments

**requirements.txt**
- Python package dependencies
- requests==2.31.0
- urllib3==2.1.0

### Documentation Files

**DEPLOYMENT.md**
- Complete deployment package overview
- Feature list and component descriptions
- Quick start summary
- Configuration requirements
- Security considerations
- Production deployment checklist

**README.md**
- Comprehensive documentation (10+ KB)
- Prerequisites and setup instructions
- Step-by-step Azure and Azure DevOps configuration
- Usage instructions and parameter reference
- Monitoring and verification procedures
- Troubleshooting guide
- Security best practices
- Production considerations
- Advanced configuration options
- API reference

**QUICKSTART.md**
- 5-minute setup guide
- Streamlined setup process
- Common issues and solutions
- Verification checklist
- Next steps and production checklist

**RUNBOOK.md**
- Operational runbook
- Pre-restart procedures
- Execution steps
- Post-restart verification
- Troubleshooting procedures
- Emergency procedures
- Maintenance and support

**PIPELINE_VARIABLES.md**
- Pipeline variable reference
- Environment-specific configurations
- Variable group setup
- Key Vault secret mapping
- Parameter descriptions

## How to Use These Files

### 1. Initial Setup
```bash
# Run the setup script
./setup-azure-resources.sh
```

### 2. Repository Setup
```bash
# Create new repository or use existing
git init
git add .
git commit -m "Initial commit: FTD restart automation"
git push
```

### 3. Azure DevOps Setup
- Import `azure-pipelines-simple.yml` (recommended for first time)
- OR import `azure-pipelines.yml` (for multi-environment)
- Configure service connection using output from setup script
- Create variable groups (if using multi-environment pipeline)

### 4. Run Pipeline
- Navigate to Pipelines in Azure DevOps
- Select the FTD restart pipeline
- Click "Run pipeline"
- Set parameters and confirm

## File Dependencies

### restart_ftd.py depends on:
- Python 3.11+
- requests library
- urllib3 library
- Environment variables: FTD_HOST, FTD_USERNAME, FTD_PASSWORD, FTD_RESTART_MODE

### Pipeline files depend on:
- scripts/restart_ftd.py (must be in correct location)
- requirements.txt
- Azure Key Vault with secrets
- Azure DevOps service connection

### Setup script depends on:
- Azure CLI installed and logged in
- jq (JSON processor)
- openssl (for random name generation)
- Active Azure subscription

## File Sizes

| File | Size | Type |
|------|------|------|
| scripts/restart_ftd.py | 8.9 KB | Python |
| azure-pipelines.yml | 6.5 KB | YAML |
| azure-pipelines-simple.yml | 2.9 KB | YAML |
| setup-azure-resources.sh | 7.9 KB | Bash |
| requirements.txt | 32 bytes | Text |
| DEPLOYMENT.md | 7.3 KB | Markdown |
| README.md | 10.2 KB | Markdown |
| QUICKSTART.md | 4.7 KB | Markdown |
| RUNBOOK.md | 11.1 KB | Markdown |
| PIPELINE_VARIABLES.md | 7.1 KB | Markdown |
| **Total** | **~72 KB** | - |

## Verification

To verify all files are present:

```bash
# Check main script
test -f scripts/restart_ftd.py && echo "✓ Main script present"

# Check pipelines
test -f azure-pipelines.yml && echo "✓ Full pipeline present"
test -f azure-pipelines-simple.yml && echo "✓ Simple pipeline present"

# Check setup script
test -f setup-azure-resources.sh && echo "✓ Setup script present"

# Check documentation
test -f README.md && echo "✓ README present"
test -f QUICKSTART.md && echo "✓ Quickstart present"
test -f RUNBOOK.md && echo "✓ Runbook present"
test -f DEPLOYMENT.md && echo "✓ Deployment guide present"

# Check requirements
test -f requirements.txt && echo "✓ Requirements present"
```

## Making Scripts Executable

If scripts are not executable after extraction:

```bash
chmod +x scripts/restart_ftd.py
chmod +x setup-azure-resources.sh
```

## Missing Files?

If any files appear to be missing:

1. **Check the correct directory**: All files should be in `ftd-restart-automation/`
2. **Verify extraction**: Ensure all files were extracted from the archive
3. **Check scripts folder**: The main Python script should be in `scripts/`
4. **Review file permissions**: Scripts should be executable

## Start Here

**For first-time users:**
1. Read QUICKSTART.md first
2. Run setup-azure-resources.sh
3. Follow Azure DevOps setup in QUICKSTART.md
4. Import azure-pipelines-simple.yml
5. Run a test

**For detailed setup:**
1. Read README.md completely
2. Review DEPLOYMENT.md for overview
3. Follow step-by-step instructions
4. Reference RUNBOOK.md for operations

**For production deployment:**
1. Complete all setup steps
2. Review security considerations in README.md
3. Complete production checklist in DEPLOYMENT.md
4. Follow procedures in RUNBOOK.md

---

All files are present and ready to use! 🚀
