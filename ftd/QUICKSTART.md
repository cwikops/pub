# Quick Start Guide - FTD Restart Automation

## 5-Minute Setup

### 1. Run Azure Setup Script

```bash
# Set your Azure subscription
export AZURE_SUBSCRIPTION_ID="your-subscription-id"
export ENVIRONMENT="production"  # or development, staging

# Run setup
./setup-azure-resources.sh
```

This will:
- Create Azure Key Vault
- Store FTD credentials securely
- Create Service Principal
- Output configuration details

### 2. Configure Azure DevOps

#### Create Service Connection
1. Go to Azure DevOps → Project Settings → Service Connections
2. Click "New service connection" → "Azure Resource Manager"
3. Select "Service principal (manual)"
4. Enter details from setup script output:
   - Subscription ID
   - Subscription Name
   - Service Principal ID (App ID)
   - Service Principal Key (Client Secret)
   - Tenant ID
5. Name it: `Azure-ServiceConnection`
6. Verify and save

#### Create Environment (Optional for Production)
1. Go to Pipelines → Environments
2. Create new environment: `ftd-production`
3. Add "Approvals" check
4. Add required approvers

### 3. Update Pipeline Files

#### Option A: Simple Pipeline
Edit `azure-pipelines-simple.yml`:

```yaml
variables:
  keyVaultName: 'kv-ftd-prod'  # From setup script output
  serviceConnection: 'Azure-ServiceConnection'  # Your connection name
```

#### Option B: Multi-Environment Pipeline
Edit `azure-pipelines.yml`:

1. Update service connection name
2. Update Key Vault names for each environment

### 4. Add to Azure DevOps

#### Upload Files
```bash
git add scripts/restart_ftd.py
git add azure-pipelines-simple.yml  # or azure-pipelines.yml
git add requirements.txt
git commit -m "Add FTD restart automation"
git push
```

#### Create Pipeline
1. Go to Pipelines → New Pipeline
2. Select your repository
3. Choose "Existing Azure Pipelines YAML file"
4. Select: `/azure-pipelines-simple.yml`
5. Run and review

### 5. Test Run

1. Click "Run pipeline"
2. Set parameters:
   - **FTD Environment**: Choose your environment
   - **Restart Mode**: Select `GRACEFUL`
   - **Confirm Restart**: Type `YES`
3. Click "Run"
4. Monitor the output

Expected output:
```
✓ Validation passed
Authenticating to FTD at 10.x.x.x
Authentication successful
Connected to device: FTD-PROD-01
Initiating GRACEFUL restart of FTD device
FTD restart initiated successfully
Device will reboot and may take 10-15 minutes
```

## Verification Checklist

After setup, verify:

- [ ] Key Vault created and accessible
- [ ] Secrets stored correctly (ftd-host, ftd-username, ftd-password)
- [ ] Service Principal has Key Vault access
- [ ] Azure DevOps service connection works
- [ ] Pipeline runs successfully
- [ ] FTD restarts as expected

## Common Setup Issues

### Issue: Service Principal Permissions
**Solution:**
```bash
# Grant access manually
az role assignment create \
  --assignee <app-id> \
  --role "Key Vault Secrets User" \
  --scope /subscriptions/<sub-id>/resourceGroups/<rg>/providers/Microsoft.KeyVault/vaults/<vault-name>
```

### Issue: Pipeline Can't Access Key Vault
**Solution:**
1. Verify service connection in Azure DevOps
2. Check service principal has correct role
3. Ensure Key Vault name is correct in pipeline

### Issue: FTD Authentication Failed
**Solution:**
1. Verify FTD credentials in Key Vault:
```bash
az keyvault secret show --vault-name kv-ftd-prod --name ftd-username
az keyvault secret show --vault-name kv-ftd-prod --name ftd-host
```
2. Test FTD API manually:
```bash
curl -k -X POST https://<ftd-ip>/api/fdm/latest/fdm/token \
  -H "Content-Type: application/json" \
  -d '{"grant_type":"password","username":"admin","password":"yourpass"}'
```

## Repository Structure

Recommended structure:
```
ftd-automation/
├── scripts/
│   └── restart_ftd.py
├── azure-pipelines-simple.yml
├── azure-pipelines.yml (optional)
├── requirements.txt
├── README.md
├── QUICKSTART.md (this file)
└── setup-azure-resources.sh
```

## Next Steps

1. **Schedule Automation**: Add cron trigger to pipeline
2. **Add Monitoring**: Integrate with monitoring system
3. **Setup Alerts**: Configure failure notifications
4. **Document Runbook**: Create operational procedures
5. **Test DR**: Verify restart works during incidents

## Support

For issues:
1. Check pipeline logs in Azure DevOps
2. Verify Key Vault access
3. Test FTD API connectivity
4. Review FTD logs after restart

## Production Checklist

Before using in production:

- [ ] Tested in development environment
- [ ] Documented maintenance windows
- [ ] Stakeholders notified
- [ ] Rollback plan ready
- [ ] Monitoring configured
- [ ] Approvals configured for production environment
- [ ] HA failover tested (if applicable)

---

**Ready to automate!** 🚀
