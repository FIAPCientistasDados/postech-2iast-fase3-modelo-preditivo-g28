// =========================
// Parâmetros
// =========================

@description('Região da Storage Account.')
param location string

@description('Ambiente da implantação.')
@allowed([
  'dev'
  'hom'
  'prod'
])
param environment string

@description('Nome da Storage Account.')
@minLength(3)
@maxLength(24)
param storageAccountName string

@description('Nome do contêiner Bronze.')
@minLength(3)
@maxLength(63)
param bronzeContainer string = 'bronze'

@description('Nome do contêiner Silver.')
@minLength(3)
@maxLength(63)
param silverContainer string = 'silver'

@description('Nome do contêiner Gold.')
@minLength(3)
@maxLength(63)
param goldContainer string = 'gold'


// =========================
// Storage Account
// =========================

resource storage 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location

  tags: {
    environment: environment
    managedBy: 'Bicep'
    workload: 'tech-challenge'
  }

  sku: {
    name: 'Standard_LRS'
  }

  kind: 'StorageV2'

  properties: {
    accessTier: 'Hot'
    allowBlobPublicAccess: false
    allowCrossTenantReplication: false
    allowSharedKeyAccess: true
    defaultToOAuthAuthentication: false
    minimumTlsVersion: 'TLS1_2'
    publicNetworkAccess: 'Enabled'
    supportsHttpsTrafficOnly: true
  }
}


// =========================
// Blob Service
// =========================

resource blobService 'Microsoft.Storage/storageAccounts/blobServices@2023-05-01' = {
  parent: storage
  name: 'default'

  properties: {
    deleteRetentionPolicy: {
      enabled: true
      days: 7
    }

    containerDeleteRetentionPolicy: {
      enabled: true
      days: 7
    }
  }
}


// =========================
// Contêiner Bronze
// =========================

resource bronze 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: bronzeContainer

  properties: {
    publicAccess: 'None'
  }
}


// =========================
// Contêiner Silver
// =========================

resource silver 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: silverContainer

  properties: {
    publicAccess: 'None'
  }
}


// =========================
// Contêiner Gold
// =========================

resource gold 'Microsoft.Storage/storageAccounts/blobServices/containers@2023-05-01' = {
  parent: blobService
  name: goldContainer

  properties: {
    publicAccess: 'None'
  }
}


// =========================
// Outputs
// =========================

@description('Nome efetivo da Storage Account.')
output storageAccountName string = storage.name

@description('ID da Storage Account.')
output storageAccountId string = storage.id

@description('Endpoint do serviço Blob.')
output blobEndpoint string = storage.properties.primaryEndpoints.blob

@description('Nome do contêiner Bronze.')
output bronzeContainerName string = bronze.name

@description('Nome do contêiner Silver.')
output silverContainerName string = silver.name

@description('Nome do contêiner Gold.')
output goldContainerName string = gold.name
