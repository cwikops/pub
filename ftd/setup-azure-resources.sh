#!/bin/bash
#
# Setup script for Azure Key Vault and FTD automation prerequisites
# This script creates the necessary Azure resources for FTD restart automation
#

set -e

# Color output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Configuration
SUBSCRIPTION_ID="${AZURE_SUBSCRIPTION_ID:-}"
ENVIRONMENT="${ENVIRONMENT:-production}"
LOCATION="${LOCATION:-eastus}"

# Resource names
RESOURCE_GROUP="rg-ftd-${ENVIRONMENT}"
KEY_VAULT_NAME="kv-ftd-${ENVIRONMENT}-$(openssl rand -hex 3)"
SERVICE_PRINCIPAL_NAME="sp-ftd-automation-${ENVIRONMENT}"

# FTD configuration (will prompt for these)
FTD_HOST=""
FTD_USERNAME=""
FTD_PASSWORD=""

echo "========================================"
echo "Azure FTD Automation Setup"
echo "========================================"
echo ""

# Check if Azure CLI is installed
if ! command -v az &> /dev/null; then
    print_error "Azure CLI is not installed. Please install it first."
    print_info "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

# Check if logged in
print_info "Checking Azure CLI login status..."
if ! az account show &> /dev/null; then
    print_error "Not logged in to Azure CLI"
    print_info "Please run: az login"
    exit 1
fi

# Get subscription ID if not set
if [ -z "$SUBSCRIPTION_ID" ]; then
    SUBSCRIPTION_ID=$(az account show --query id -o tsv)
    print_info "Using subscription: $SUBSCRIPTION_ID"
fi

# Set subscription
az account set --subscription "$SUBSCRIPTION_ID"

# Prompt for FTD configuration
echo ""
print_info "Please provide FTD configuration details:"
echo ""

read -p "FTD IP Address or Hostname: " FTD_HOST
read -p "FTD Admin Username [admin]: " FTD_USERNAME
FTD_USERNAME=${FTD_USERNAME:-admin}
read -s -p "FTD Admin Password: " FTD_PASSWORD
echo ""

# Validate inputs
if [ -z "$FTD_HOST" ] || [ -z "$FTD_PASSWORD" ]; then
    print_error "FTD host and password are required"
    exit 1
fi

echo ""
print_info "Configuration Summary:"
echo "  Environment: $ENVIRONMENT"
echo "  Location: $LOCATION"
echo "  Resource Group: $RESOURCE_GROUP"
echo "  Key Vault: $KEY_VAULT_NAME"
echo "  FTD Host: $FTD_HOST"
echo "  FTD Username: $FTD_USERNAME"
echo ""

read -p "Proceed with setup? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_warning "Setup cancelled"
    exit 0
fi

# Create Resource Group
echo ""
print_info "Creating resource group: $RESOURCE_GROUP"
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Resource group already exists"
else
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    print_info "Resource group created successfully"
fi

# Create Key Vault
echo ""
print_info "Creating Key Vault: $KEY_VAULT_NAME"
if az keyvault show --name "$KEY_VAULT_NAME" &> /dev/null; then
    print_warning "Key Vault already exists"
else
    az keyvault create \
        --name "$KEY_VAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --enable-rbac-authorization true \
        --output none
    print_info "Key Vault created successfully"
fi

# Get Key Vault ID
KEY_VAULT_ID=$(az keyvault show --name "$KEY_VAULT_NAME" --query id -o tsv)

# Create Service Principal
echo ""
print_info "Creating Service Principal: $SERVICE_PRINCIPAL_NAME"

SP_OUTPUT=$(az ad sp create-for-rbac \
    --name "$SERVICE_PRINCIPAL_NAME" \
    --role "Key Vault Secrets User" \
    --scopes "$KEY_VAULT_ID" \
    --output json 2>/dev/null || echo '{}')

if [ "$SP_OUTPUT" = "{}" ]; then
    print_warning "Service Principal may already exist or creation failed"
    print_info "Attempting to retrieve existing service principal..."
    
    APP_ID=$(az ad sp list --display-name "$SERVICE_PRINCIPAL_NAME" --query "[0].appId" -o tsv)
    
    if [ -n "$APP_ID" ]; then
        print_info "Found existing Service Principal with App ID: $APP_ID"
        
        # Ensure it has the correct role
        az role assignment create \
            --assignee "$APP_ID" \
            --role "Key Vault Secrets User" \
            --scope "$KEY_VAULT_ID" \
            --output none 2>/dev/null || true
    fi
