@description('Nome do Key Vault.')
param keyVaultName string

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

resource keyVault 'Microsoft.KeyVault/vaults@2024-11-01' existing = {
  name: keyVaultName
}

resource roleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(
    keyVault.id,
    principalId,
    roleDefinitionId
  )
  scope: keyVault
  properties: {
    roleDefinitionId: roleDefinitionId
    principalId: principalId
    principalType: principalType
  }
}

output roleAssignmentId string = roleAssignment.id
