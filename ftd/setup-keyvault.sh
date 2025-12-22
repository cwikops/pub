#!/bin/bash

###############################################################################
# Azure Key Vault Setup Script for FTD Restart Automation
# This script creates and configures Azure Key Vault with FTD credentials
###############################################################################

set -e  # Exit on error

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_info "Checking prerequisites..."

if ! command_exists az; then
    print_error "Azure CLI is not installed. Please install it first."
    print_info "Visit: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli"
    exit 1
fi

print_success "Azure CLI found"

# Configuration variables
print_info "Starting configuration..."
echo ""

# Prompt for configuration
read -p "Enter Resource Group Name: " RESOURCE_GROUP
read -p "Enter Key Vault Name (must be globally unique): " KEYVAULT_NAME
read -p "Enter Azure Location [eastus]: " LOCATION
LOCATION=${LOCATION:-eastus}

echo ""
read -p "Enter FTD Username [admin]: " FTD_USERNAME
FTD_USERNAME=${FTD_USERNAME:-admin}

# Prompt for password securely
echo ""
print_info "Enter FTD Password (input will be hidden):"
read -s FTD_PASSWORD
echo ""

if [ -z "$FTD_PASSWORD" ]; then
    print_error "Password cannot be empty"
    exit 1
fi

echo ""
read -p "Enter Azure DevOps Service Principal Object ID (optional): " SP_OBJECT_ID

# Display configuration summary
echo ""
echo "=========================================="
echo "Configuration Summary"
echo "=========================================="
echo "Resource Group:     $RESOURCE_GROUP"
echo "Key Vault Name:     $KEYVAULT_NAME"
echo "Location:           $LOCATION"
echo "FTD Username:       $FTD_USERNAME"
echo "FTD Password:       ********"
if [ -n "$SP_OBJECT_ID" ]; then
    echo "Service Principal:  $SP_OBJECT_ID"
fi
echo "=========================================="
echo ""

read -p "Proceed with this configuration? (yes/no): " CONFIRM
if [ "$CONFIRM" != "yes" ]; then
    print_warning "Setup cancelled by user"
    exit 0
fi

# Login check
print_info "Checking Azure login status..."
if ! az account show &> /dev/null; then
    print_info "Not logged in to Azure. Starting login..."
    az login
else
    print_success "Already logged in to Azure"
    CURRENT_ACCOUNT=$(az account show --query name -o tsv)
    print_info "Current subscription: $CURRENT_ACCOUNT"
    echo ""
    read -p "Use this subscription? (yes/no): " USE_CURRENT
    if [ "$USE_CURRENT" != "yes" ]; then
        az account list --output table
        read -p "Enter Subscription ID to use: " SUBSCRIPTION_ID
        az account set --subscription "$SUBSCRIPTION_ID"
    fi
fi

SUBSCRIPTION_ID=$(az account show --query id -o tsv)
print_success "Using subscription: $SUBSCRIPTION_ID"

# Create or verify resource group
print_info "Checking resource group..."
if az group show --name "$RESOURCE_GROUP" &> /dev/null; then
    print_success "Resource group '$RESOURCE_GROUP' already exists"
else
    print_info "Creating resource group '$RESOURCE_GROUP'..."
    az group create \
        --name "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --output none
    print_success "Resource group created"
fi

# Create Key Vault
print_info "Checking Key Vault..."
if az keyvault show --name "$KEYVAULT_NAME" --resource-group "$RESOURCE_GROUP" &> /dev/null; then
    print_warning "Key Vault '$KEYVAULT_NAME' already exists"
    read -p "Update existing Key Vault? (yes/no): " UPDATE_KV
    if [ "$UPDATE_KV" != "yes" ]; then
        print_warning "Skipping Key Vault creation"
        KV_EXISTS=true
    fi
fi

if [ -z "$KV_EXISTS" ]; then
    print_info "Creating Key Vault '$KEYVAULT_NAME'..."
    az keyvault create \
        --name "$KEYVAULT_NAME" \
        --resource-group "$RESOURCE_GROUP" \
        --location "$LOCATION" \
        --enable-rbac-authorization false \
        --output none
    
    print_success "Key Vault created successfully"
