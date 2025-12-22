# Cisco FTD Restart Automation - Azure DevOps Pipeline

Complete solution for automating Cisco FTD restarts using Azure DevOps pipelines with credentials stored securely in Azure Key Vault.

## Architecture Overview

```
Azure DevOps Pipeline
  ├── Retrieve credentials from Azure Key Vault
  ├── Execute Python restart script
  ├── Monitor FTD recovery
  └── Post-restart verification
```

## Prerequisites

### 1. Azure Resources
- Azure Key Vault (to store FTD credentials)
- Azure DevOps organization and project
- Azure service connection configured in Azure DevOps

### 2. Azure DevOps Configuration
- Service connection with Key Vault access
- Repository with pipeline files
- Environment configured for approvals (optional)

### 3. Network Requirements
- Azure DevOps agent must have network connectivity to FTD management interface
- FTD management interface must be accessible via HTTPS
- Self-signed certificates are supported

## Setup Instructions

### Step 1: Create Azure Key Vault and Store Credentials

```bash
# Variables
RESOURCE_GROUP="your-rg-name"
KEYVAULT_NAME="your-keyvault-name"
LOCATION="eastus"
FTD_USERNAME="admin"
FTD_PASSWORD="YourSecurePassword"

# Create Key Vault
az keyvault create \
  --name "$KEYVAULT_NAME" \
  --resource-group "$RESOURCE_GROUP" \
  --location "$LOCATION" \
  --enable-rbac-authorization false

# Store FTD credentials
az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "ftd-username" \
  --value "$FTD_USERNAME"

az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "ftd-password" \
  --value "$FTD_PASSWORD"

# Verify secrets
az keyvault secret list \
  --vault-name "$KEYVAULT_NAME" \
  --query "[].name" \
  --output table
```

### Step 2: Configure Azure DevOps Service Connection

1. Navigate to Azure DevOps Project Settings
2. Go to Service connections
3. Create new Azure Resource Manager connection
4. Configure with appropriate permissions to access Key Vault

**Grant Key Vault Access:**

```bash
# Get service principal ID from Azure DevOps service connection
SERVICE_PRINCIPAL_ID="your-sp-object-id"

# Grant access to Key Vault
az keyvault set-policy \
  --name "$KEYVAULT_NAME" \
  --object-id "$SERVICE_PRINCIPAL_ID" \
  --secret-permissions get list
```

### Step 3: Configure Pipeline in Azure DevOps

1. **Create Repository Structure:**
   ```
   your-repo/
   ├── restart_ftd.py
   ├── azure-pipelines.yml
   ├── requirements.txt
   └── README.md
   ```

2. **Update Pipeline Variables:**
   
   Edit `azure-pipelines.yml` and update:
   ```yaml
   variables:
     - name: keyVaultName
       value: 'your-keyvault-name'  # Your Key Vault name
     - name: azureSubscription
       value: 'your-service-connection-name'  # Your service connection name
   ```

