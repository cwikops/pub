// modules/webApp.bicep - Web App module

@description('Web App name')
param name string

@description('Azure region')
param location string

@description('Resource tags')
param tags object = {}

@description('App Service Plan ID')
param appServicePlanId string

@description('Application Insights connection string')
param appInsightsConnectionString string = ''

@description('Storage account name for app settings')
param storageAccountName string = ''

@description('Runtime stack')
param runtimeStack string = 'DOTNETCORE|8.0'

@description('Always On setting')
param alwaysOn bool = true

@description('HTTPS Only')
param httpsOnly bool = true

resource webApp 'Microsoft.Web/sites@2023-01-01' = {
  name: name
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: httpsOnly
    siteConfig: {
      linuxFxVersion: runtimeStack
      alwaysOn: alwaysOn
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
      appSettings: concat(
        [
          {
            name: 'WEBSITE_RUN_FROM_PACKAGE'
            value: '1'
          }
        ],
        !empty(appInsightsConnectionString) ? [
          {
            name: 'APPLICATIONINSIGHTS_CONNECTION_STRING'
            value: appInsightsConnectionString
          }
          {
            name: 'ApplicationInsightsAgent_EXTENSION_VERSION'
            value: '~3'
          }
        ] : [],
        !empty(storageAccountName) ? [
          {
            name: 'STORAGE_ACCOUNT_NAME'
            value: storageAccountName
          }
        ] : []
      )
    }
  }
}

// Staging slot for production deployments
resource stagingSlot 'Microsoft.Web/sites/slots@2023-01-01' = {
  parent: webApp
  name: 'staging'
  location: location
  tags: tags
  kind: 'app,linux'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    serverFarmId: appServicePlanId
    httpsOnly: httpsOnly
    siteConfig: {
      linuxFxVersion: runtimeStack
      alwaysOn: alwaysOn
      minTlsVersion: '1.2'
      ftpsState: 'Disabled'
    }
  }
}

@description('Web App URL')
output url string = 'https://${webApp.properties.defaultHostName}'

@description('Web App name')
output name string = webApp.name

@description('Web App ID')
output id string = webApp.id

@description('Web App principal ID')
output principalId string = webApp.identity.principalId
