// modules/appServicePlan.bicep - App Service Plan module

@description('App Service Plan name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('App Service Plan SKU')
@allowed([
  'F1'
  'B1'
  'B2'
  'B3'
  'S1'
  'S2'
  'S3'
  'P1v2'
  'P2v2'
  'P3v2'
  'P1v3'
  'P2v3'
  'P3v3'
])
param sku string = 'B1'

@description('Operating system')
@allowed([
  'Linux'
  'Windows'
])
param operatingSystem string = 'Linux'

var skuTier = contains(sku, 'F') ? 'Free' : contains(sku, 'B') ? 'Basic' : contains(sku, 'S') ? 'Standard' : 'PremiumV2'

resource appServicePlan 'Microsoft.Web/serverfarms@2023-01-01' = {
  name: name
  location: location
  tags: tags
  kind: operatingSystem == 'Linux' ? 'linux' : 'windows'
  sku: {
    name: sku
    tier: skuTier
  }
  properties: {
    reserved: operatingSystem == 'Linux'
  }
}

@description('App Service Plan ID')
output id string = appServicePlan.id

@description('App Service Plan name')
output name string = appServicePlan.name
