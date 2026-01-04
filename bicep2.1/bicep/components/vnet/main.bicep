@description('Name of the virtual network')
param vnetName string

@description('Location for the virtual network')
param location string = resourceGroup().location

@description('Address prefix for the virtual network')
param addressPrefix string

@description('Subnets configuration')
param subnets array = []

@description('Enable DDoS protection')
param enableDdosProtection bool = false

@description('Tags to apply to the virtual network')
param tags object = {}

resource vnet 'Microsoft.Network/virtualNetworks@2024-01-01' = {
  name: vnetName
  location: location
  tags: tags
  properties: {
    addressSpace: {
      addressPrefixes: [
        addressPrefix
      ]
    }
    enableDdosProtection: enableDdosProtection
    subnets: [for subnet in subnets: {
      name: subnet.name
      properties: {
        addressPrefix: subnet.addressPrefix
        privateEndpointNetworkPolicies: contains(subnet, 'privateEndpointNetworkPolicies') ? subnet.privateEndpointNetworkPolicies : 'Enabled'
        privateLinkServiceNetworkPolicies: contains(subnet, 'privateLinkServiceNetworkPolicies') ? subnet.privateLinkServiceNetworkPolicies : 'Enabled'
        serviceEndpoints: contains(subnet, 'serviceEndpoints') ? subnet.serviceEndpoints : []
        delegations: contains(subnet, 'delegations') ? subnet.delegations : []
        networkSecurityGroup: contains(subnet, 'nsgId') ? {
          id: subnet.nsgId
        } : null
      }
    }]
  }
}

output vnetId string = vnet.id
output vnetName string = vnet.name
output subnets array = [for (subnet, i) in subnets: {
  name: vnet.properties.subnets[i].name
  id: vnet.properties.subnets[i].id
  addressPrefix: vnet.properties.subnets[i].properties.addressPrefix
}]
