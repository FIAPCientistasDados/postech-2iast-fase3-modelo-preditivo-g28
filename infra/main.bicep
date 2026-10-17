targetScope = 'resourceGroup'

// =========================
// Parâmetros principais
// =========================

@description('Ambiente da implantação.')
@allowed([
  'dev'
  'hom'
  'prod'
])
param environment string

@description('Região dos recursos.')
param location string = resourceGroup().location

@description('Nome do Azure Data Factory.')
param dataFactoryName string

@description('Nome da Storage Account.')
param storageAccountName string

@description('Nome do contêiner Bronze.')
param bronzeContainer string = 'bronze'

@description('Nome do Azure Key Vault.')
param keyVaultName string


// =========================
// BigQuery
// =========================

@description('Conteúdo ou referência das credenciais do Google BigQuery.')
@secure()
param googleApplicationCredentials string


// =========================
// Identidades IAM
// =========================

@description('Object ID do Service Principal usado no deployment.')
param deployServicePrincipalObjectId string

@description('Object ID da aplicação empresarial AzureDatabricks.')
param azureDatabricksObjectId string = '1d773a1f-1e5e-48d6-9a74-27e94d371bdc'


// =========================
// Azure RBAC Role Definitions
// =========================

// Key Vault Secrets Officer
var keyVaultSecretsOfficerRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'b86a8fe4-44ce-4948-aee5-eccb2c155cd7'
)

// Key Vault Secrets User
var keyVaultSecretsUserRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '4633458b-17de-408a-b874-0445c86b69e6'
)

// Storage Blob Data Contributor
var storageBlobDataContributorRoleDefinitionId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'ba92f5b4-2d11-453d-a403-e96b0029c9fe'
)


// =========================
// Log Analytics
// =========================

module logAnalytics './modules/loganalytics.bicep' = {
  name: 'deploy-log-analytics-${environment}'
  params: {
    location: location
    environment: environment
  }
}


// =========================
// Storage Account
// =========================

module storage './modules/storage.bicep' = {
  name: 'deploy-storage-${environment}'
  params: {
    location: location
    environment: environment
    storageAccountName: storageAccountName
    bronzeContainer: bronzeContainer
  }
}


// =========================
// Event Hub
// =========================

module eventHub './modules/eventhub.bicep' = {
  name: 'deploy-event-hub-${environment}'
  params: {
    location: location
    environment: environment
  }
}


// =========================
// Key Vault
// =========================

module keyVault './modules/keyvault.bicep' = {
  name: 'deploy-key-vault-${environment}'
  params: {
    keyVaultName: keyVaultName
    location: location
    environment: environment
  }
}


// =========================
// Azure Databricks
// =========================

module databricks './modules/databricks.bicep' = {
  name: 'deploy-databricks-${environment}'
  params: {
    location: location
    environment: environment
  }
}


// =========================
// Azure Data Factory
// =========================

module dataFactory './modules/datafactory.bicep' = {
  name: 'deploy-data-factory-${environment}'
  params: {
    location: location
    environment: environment
    dataFactoryName: dataFactoryName
  }
}


// =========================
// Pipeline BigQuery para Blob
// =========================

module bigqueryToBlob './modules/bigqueryToBlob.bicep' = {
  name: 'deploy-bigquery-to-blob-${environment}'
  params: {
    dataFactoryName: dataFactoryName
    location: location
    storageAccountName: storageAccountName
    bronzeContainer: bronzeContainer
    googleApplicationCredentials: googleApplicationCredentials
  }
  dependsOn: [
    dataFactory
    storage
  ]
}


// =========================
// IAM: Service Principal no Key Vault
// =========================

// Permite que o Service Principal do deployment
// crie e atualize segredos no Key Vault.
module deployServicePrincipalKeyVaultRole './modules/key-vault-role-assignment.bicep' = {
  name: 'iam-deploy-sp-key-vault-${environment}'
  params: {
    keyVaultName: keyVaultName
    principalId: deployServicePrincipalObjectId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsOfficerRoleDefinitionId
  }
  dependsOn: [
    keyVault
  ]
}


// =========================
// IAM: Azure Databricks no Key Vault
// =========================

// Permite que o Azure Databricks leia os segredos.
module azureDatabricksKeyVaultRole './modules/key-vault-role-assignment.bicep' = {
  name: 'iam-databricks-key-vault-${environment}'
  params: {
    keyVaultName: keyVaultName
    principalId: azureDatabricksObjectId
    principalType: 'ServicePrincipal'
    roleDefinitionId: keyVaultSecretsUserRoleDefinitionId
  }
  dependsOn: [
    keyVault
    databricks
  ]
}


// =========================
// IAM: Azure Databricks na Storage Account
// =========================

// Permite que o Azure Databricks leia,
// grave e exclua blobs na Storage Account.
module azureDatabricksStorageRole './modules/storage-role-assignment.bicep' = {
  name: 'iam-databricks-storage-${environment}'
  params: {
    storageAccountName: storageAccountName
    principalId: azureDatabricksObjectId
    principalType: 'ServicePrincipal'
    roleDefinitionId: storageBlobDataContributorRoleDefinitionId
  }
  dependsOn: [
    storage
    databricks
  ]
}


// =========================
// Outputs
// =========================

output deployedEnvironment string = environment
output deployedLocation string = location
output deployedResourceGroup string = resourceGroup().name
output deployedStorageAccountName string = storageAccountName
output deployedBronzeContainer string = bronzeContainer
output deployedKeyVaultName string = keyVaultName
output deployedDataFactoryName string = dataFactoryName
