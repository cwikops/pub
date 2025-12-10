# Azure DevOps Bicep Deployment Pipeline

This repository contains an Azure DevOps pipeline for deploying Azure infrastructure using Bicep templates with environment-specific parameters.

## Pipeline Stages

| Stage | Description |
|-------|-------------|
| **Lint** | Validates Bicep syntax, runs linter rules, and validates deployment configuration |
| **Preview** | Runs `what-if` analysis to show planned changes before deployment |
| **Deploy** | Deploys the Bicep templates to the target environment |
| **Validate** | Post-deployment verification of deployed resources |

## Project Structure

```
├── azure-bicep-pipeline.yml    # Main pipeline definition
└── infra/
    ├── main.bicep              # Main deployment template
    ├── bicepconfig.json        # Bicep linter configuration
    ├── modules/
    │   ├── storage.bicep       # Storage account module
    │   ├── appServicePlan.bicep # App Service Plan module
    │   ├── webApp.bicep        # Web App module
    │   └── appInsights.bicep   # Application Insights module
    └── parameters/
        ├── dev.parameters.json     # Development environment parameters
        ├── staging.parameters.json # Staging environment parameters
        └── prod.parameters.json    # Production environment parameters
```

## Prerequisites

### 1. Azure Service Connections

Create service connections in Azure DevOps for each environment:

- `azure-service-connection-dev`
- `azure-service-connection-staging`
- `azure-service-connection-prod`

**To create a service connection:**
1. Go to Project Settings → Service connections
2. Click "New service connection"
3. Select "Azure Resource Manager"
4. Choose "Service principal (automatic)" or "Service principal (manual)"
5. Configure the subscription and resource group scope

### 2. Pipeline Variables

Set up the following variables in your pipeline or variable group:

| Variable | Description |
|----------|-------------|
| `DEV_SUBSCRIPTION_ID` | Azure subscription ID for dev environment |
| `STAGING_SUBSCRIPTION_ID` | Azure subscription ID for staging environment |
| `PROD_SUBSCRIPTION_ID` | Azure subscription ID for production environment |

### 3. Environments

Create environments in Azure DevOps for deployment approvals:

1. Go to Pipelines → Environments
2. Create environments: `dev`, `staging`, `prod`
3. Configure approval gates for `staging` and `prod`

## Usage

### Running the Pipeline

**Via Azure DevOps UI:**
1. Go to Pipelines
2. Select the pipeline
3. Click "Run pipeline"
4. Select the target environment
5. Optionally skip the preview stage

**Via triggers:**
- Automatic on push to `main` or `develop` branches
- Automatic on pull requests to `main` or `develop`

### Pipeline Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `environment` | Target environment (dev/staging/prod) | `dev` |
| `skipPreview` | Skip the what-if preview stage | `false` |

## Environment Configuration

### Development (`dev`)
- **SKU:** B1 (Basic)
- **Storage:** Standard_LRS
- **Location:** East US

### Staging (`staging`)
- **SKU:** S1 (Standard)
- **Storage:** Standard_GRS
- **Location:** East US

### Production (`prod`)
- **SKU:** P1v2 (Premium)
- **Storage:** Standard_ZRS
- **Location:** West US 2

## Customization

### Adding New Resources

1. Create a new module in `infra/modules/`
2. Reference it in `main.bicep`
3. Add required parameters to each environment's parameter file

### Modifying Linter Rules

Edit `infra/bicepconfig.json` to adjust linting rules. Available levels:
- `error` - Fails the build
- `warning` - Shows warning but doesn't fail
- `off` - Disables the rule

### Adding New Environments

1. Create a new parameter file: `infra/parameters/{env}.parameters.json`
2. Add environment to pipeline parameters in `azure-bicep-pipeline.yml`
3. Add environment-specific variables
4. Create the Azure DevOps environment for approvals

## Troubleshooting

### Common Issues

**"Resource group not found"**
- Ensure the service connection has permissions to create resource groups
- Or pre-create the resource group before running the pipeline

**"Linting errors"**
- Review the linting output and fix issues in Bicep files
- Adjust rules in `bicepconfig.json` if needed

**"Deployment validation failed"**
- Check parameter file syntax
- Verify all required parameters are provided
- Ensure API versions are valid

### Debugging Tips

1. Enable verbose logging by adding `--verbose` to Azure CLI commands
2. Check the what-if output to understand planned changes
3. Review deployment outputs for resource details
