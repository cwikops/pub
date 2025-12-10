// modules/appInsights.bicep - Application Insights module

@description('Application Insights name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('Log Analytics Workspace ID (optional)')
param workspaceId string = ''

// Create Log Analytics Workspace if not provided
resource logAnalytics 'Microsoft.OperationalInsights/workspaces@2022-10-01' = if (empty(workspaceId)) {
  name: '${name}-law'
  location: location
  tags: tags
  properties: {
    sku: {
      name: 'PerGB2018'
    }
    retentionInDays: 30
  }
}

resource appInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: name
  location: location
  tags: tags
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: empty(workspaceId) ? logAnalytics.id : workspaceId
    IngestionMode: 'LogAnalytics'
    publicNetworkAccessForIngestion: 'Enabled'
    publicNetworkAccessForQuery: 'Enabled'
  }
}

@description('Application Insights connection string')
output connectionString string = appInsights.properties.ConnectionString

@description('Application Insights instrumentation key')
output instrumentationKey string = appInsights.properties.InstrumentationKey

@description('Application Insights ID')
output id string = appInsights.id

@description('Application Insights name')
output name string = appInsights.name
