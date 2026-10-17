@description('Nome da Storage Account.')
param storageAccountName string

@description('Object ID da entidade que receberá a função.')
param principalId string

@description('ID da definição da função RBAC.')
param roleDefinitionId string

@description('Tipo da entidade.')
@allowed([
  'User'
  'Group'
  'ServicePrincipal'
  'ForeignGroup'
])
param principalType string = 'ServicePrincipal'

resource storageAccount 'Microsoft.Storage/storageAccounts@2025-06-01' existing = {
  name: storageAccountName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(
    storageAccount.id,
    principalId,
    roleDefinitionId
  )
  scope: storageAccount
  properties: {
    roleDefinitionId: roleDefinitionId
    principalId: principalId
    principalType: principalType
  }
}

output roleAssignmentId string = roleAssignment.id
