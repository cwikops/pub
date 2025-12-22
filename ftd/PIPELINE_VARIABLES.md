# Azure Pipeline Variable Templates

This file contains example variable configurations for different environments.
Copy the appropriate section to your pipeline or Azure DevOps variable groups.

## Production Environment

```yaml
variables:
  # Key Vault Configuration
  keyVaultName: 'ftd-keyvault-prod'
  azureSubscription: 'Azure-Production-Connection'
  
  # Secret Names in Key Vault
  ftdHostSecretName: 'ftd-prod-host'
  ftdUsernameSecretName: 'ftd-prod-username'
  ftdPasswordSecretName: 'ftd-prod-password'
  
  # Environment Settings
  environment: 'production'
  requireApproval: true
  notificationEmail: 'network-team@company.com'
```

## Staging Environment

```yaml
variables:
  # Key Vault Configuration
  keyVaultName: 'ftd-keyvault-staging'
  azureSubscription: 'Azure-Staging-Connection'
  
  # Secret Names in Key Vault
  ftdHostSecretName: 'ftd-staging-host'
  ftdUsernameSecretName: 'ftd-staging-username'
  ftdPasswordSecretName: 'ftd-staging-password'
  
  # Environment Settings
  environment: 'staging'
  requireApproval: false
  notificationEmail: 'dev-team@company.com'
```

## Development Environment

```yaml
variables:
  # Key Vault Configuration
  keyVaultName: 'ftd-keyvault-dev'
  azureSubscription: 'Azure-Development-Connection'
  
  # Secret Names in Key Vault
  ftdHostSecretName: 'ftd-dev-host'
  ftdUsernameSecretName: 'ftd-dev-username'
  ftdPasswordSecretName: 'ftd-dev-password'
  
  # Environment Settings
  environment: 'development'
  requireApproval: false
  notificationEmail: 'qa-team@company.com'
```

## Using Azure DevOps Variable Groups

### Create Variable Group via Azure CLI

```bash
# Production Variable Group
az pipelines variable-group create \
  --name "FTD-Production-Vars" \
  --variables \
    keyVaultName=ftd-keyvault-prod \
    azureSubscription=Azure-Production-Connection \
    ftdHostSecretName=ftd-prod-host \
    ftdUsernameSecretName=ftd-prod-username \
    ftdPasswordSecretName=ftd-prod-password \
  --organization "https://dev.azure.com/YourOrg" \
  --project "YourProject"

# Staging Variable Group
az pipelines variable-group create \
  --name "FTD-Staging-Vars" \
  --variables \
    keyVaultName=ftd-keyvault-staging \
    azureSubscription=Azure-Staging-Connection \
    ftdHostSecretName=ftd-staging-host \
    ftdUsernameSecretName=ftd-staging-username \
    ftdPasswordSecretName=ftd-staging-password \
  --organization "https://dev.azure.com/YourOrg" \
  --project "YourProject"
```

### Reference Variable Group in Pipeline

```yaml
# In azure-pipelines.yml
variables:
  - group: FTD-Production-Vars  # Reference variable group
```

## Using Key Vault Variable Group

### Create Key Vault-Linked Variable Group

1. Go to Azure DevOps > Pipelines > Library
2. Click "Variable groups"
3. Click "+ Variable group"
4. Name: "FTD-Production-Secrets"
5. Enable "Link secrets from an Azure key vault as variables"
6. Select your Azure subscription
7. Select your Key Vault name
8. Authorize
9. Add variables and map to Key Vault secrets
10. Save

### Reference in Pipeline

```yaml
variables:
  - group: FTD-Production-Secrets
```

## Multi-Environment Pipeline Example

