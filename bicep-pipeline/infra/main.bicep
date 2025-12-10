// main.bicep - Main deployment template
// This template orchestrates the deployment of all resources

targetScope = 'resourceGroup'

// ============================================
// Parameters
// ============================================

@description('Environment name (dev, staging, prod)')
@allowed([
  'dev'
  'staging'
  'prod'
])
param environment string

@description('Azure region for resource deployment')
param location string = resourceGroup().location

@description('Base name for all resources')
@minLength(3)
@maxLength(20)
param baseName string

@description('Tags to apply to all resources')
param tags object = {}

@description('SKU for the App Service Plan')
@allowed([
  'B1'
  'B2'
  'S1'
  'S2'
  'P1v2'
  'P2v2'
])
param appServicePlanSku string = 'B1'

@description('Enable Application Insights')
param enableAppInsights bool = true

@description('Storage account SKU')
@allowed([
  'Standard_LRS'
  'Standard_GRS'
  'Standard_ZRS'
])
param storageAccountSku string = 'Standard_LRS'

// ============================================
// Variables
// ============================================

var resourcePrefix = '${baseName}-${environment}'
var defaultTags = union(tags, {
  Environment: environment
  ManagedBy: 'Bicep'
  DeployedAt: utcNow('yyyy-MM-dd')
})

// ============================================
// Modules
// ============================================

// Storage Account
module storage 'modules/storage.bicep' = {
  name: 'storage-${uniqueString(deployment().name)}'
  params: {
    name: replace('${resourcePrefix}st', '-', '')
    location: location
    tags: defaultTags
    sku: storageAccountSku
  }
}

// App Service Plan
module appServicePlan 'modules/appServicePlan.bicep' = {
  name: 'appserviceplan-${uniqueString(deployment().name)}'
  params: {
    name: '${resourcePrefix}-asp'
    location: location
    tags: defaultTags
    sku: appServicePlanSku
  }
}

// Web App
module webApp 'modules/webApp.bicep' = {
  name: 'webapp-${uniqueString(deployment().name)}'
  params: {
    name: '${resourcePrefix}-web'
    location: location
    tags: defaultTags
    appServicePlanId: appServicePlan.outputs.id
    appInsightsConnectionString: enableAppInsights ? appInsights.outputs.connectionString : ''
    storageAccountName: storage.outputs.name
  }
}

// Application Insights
module appInsights 'modules/appInsights.bicep' = if (enableAppInsights) {
  name: 'appinsights-${uniqueString(deployment().name)}'
  params: {
    name: '${resourcePrefix}-ai'
    location: location
    tags: defaultTags
  }
}

// ============================================
// Outputs
// ============================================

@description('Storage account name')
output storageAccountName string = storage.outputs.name

@description('Web app URL')
output webAppUrl string = webApp.outputs.url

@description('Web app name')
output webAppName string = webApp.outputs.name

@description('App Service Plan ID')
output appServicePlanId string = appServicePlan.outputs.id

@description('Application Insights connection string')
output appInsightsConnectionString string = enableAppInsights ? appInsights.outputs.connectionString : ''