else
    print_info "Service Principal created successfully"
    
    SP_APP_ID=$(echo "$SP_OUTPUT" | jq -r '.appId')
    SP_PASSWORD=$(echo "$SP_OUTPUT" | jq -r '.password')
    SP_TENANT=$(echo "$SP_OUTPUT" | jq -r '.tenant')
    
    echo ""
    print_info "Service Principal Details (save these for Azure DevOps):"
    echo "  Application (client) ID: $SP_APP_ID"
    echo "  Client Secret: $SP_PASSWORD"
    echo "  Tenant ID: $SP_TENANT"
    echo "  Subscription ID: $SUBSCRIPTION_ID"
fi

# Add secrets to Key Vault
echo ""
print_info "Adding secrets to Key Vault..."

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "ftd-host" \
    --value "$FTD_HOST" \
    --output none

print_info "Added secret: ftd-host"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "ftd-username" \
    --value "$FTD_USERNAME" \
    --output none

print_info "Added secret: ftd-username"

az keyvault secret set \
    --vault-name "$KEY_VAULT_NAME" \
    --name "ftd-password" \
    --value "$FTD_PASSWORD" \
    --output none

print_info "Added secret: ftd-password"

# Get current user
CURRENT_USER=$(az account show --query user.name -o tsv)
print_info "Granting Key Vault access to current user: $CURRENT_USER"

# Grant access to current user for verification
az role assignment create \
    --assignee "$CURRENT_USER" \
    --role "Key Vault Secrets Officer" \
    --scope "$KEY_VAULT_ID" \
    --output none 2>/dev/null || print_warning "Could not grant access to current user"

# Verification
echo ""
print_info "Verifying Key Vault secrets..."
SECRETS=$(az keyvault secret list --vault-name "$KEY_VAULT_NAME" --query "[].name" -o tsv)

if echo "$SECRETS" | grep -q "ftd-host" && \
   echo "$SECRETS" | grep -q "ftd-username" && \
   echo "$SECRETS" | grep -q "ftd-password"; then
    print_info "✓ All secrets verified successfully"
else
    print_warning "Some secrets may be missing"
fi

# Summary
echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
print_info "Resources Created:"
echo "  • Resource Group: $RESOURCE_GROUP"
echo "  • Key Vault: $KEY_VAULT_NAME"
echo "  • Service Principal: $SERVICE_PRINCIPAL_NAME"
echo ""
print_info "Next Steps:"
echo "  1. Configure Azure DevOps Service Connection with the Service Principal details"
echo "  2. Update azure-pipelines.yml with:"
echo "     - Key Vault name: $KEY_VAULT_NAME"
echo "     - Service connection name (you choose this in ADO)"
echo "  3. Create variable group in Azure DevOps: ftd-${ENVIRONMENT}-config"
echo "  4. Run the pipeline to test FTD restart"
echo ""
print_info "Configuration file saved to: ftd-config-${ENVIRONMENT}.txt"

# Save configuration to file
cat > "ftd-config-${ENVIRONMENT}.txt" << EOF
Azure FTD Automation Configuration
===================================

Environment: $ENVIRONMENT
Subscription ID: $SUBSCRIPTION_ID
Resource Group: $RESOURCE_GROUP
Key Vault: $KEY_VAULT_NAME
Service Principal: $SERVICE_PRINCIPAL_NAME

FTD Configuration:
  Host: $FTD_HOST
  Username: $FTD_USERNAME
  Password: [stored in Key Vault]

Service Principal Details:
  (See console output for App ID, Client Secret, and Tenant ID)

Azure DevOps Configuration:
  Variable Group: ftd-${ENVIRONMENT}-config
  Service Connection: Azure-ServiceConnection (or your chosen name)
  Environment: ftd-${ENVIRONMENT}

Pipeline Configuration:
  Update azure-pipelines.yml:
  - keyVaultName: '$KEY_VAULT_NAME'
  - azureSubscription: 'Azure-ServiceConnection'
EOF

print_info "Setup completed successfully!"