```yaml
# azure-pipelines.yml with environment-specific variables

trigger: none

parameters:
  - name: environment
    displayName: 'Target Environment'
    type: string
    default: 'production'
    values:
      - production
      - staging
      - development

variables:
  - ${{ if eq(parameters.environment, 'production') }}:
    - group: FTD-Production-Vars
  - ${{ if eq(parameters.environment, 'staging') }}:
    - group: FTD-Staging-Vars
  - ${{ if eq(parameters.environment, 'development') }}:
    - group: FTD-Development-Vars

stages:
  - stage: RestartFTD
    displayName: 'Restart FTD - ${{ parameters.environment }}'
    jobs:
      - job: Restart
        steps:
          - task: AzureKeyVault@2
            inputs:
              azureSubscription: '$(azureSubscription)'
              KeyVaultName: '$(keyVaultName)'
              SecretsFilter: '$(ftdHostSecretName),$(ftdUsernameSecretName),$(ftdPasswordSecretName)'
```

## Secret Name Mapping

When secrets are retrieved from Key Vault, they become pipeline variables.
The mapping is automatic:

| Key Vault Secret | Pipeline Variable |
|-----------------|-------------------|
| ftd-prod-host | $(ftd-prod-host) |
| ftd-prod-username | $(ftd-prod-username) |
| ftd-prod-password | $(ftd-prod-password) |

Use these in your pipeline:

```yaml
- script: |
    python restart_ftd.py
  env:
    FTD_HOST: $(ftd-prod-host)
    FTD_USERNAME: $(ftd-prod-username)
    FTD_PASSWORD: $(ftd-prod-password)
```

## Security Best Practices

1. **Use Variable Groups for Non-Secrets**
   - Environment names
   - Service connection names
   - Key Vault names

2. **Use Key Vault for Secrets**
   - Passwords
   - API keys
   - Connection strings

3. **Enable Secret Masking**
   - Secrets automatically masked in logs
   - Use `##vso[task.setvariable;issecret=true]` for runtime secrets

4. **Restrict Variable Group Access**
   - Set permissions on variable groups
   - Only authorized users can edit
   - Audit variable group changes

5. **Use Separate Key Vaults**
   - One Key Vault per environment
   - Separate prod/staging/dev credentials
   - Apply least-privilege access

## Variable Precedence

Pipeline variables follow this precedence (highest to lowest):

1. Runtime parameters
2. Pipeline variables (defined in YAML)
3. Variable groups
4. Predefined variables

## Validation Script

Use this script to validate your variable configuration:

```bash
#!/bin/bash

echo "Validating Azure DevOps Variable Configuration"
echo "=============================================="

# Check if variables are set
vars_to_check=(
    "keyVaultName"
    "azureSubscription"
    "ftdHostSecretName"
    "ftdUsernameSecretName"
    "ftdPasswordSecretName"
)

all_set=true

for var in "${vars_to_check[@]}"; do
    if [ -z "${!var}" ]; then
        echo "✗ Missing: $var"
        all_set=false
    else
        echo "✓ Set: $var = ${!var}"
    fi
done

if [ "$all_set" = true ]; then
    echo ""
    echo "✓ All required variables are configured"
    exit 0
else
    echo ""
    echo "✗ Some variables are missing"
    exit 1
fi
```

## Example: Complete Pipeline with Variables

```yaml
trigger: none

parameters:
  - name: environment
    type: string
    default: 'production'
  - name: confirmRestart
    type: string
    default: 'NO'

variables:
  - ${{ if eq(parameters.environment, 'production') }}:
    - group: FTD-Production-Secrets
    - name: keyVaultName
      value: 'ftd-keyvault-prod'
  
stages:
  - stage: Restart
    jobs:
      - job: Execute
        steps:
          - task: AzureKeyVault@2
            inputs:
              azureSubscription: 'Azure-Production'
              KeyVaultName: '$(keyVaultName)'
              SecretsFilter: '*'
          
          - script: |
              python restart_ftd.py
            env:
              FTD_HOST: $(ftd-prod-host)
              FTD_USERNAME: $(ftd-prod-username)
              FTD_PASSWORD: $(ftd-prod-password)
```
