# Azure Infrastructure Deployment Pipeline

This repository contains Azure DevOps pipelines and Bicep modules for deploying infrastructure across multiple environments.

## 📁 Repository Structure

```
├── bicep/
│   ├── bicepconfig.json                                    # Bicep linting configuration
│   └── components/
│       ├── resourceGroup/
│       │   ├── main.bicep                                  # Resource Group component
│       │   └── parameters/
│       │       ├── dev/main.parameters.json
│       │       ├── sit/main.parameters.json
│       │       ├── uat/main.parameters.json
│       │       └── prod/main.parameters.json
│       ├── vnet/
│       │   ├── main.bicep                                  # Virtual Network component
│       │   └── parameters/
│       │       ├── dev/main.parameters.json
│       │       ├── sit/main.parameters.json
│       │       ├── uat/main.parameters.json
│       │       └── prod/main.parameters.json
│       └── keyVault/
│           ├── main.bicep                                  # Key Vault component
│           └── parameters/
│               ├── dev/main.parameters.json
│               ├── sit/main.parameters.json
│               ├── uat/main.parameters.json
│               └── prod/main.parameters.json
└── pipelines/
    ├── azure-pipelines.yml                                 # Main pipeline with environment/component map
    └── templates/
        └── deploy-environment.yml                          # Reusable template for deploying components
```

## 🚀 Components Deployed

| Component | Description |
|-----------|-------------|
| **Resource Group** | Container for all resources |
| **Virtual Network** | Network infrastructure with configurable subnets |
| **Key Vault** | Secrets management with RBAC authorization |

## 🌍 Environments

| Environment | Address Space | Key Vault SKU | DDoS Protection |
|-------------|---------------|---------------|-----------------|
| Dev | 10.0.0.0/16 | Standard | No |
| SIT | 10.1.0.0/16 | Standard | No |
| UAT | 10.2.0.0/16 | Standard | No |
| Prod | 10.3.0.0/16 | Premium | Yes |

## ⚙️ Prerequisites

### Azure DevOps Service Connections

Create the following service connections in Azure DevOps:

- `azure-service-connection-dev` → Dev subscription
- `azure-service-connection-sit` → SIT subscription
- `azure-service-connection-uat` → UAT subscription
- `azure-service-connection-prod` → Prod subscription

Each service connection requires **Contributor** and **User Access Administrator** roles at the subscription level for deploying resources.

### Permissions Required

The service principal needs:
- `Microsoft.Resources/subscriptions/resourceGroups/write`
- `Microsoft.Network/virtualNetworks/*`
- `Microsoft.KeyVault/vaults/*`

## 🔧 Pipeline Configuration

### Triggers

The pipeline triggers on:
- Push to `main` or `develop` branches
- Pull requests to `main`
- Changes in `bicep/**` or `pipelines/**` paths

### Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `deployDev` | true | Deploy to Development |
| `deploySit` | true | Deploy to SIT |
| `deployUat` | true | Deploy to UAT |
| `deployProd` | false | Deploy to Production |
| `skipValidation` | false | Skip What-If validation |

### Approval Gates

- **UAT**: Requires manual approval from approvers
- **Prod**: Requires manual approval from platform and approvers teams

## 📝 Customization

### Adding New Subnets

Edit the environment parameter file and add to the `subnets` array:

```json
{
  "name": "snet-newsubnet",
  "addressPrefix": "10.x.10.0/24",
  "serviceEndpoints": [
    { "service": "Microsoft.KeyVault" }
  ]
}
```

### Changing Resource Names

Update the parameter files in `bicep/parameters/{environment}/main.parameters.json`:

```json
{
  "resourceGroupConfig": {
    "value": {
      "name": "rg-yourproject-{env}-{region}"
    }
  }
}
```

### Adding New Components

1. Create component directory structure:
   ```
   bicep/components/{componentName}/
   ├── main.bicep
   └── parameters/
       ├── dev/main.parameters.json
       ├── sit/main.parameters.json
       ├── uat/main.parameters.json
       └── prod/main.parameters.json
   ```
2. Add deployment job in `pipelines/templates/deploy-infrastructure.yml`
3. Update verification job to include the new component

## 🔒 Security Features

- **Key Vault**: RBAC authorization enabled by default
- **Purge Protection**: Enabled for SIT, UAT, and Prod
- **Network ACLs**: Deny by default for UAT and Prod
- **Service Endpoints**: Configured for secure service access

## 📊 Pipeline Stages

```
Build → Dev → SIT → [Approval] → UAT → [Approval] → Prod
```

Each deployment stage includes:
1. **Validation**: Bicep syntax and What-If analysis
2. **Deployment**: Azure CLI deployment
3. **Verification**: Resource existence checks

## 🛠️ Local Development

### Validate Bicep Locally

```bash
# Build individual component
az bicep build --file bicep/components/resourceGroup/main.bicep
az bicep build --file bicep/components/vnet/main.bicep
az bicep build --file bicep/components/keyVault/main.bicep
```

### Deploy Components Manually

```bash
# 1. Deploy Resource Group (subscription scope)
az deployment sub create \
  --name "manual-rg-deployment" \
  --location westeurope \
  --template-file bicep/components/resourceGroup/main.bicep \
  --parameters @bicep/components/resourceGroup/parameters/dev/main.parameters.json

# 2. Deploy VNet (resource group scope)
az deployment group create \
  --name "manual-vnet-deployment" \
  --resource-group rg-myproject-dev-weu \
  --template-file bicep/components/vnet/main.bicep \
  --parameters @bicep/components/vnet/parameters/dev/main.parameters.json

# 3. Deploy Key Vault (resource group scope)
az deployment group create \
  --name "manual-kv-deployment" \
  --resource-group rg-myproject-dev-weu \
  --template-file bicep/components/keyVault/main.bicep \
  --parameters @bicep/components/keyVault/parameters/dev/main.parameters.json
```

## 📚 References

- [Bicep Documentation](https://learn.microsoft.com/azure/azure-resource-manager/bicep/)
- [Azure DevOps Pipelines](https://learn.microsoft.com/azure/devops/pipelines/)
- [Azure Naming Conventions](https://learn.microsoft.com/azure/cloud-adoption-framework/ready/azure-best-practices/resource-naming)
