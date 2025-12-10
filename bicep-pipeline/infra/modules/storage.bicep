// modules/storage.bicep - Storage Account module

@description('Storage account name (must be globally unique)')
@minLength(3)
@maxLength(24)
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('Storage account SKU')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_ZRS'
  'Premium_LRS'
])
param sku string = 'Standard_LRS'

@description('Storage account kind')
@allowed([
  'StorageV2'
  'BlobStorage'
])
param kind string = 'StorageV2'

@description('Enable blob public access')
param allowBlobPublicAccess bool = false

@description('Minimum TLS version')
param minimumTlsVersion string = 'TLS1_2'

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-01-01' = {
  name: name
  location: location
  tags: tags
  sku: {
    name: sku
  }
  kind: kind
  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: allowBlobPublicAccess
    minimumTlsVersion: minimumTlsVersion
    supportsHttpsTrafficOnly: true
    encryption: {
      services: {
        blob: {
          enabled: true
        }
        file: {
          enabled: true
        }
      }
      keySource: 'Microsoft.Storage'
    }
  }
}

@description('Storage account name')
output name string = storageAccount.name

@description('Storage account ID')
output id string = storageAccount.id

@description('Storage account primary endpoint')
output primaryEndpoint string = storageAccount.properties.primaryEndpoints.blob