fi

# Store FTD credentials
print_info "Storing FTD credentials in Key Vault..."

# Store username
print_info "Storing FTD username..."
az keyvault secret set \
    --vault-name "$KEYVAULT_NAME" \
    --name "ftd-username" \
    --value "$FTD_USERNAME" \
    --output none

print_success "Username stored"

# Store password
print_info "Storing FTD password..."
az keyvault secret set \
    --vault-name "$KEYVAULT_NAME" \
    --name "ftd-password" \
    --value "$FTD_PASSWORD" \
    --output none

print_success "Password stored"

# Grant access to Service Principal if provided
if [ -n "$SP_OBJECT_ID" ]; then
    print_info "Granting Key Vault access to Service Principal..."
    
    az keyvault set-policy \
        --name "$KEYVAULT_NAME" \
        --object-id "$SP_OBJECT_ID" \
        --secret-permissions get list \
        --output none
    
    print_success "Service Principal access granted"
fi

# Enable diagnostic settings (optional)
print_info "Configuring Key Vault logging..."
read -p "Enable Key Vault diagnostic logging? (yes/no): " ENABLE_LOGGING

if [ "$ENABLE_LOGGING" == "yes" ]; then
    read -p "Enter Log Analytics Workspace Resource ID: " WORKSPACE_ID
    
    if [ -n "$WORKSPACE_ID" ]; then
        az monitor diagnostic-settings create \
            --name "KeyVault-Diagnostics" \
            --resource "/subscriptions/$SUBSCRIPTION_ID/resourceGroups/$RESOURCE_GROUP/providers/Microsoft.KeyVault/vaults/$KEYVAULT_NAME" \
            --logs '[{"category": "AuditEvent", "enabled": true}]' \
            --workspace "$WORKSPACE_ID" \
            --output none
        
        print_success "Diagnostic logging enabled"
    fi
fi

# Verify secrets
print_info "Verifying stored secrets..."
SECRET_COUNT=$(az keyvault secret list --vault-name "$KEYVAULT_NAME" --query "length([?starts_with(name, 'ftd-')])" -o tsv)

if [ "$SECRET_COUNT" -eq 2 ]; then
    print_success "All secrets verified"
else
    print_error "Secret verification failed. Expected 2, found $SECRET_COUNT"
fi

# Display summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
print_success "Key Vault Configuration:"
echo "  Name:                $KEYVAULT_NAME"
echo "  Resource Group:      $RESOURCE_GROUP"
echo "  Location:            $LOCATION"
echo "  Subscription:        $SUBSCRIPTION_ID"
echo ""

print_success "Stored Secrets:"
echo "  ftd-username:        ✓"
echo "  ftd-password:        ✓"
echo ""

if [ -n "$SP_OBJECT_ID" ]; then
    print_success "Service Principal Access: ✓"
    echo ""
fi

print_info "Next Steps:"
echo ""
echo "1. Update your Azure DevOps pipeline with these values:"
echo "   - keyVaultName: $KEYVAULT_NAME"
echo "   - azureSubscription: <your-service-connection-name>"
echo ""
echo "2. Ensure your Azure DevOps service connection has access to:"
echo "   - Subscription: $SUBSCRIPTION_ID"
echo "   - Resource Group: $RESOURCE_GROUP"
echo "   - Key Vault: $KEYVAULT_NAME"
echo ""
echo "3. If you haven't already, grant your service principal access:"
echo "   az keyvault set-policy \\"
echo "     --name $KEYVAULT_NAME \\"
echo "     --object-id <SERVICE-PRINCIPAL-OBJECT-ID> \\"
echo "     --secret-permissions get list"
echo ""

print_info "To retrieve your credentials later:"
echo "  az keyvault secret show --vault-name $KEYVAULT_NAME --name ftd-username --query value -o tsv"
echo "  az keyvault secret show --vault-name $KEYVAULT_NAME --name ftd-password --query value -o tsv"
echo ""

print_info "To list all secrets:"
echo "  az keyvault secret list --vault-name $KEYVAULT_NAME --query '[].name' -o table"
echo ""

print_success "Setup script completed successfully!"
