# Cisco FTD Restart Automation - Deployment Package

## Package Contents

This complete solution automates Cisco FTD restarts using Azure DevOps with credentials from Azure Key Vault.

### Files Included

```
ftd-restart-automation/
├── scripts/
│   └── restart_ftd.py              # Main Python script for FTD restart
├── azure-pipelines.yml             # Full-featured multi-environment pipeline
├── azure-pipelines-simple.yml      # Simplified single-environment pipeline
├── setup-azure-resources.sh        # Automated Azure setup script
├── requirements.txt                # Python dependencies
├── README.md                       # Complete documentation
├── QUICKSTART.md                   # 5-minute setup guide
├── RUNBOOK.md                      # Operational runbook
└── PIPELINE_VARIABLES.md           # Pipeline configuration reference
```

## Key Features

✅ **Secure Credential Management**
- Credentials stored in Azure Key Vault
- No hardcoded secrets in code
- Service Principal authentication

✅ **Multi-Environment Support**
- Separate configurations for dev/staging/prod
- Environment-specific Key Vaults
- Manual approval gates for production

✅ **Flexible Restart Options**
- GRACEFUL restart (recommended)
- FORCED restart (emergency use)
- Parameter validation and safety checks

✅ **Production-Ready**
- Comprehensive error handling
- Detailed logging
- Proper cleanup and logout

✅ **Complete Documentation**
- Setup guides
- Troubleshooting procedures
- Operational runbooks

## Quick Start

### 1. Run Azure Setup (5 minutes)
```bash
cd ftd-restart-automation
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export ENVIRONMENT="production"
./setup-azure-resources.sh
```

### 2. Configure Azure DevOps
- Create Service Connection with output from setup script
- Create variable groups for environments
- Import pipeline YAML file

### 3. Run Pipeline
- Select environment
- Choose restart mode
- Type "YES" to confirm
- Execute

See **QUICKSTART.md** for detailed instructions.

## Component Overview

### restart_ftd.py
Python script that:
- Authenticates to FTD using REST API
- Retrieves device information
- Initiates graceful or forced restart
- Handles errors and cleanup
- Uses environment variables from Key Vault

### azure-pipelines.yml
Full-featured pipeline with:
- Multi-stage deployment (Validation → Restart → Notification)
- Environment-specific configurations
- Deployment environments with approval gates
- Parameter validation
- Comprehensive logging

### azure-pipelines-simple.yml
Simplified pipeline for:
- Single job execution
- Easy customization
- Quick deployment
- Minimal configuration

### setup-azure-resources.sh
Automated setup that:
- Creates Azure Key Vault
- Stores FTD credentials securely
- Creates Service Principal
- Configures RBAC permissions
- Outputs configuration details

## Configuration Requirements

### Azure Resources Needed
- Azure Subscription
- Resource Group
- Azure Key Vault (per environment)
- Service Principal with Key Vault access
- Azure DevOps organization and project

### FTD Requirements
- FTD version 6.2.3 or later
- REST API enabled
- Admin credentials
- HTTPS access from Azure

### Network Requirements
- Azure DevOps agent can reach FTD IP
- HTTPS (port 443) access
- Self-signed certificates supported

## Security Considerations

✅ **Credentials Protection**
- All credentials in Azure Key Vault
- Key Vault audit logging enabled
- RBAC-based access control
- No secrets in source control

✅ **Pipeline Security**
- Manual approval for production
- Parameter validation
- Service Principal with least privilege
- Audit trail in Azure DevOps

✅ **Network Security**
- SSL/TLS encryption
- Private endpoints (optional)
- Network isolation (optional)

## Operational Notes

### Restart Impact
- **Duration**: 10-15 minutes total downtime
- **Traffic Impact**: All connections dropped during restart
- **HA Consideration**: Restart standby first in HA pairs

### Recommended Schedule
- **Development**: Anytime
- **Staging**: Off-peak hours
- **Production**: 2-4 AM during maintenance windows

### Monitoring
- Pipeline logs in Azure DevOps (30-day retention)
- Azure Key Vault access logs
- FTD system logs post-restart

## Support and Maintenance

### Troubleshooting
See **README.md** sections:
- Authentication failures
- Connection timeouts
- Key Vault access issues
- API endpoint errors

### Updates
To update the solution:
1. Test changes in development
2. Update version tags
3. Deploy to staging
4. Validate before production

### Backup and Recovery
- Key Vault soft-delete enabled (90 days)
- Pipeline YAML in source control
- Configuration documented

## Advanced Features

### Scheduled Restarts
Add cron trigger to pipeline for automated weekly restarts

### Notifications
Integrate with:
- Microsoft Teams
- Email
- PagerDuty
- ServiceNow

### Multi-FTD Support
Extend to manage multiple FTD devices:
- Loop through device list
- Parallel execution
- Sequential restart with delays

### Health Checks
Add post-restart verification:
- API availability check
- Service health monitoring
- Automated validation

## Customization Options

### Environment Variables
Adjust in pipeline or add to Key Vault:
- `FTD_HOST` - FTD IP or hostname
- `FTD_USERNAME` - Admin username
- `FTD_PASSWORD` - Admin password
- `FTD_RESTART_MODE` - GRACEFUL or FORCED

### Pipeline Parameters
Customize in YAML:
- Environment selection
- Restart mode
- Timeout values
- Notification settings

### Script Extensions
Modify `restart_ftd.py` to:
- Add pre-restart validation
- Implement health checks
- Integrate with monitoring
- Add custom logging

## Production Deployment Checklist

Before deploying to production:

- [ ] Azure resources created (Key Vault, Service Principal)
- [ ] FTD credentials stored in Key Vault
- [ ] Service connection configured in Azure DevOps
- [ ] Variable groups created for each environment
- [ ] Pipeline imported and validated
- [ ] Test run successful in development
- [ ] Test run successful in staging
- [ ] Approval gates configured for production environment
- [ ] Maintenance window scheduled
- [ ] Stakeholders notified
- [ ] Rollback plan documented
- [ ] Monitoring configured
- [ ] HA failover tested (if applicable)
- [ ] Documentation updated with environment-specific details

## Getting Help

1. **Review Documentation**
   - README.md - Complete reference
   - QUICKSTART.md - Fast setup
   - RUNBOOK.md - Operations guide

2. **Check Logs**
   - Azure DevOps pipeline logs
   - Azure Key Vault audit logs
   - FTD system logs

3. **Common Issues**
   - Verify credentials in Key Vault
   - Check network connectivity
   - Validate service principal permissions
   - Ensure FTD API is enabled

4. **Contact Support**
   - Submit feedback via thumbs down in Claude
   - Check Azure DevOps documentation
   - Review Cisco FTD API documentation

## Version History

**v1.0.0** (2024-12-22)
- Initial release
- FTD API restart via REST
- Azure Key Vault integration
- Multi-environment support
- Comprehensive documentation

---

## Ready to Deploy! 🚀

Follow the **QUICKSTART.md** guide to get started in 5 minutes.

For detailed setup and configuration, see **README.md**.

For operational procedures, see **RUNBOOK.md**.
