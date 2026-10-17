param location string
param environment string

resource ehNamespace 'Microsoft.EventHub/namespaces@2022-10-01-preview' = {
  name: 'evh-${environment}'
  location: location
  sku: {
    name: 'Standard'
    tier: 'Standard'
  }
}

resource eventHub 'Microsoft.EventHub/namespaces/eventhubs@2022-10-01-preview' = {
  parent: ehNamespace
  name: 'techchallenge'
}