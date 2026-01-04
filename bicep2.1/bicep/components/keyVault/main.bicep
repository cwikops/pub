@description('Name of the Key Vault')
param keyVaultName string

@description('Location for the Key Vault')
param location string = resourceGroup().location

@description('SKU for the Key Vault')
@allowed([
  'standard'
  'premium'
])
param skuName string = 'standard'

@description('Tenant ID for the Key Vault')
param tenantId string = subscription().tenantId

@description('Enable soft delete')
param enableSoftDelete bool = true

@description('Soft delete retention in days')
@minValue(7)
@maxValue(90)
param softDeleteRetentionInDays int = 90

@description('Enable purge protection')
param enablePurgeProtection bool = true

@description('Enable RBAC authorization')
param enableRbacAuthorization bool = true

@description('Enable for deployment')
param enabledForDeployment bool = false

@description('Enable for disk encryption')
param enabledForDiskEncryption bool = false

@description('Enable for template deployment')
param enabledForTemplateDeployment bool = true

@description('Network ACLs configuration')
param networkAcls object = {
  defaultAction: 'Allow'
  bypass: 'AzureServices'
  ipRules: []
  virtualNetworkRules: []
}

@description('Access policies (used when RBAC is disabled)')
param accessPolicies array = []

@description('Tags to apply to the Key Vault')
param tags object = {}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  tags: tags
  properties: {
    tenantId: tenantId
    sku: {
      family: 'A'
      name: skuName
    }
    enableSoftDelete: enableSoftDelete
    softDeleteRetentionInDays: softDeleteRetentionInDays
    enablePurgeProtection: enablePurgeProtection ? true : null
    enableRbacAuthorization: enableRbacAuthorization
    enabledForDeployment: enabledForDeployment
    enabledForDiskEncryption: enabledForDiskEncryption
    enabledForTemplateDeployment: enabledForTemplateDeployment
    networkAcls: {
      defaultAction: networkAcls.defaultAction
      bypass: networkAcls.bypass
      ipRules: [for ipRule in networkAcls.ipRules: {
        value: ipRule
      }]
      virtualNetworkRules: [for vnetRule in networkAcls.virtualNetworkRules: {
        id: vnetRule
      }]
    }
    accessPolicies: enableRbacAuthorization ? [] : accessPolicies
  }
}

output keyVaultId string = keyVault.id
output keyVaultName string = keyVault.name
output keyVaultUri string = keyVault.properties.vaultUri