3. **Create Pipeline in Azure DevOps:**
   - Go to Pipelines → New Pipeline
   - Select your repository
   - Choose "Existing Azure Pipelines YAML file"
   - Select `azure-pipelines.yml`
   - Save (don't run yet)

### Step 4: Configure Environments (Optional but Recommended)

Create environments for approval gates:

```bash
# In Azure DevOps:
# Pipelines → Environments → New Environment
# Name: production
# Add approvers for production restarts
```

## Usage

### Running the Pipeline

1. **Navigate to Pipelines** in Azure DevOps
2. **Select the FTD Restart pipeline**
3. **Click "Run pipeline"**
4. **Provide required parameters:**
   - **FTD Host**: IP address or FQDN of FTD (e.g., `10.0.1.100`)
   - **Restart Mode**: `GRACEFUL` or `FORCED`
   - **Environment**: `production`, `staging`, or `development`

5. **Review and approve** (if approval gates are configured)
6. **Monitor pipeline execution**

### Pipeline Parameters

| Parameter | Description | Values | Default |
|-----------|-------------|--------|---------|
| ftdHost | FTD management IP/FQDN | Any valid address | (required) |
| restartMode | Type of restart | GRACEFUL, FORCED | GRACEFUL |
| environment | Target environment | production, staging, development | production |

### Restart Modes

**GRACEFUL:**
- Saves running configuration
- Cleanly shuts down services
- Recommended for normal restarts
- Takes slightly longer

**FORCED:**
- Immediate restart
- May not save latest changes
- Use only in emergency situations
- Faster but riskier

## Pipeline Stages

### Stage 1: Validation
- Validates input parameters
- Ensures FTD host is specified
- Checks restart mode is valid

### Stage 2: RestartFTD
- Retrieves credentials from Key Vault
- Executes Python restart script
- Initiates FTD restart via API

### Stage 3: PostRestart
- Waits 5 minutes for FTD to begin booting
- Checks FTD availability (10 attempts, 60s intervals)
- Provides manual verification checklist

## Security Best Practices

### 1. Key Vault Access
```bash
# Use RBAC for granular access control
az role assignment create \
  --assignee "$SERVICE_PRINCIPAL_ID" \
  --role "Key Vault Secrets User" \
  --scope "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME"
```

### 2. Secret Rotation
```bash
# Update FTD password in Key Vault
az keyvault secret set \
  --vault-name "$KEYVAULT_NAME" \
  --name "ftd-password" \
  --value "$NEW_PASSWORD"

# No pipeline changes needed - automatically uses new value
```

### 3. Audit Logging
```bash
# Enable Key Vault diagnostic settings
az monitor diagnostic-settings create \
  --name "KeyVault-Diagnostics" \
  --resource "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME" \
  --logs '[{"category": "AuditEvent", "enabled": true}]' \
  --workspace "$LOG_ANALYTICS_WORKSPACE_ID"
```

## Troubleshooting

### Issue: Authentication Failed

**Symptoms:**
```
ERROR: Authentication failed: HTTP 401
```

**Solutions:**
1. Verify credentials in Key Vault:
   ```bash
   az keyvault secret show \
     --vault-name "$KEYVAULT_NAME" \
     --name "ftd-username"
   ```

2. Test FTD credentials manually:
   ```bash
   curl -k -X POST https://<FTD_HOST>/api/fdm/latest/fdm/token \
     -H "Content-Type: application/json" \
     -d '{"grant_type":"password","username":"admin","password":"password"}'
   ```

3. Check FTD password policy and account lockout

### Issue: Key Vault Access Denied

**Symptoms:**
```
ERROR: Failed to retrieve FTD username from Key Vault
```

**Solutions:**
1. Verify service connection permissions:
   ```bash
   az keyvault show \
     --name "$KEYVAULT_NAME" \
     --query properties.accessPolicies
   ```

2. Grant access policy:
   ```bash
   az keyvault set-policy \
     --name "$KEYVAULT_NAME" \
     --object-id "$SERVICE_PRINCIPAL_ID" \
     --secret-permissions get list
   ```

### Issue: FTD Not Reachable

**Symptoms:**
```
ERROR: FTD is not reachable: Connection timeout
```

**Solutions:**
1. Check Azure DevOps agent networking
2. Verify FTD management interface is accessible
3. Check firewall rules and NSG
4. Test connectivity:
   ```bash
   # From pipeline agent
   curl -k https://<FTD_HOST>
   ```

### Issue: Restart Request Failed

**Symptoms:**
```
ERROR: Failed to restart FTD: HTTP 403
```

**Solutions:**
1. Verify user has admin privileges on FTD
2. Check if FTD is already in maintenance mode
3. Review FTD API logs
4. Ensure no pending deployments from FMC

## Advanced Configuration

### Multiple FTD Devices

Create a variable group for multiple FTDs:

```yaml
# azure-pipelines.yml
variables:
  - group: ftd-devices
  # Contains: ftd-prod-1, ftd-prod-2, ftd-staging-1

parameters:
  - name: targetDevice
    displayName: 'Target FTD Device'
    type: string
    values:
      - ftd-prod-1
      - ftd-prod-2
      - ftd-staging-1

# In script:
env:
  FTD_HOST: $($(parameters.targetDevice))
```

### HA Pair Restart

For FTD HA pairs, restart secondary first:

```yaml
parameters:
  - name: haRole
    displayName: 'HA Role'
    type: string
    values:
      - primary
      - secondary

# Add delay between restarts
- bash: |
    if [ "${{ parameters.haRole }}" == "primary" ]; then
      echo "Restarting primary - ensuring secondary is up first"
      sleep 600  # Wait 10 minutes
    fi
```

### Scheduled Restarts

Create scheduled trigger:

```yaml
schedules:
  - cron: "0 2 * * 0"  # Every Sunday at 2 AM UTC
    displayName: Weekly FTD Maintenance Restart
    branches:
      include:
        - main
    always: false  # Only if there are changes
```

### Notification Integration

Add Teams notification:

```yaml
- task: Office365Notification@1
  inputs:
    office365Endpoint: 'Teams-Webhook'
    message: |
      FTD Restart Completed
      Host: ${{ parameters.ftdHost }}
      Status: $(Agent.JobStatus)
  condition: always()
```

## Monitoring and Logging

### Pipeline Logs
- All pipeline runs are logged in Azure DevOps
- Logs retained per organization settings
- Download logs for audit purposes

### FTD Logs
After restart, check FTD logs:
```bash
# SSH to FTD
ssh admin@<FTD_HOST>

# View system logs
show logging
show tech-support
```

### Key Vault Audit
```bash
# Query Key Vault access logs
az monitor activity-log list \
  --resource-id "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME" \
  --start-time 2024-01-01 \
  --query "[].{Time:eventTimestamp, Operation:operationName.value, User:caller}" \
  --output table
```

## Maintenance

### Regular Tasks

**Weekly:**
- Review pipeline execution logs
- Verify FTD credentials are current
- Check for FTD software updates

**Monthly:**
- Rotate FTD credentials
- Review Key Vault access policies
- Test pipeline in non-production environment

**Quarterly:**
- Update Python dependencies
- Review and update documentation
- Audit pipeline permissions

### Updating the Script

1. **Test changes in development:**
   ```bash
   # Clone repository
   git clone <repo-url>
   cd <repo>
   
   # Create feature branch
   git checkout -b feature/update-restart-script
   
   # Make changes to restart_ftd.py
   # Test locally with environment variables
   export FTD_HOST="test-ftd.example.com"
   export FTD_USERNAME="admin"
   export FTD_PASSWORD="password"
   python restart_ftd.py
   ```

2. **Update pipeline:**
   ```bash
   # Commit and push
   git add .
   git commit -m "Update FTD restart script"
   git push origin feature/update-restart-script
   
   # Create pull request
   # Test in development environment
   # Merge to main after approval
   ```

## Best Practices

1. **Always use GRACEFUL restart** unless emergency
2. **Schedule restarts during maintenance windows**
3. **Configure approval gates for production**
4. **Monitor FTD recovery** after restart
5. **Document each restart** in change management system
6. **Test in non-production first**
7. **Have rollback plan** ready
8. **Coordinate with FMC** if applicable
9. **Notify stakeholders** before restart
10. **Keep credentials rotated** regularly

## Emergency Procedures

### If Restart Fails

1. **Check pipeline logs** for error details
2. **Verify FTD is still responsive:**
   ```bash
   curl -k https://<FTD_HOST>
   ```
3. **Access FTD via console** if network unreachable
4. **Check Azure VM status** (if FTD is Azure VM):
   ```bash
   az vm get-instance-view \
     --resource-group "$RESOURCE_GROUP" \
     --name "$FTD_VM_NAME"
   ```
5. **Use Azure portal** to restart VM if necessary
6. **Contact Cisco TAC** if FTD doesn't boot

### Rollback Procedure

If FTD doesn't come back online:

1. **Access via Azure Serial Console**
2. **Revert to previous configuration:**
   ```
   # On FTD console
   system restore
   ```
3. **Force reboot if unresponsive:**
   ```bash
   az vm restart \
     --resource-group "$RESOURCE_GROUP" \
     --name "$FTD_VM_NAME" \
     --force
   ```

## Support and Resources

- **Cisco FTD Documentation**: https://www.cisco.com/c/en/us/support/security/firepower-ngfw/series.html
- **Azure Key Vault**: https://docs.microsoft.com/en-us/azure/key-vault/
- **Azure DevOps**: https://docs.microsoft.com/en-us/azure/devops/
- **Python Requests Library**: https://requests.readthedocs.io/

## License

Internal use only - Customize as needed for your organization.

## Contributing

To contribute improvements:
1. Fork the repository
2. Create feature branch
3. Test thoroughly
4. Submit pull request
5. Document all changes

---

**Last Updated**: December 2024
**Version**: 1.0
**Maintained By**: DevOps Team
